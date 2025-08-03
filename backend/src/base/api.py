from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.apps import apps
from django.db import transaction, IntegrityError
from django.db.models import DateField, DateTimeField, IntegerField, PositiveIntegerField, BooleanField
from datetime import datetime
from django.http import HttpResponse
import csv
import io

from .models import CsvColumnMapping, ModelDisplaySetting
from .serializers import CsvColumnMappingSerializer, ModelDisplaySettingSerializer

DATA_TYPE_MODEL_MAPPING = {
    'item': 'master.Item',
    'supplier': 'master.Supplier',
    'warehouse': 'master.Warehouse',
    'purchase_order': 'inventory.PurchaseOrder',
    'goods_receipt': 'inventory.Receipt',
    'production_plan': 'production.ProductionPlan',
    'parts_used': 'production.PartsUsed',
    'base_setting': 'base.BaseSetting',
    'csv_column_mapping': 'base.CsvColumnMapping',
    'model_display_setting': 'base.ModelDisplaySetting',
}

class AppInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({
            'version': settings.VERSION,
        })


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ModelFieldsView(APIView):
    """
    指定されたデータ種別に対応するモデルのフィールド定義を返すAPIビュー。
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        data_type = request.query_params.get('data_type')
        model_string = DATA_TYPE_MODEL_MAPPING.get(data_type)

        if not model_string:
            return Response({'error': f'Invalid data_type: {data_type}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            app_label, model_name = model_string.split('.')
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except (LookupError, ValueError):
            return Response({'error': f'Model {model_string} not found.'}, status=status.HTTP_404_NOT_FOUND)

        fields_data = []
        for field in model._meta.get_fields():
            if not hasattr(field, 'attname') or field.auto_created or field.is_relation:
                continue

            default_value = field.get_default()
            if callable(default_value):
                default_value = "動的デフォルト値"

            fields_data.append({
                'name': field.name,
                'verbose_name': str(field.verbose_name),
                'field_type': field.get_internal_type(),
                'is_required': not field.blank,
                'default_value': str(default_value) if default_value is not None else None,
                'help_text': str(field.help_text),
            })
        return Response(fields_data)


class CsvColumnMappingViewSet(viewsets.ModelViewSet):
    """
    CSV列マッピング設定を管理するためのAPIビューセット。
    """
    queryset = CsvColumnMapping.objects.all().order_by('order')
    serializer_class = CsvColumnMappingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['data_type']

    def get_permissions(self):
        """
        アクションに応じてパーミッションを動的に設定する。
        'csv_template'アクションは認証済みユーザーなら誰でもアクセス可能とする。
        """
        if self.action == 'csv_template':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='csv-template')
    def csv_template(self, request, *args, **kwargs):
        """
        指定されたデータ種別のCSVテンプレートを生成して返す。
        アクティブなマッピングのCSVヘッダーをBOM付きUTF-8のCSV形式で出力します。
        """
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({'error': 'Query parameter "data_type" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        mappings = CsvColumnMapping.objects.filter(
            data_type=data_type,
            is_active=True
        ).order_by('order')

        headers = [mapping.csv_header for mapping in mappings]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        # BOM (Byte Order Mark) を追加してExcelでの文字化けを防ぐ
        csv_data = b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')

        response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{data_type}_template.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='import-csv')
    def import_csv(self, request, *args, **kwargs):
        """
        CSVマッピング設定に基づいて、CSVファイルを動的にインポートする。
        """
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({'status': 'error', 'message': 'Query parameter "data_type" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=status.HTTP_400_BAD_REQUEST)
        if not csv_file.name.endswith('.csv'):
            return Response({'status': 'error', 'message': '無効なファイル形式です。CSVファイルをアップロードしてください。'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. マッピング設定を取得
        mappings = CsvColumnMapping.objects.filter(data_type=data_type, is_active=True).order_by('order')
        if not mappings.exists():
            return Response({'status': 'error', 'message': f'"{data_type}" に有効なCSVマッピング設定がありません。'}, status=status.HTTP_400_BAD_REQUEST)

        model_string = DATA_TYPE_MODEL_MAPPING.get(data_type)
        try:
            app_label, model_name = model_string.split('.')
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except (LookupError, ValueError):
            return Response({'error': f'Model {model_string} not found.'}, status=status.HTTP_404_NOT_FOUND)

        expected_headers = [m.csv_header for m in mappings]
        header_to_model_map = {m.csv_header: m.model_field_name for m in mappings}
        update_keys_model = [m.model_field_name for m in mappings if m.is_update_key]

        if not update_keys_model:
            return Response({'status': 'error', 'message': 'CSVインポートのための上書きキーがCSVマッピング設定で指定されていません。'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. CSVファイルをデコード
        file_content = csv_file.read()
        decoded_file = None
        for encoding in ['utf-8-sig', 'cp932']:
            try:
                decoded_file = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if decoded_file is None:
            return Response({'status': 'error', 'message': 'ファイルのエンコーディングが無効です。UTF-8 (BOM付き可) または Shift-JIS を使用してください。'}, status=status.HTTP_400_BAD_REQUEST)

        io_string = io.StringIO(decoded_file)
        
        created_count = 0
        updated_count = 0
        errors_list = []

        try:
            reader = csv.DictReader(io_string)
            actual_headers = reader.fieldnames
            if not actual_headers:
                return Response({'status': 'error', 'message': 'CSVファイルが空か、ヘッダーがありません。'}, status=status.HTTP_400_BAD_REQUEST)

            missing_headers = set(expected_headers) - set(actual_headers)
            if missing_headers:
                return Response({'status': 'error', 'message': f"必須のCSVヘッダーがファイルに存在しません。", 'errors': [f"不足しているヘッダー: {', '.join(missing_headers)}"]}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                for i, row in enumerate(reader, start=2):
                    model_data = {}
                    row_specific_errors = []

                    for csv_header, model_field_name in header_to_model_map.items():
                        value = row.get(csv_header, '').strip()
                        if not value:
                            model_data[model_field_name] = None
                            continue
                        try:
                            field_obj = model._meta.get_field(model_field_name)
                            # 型変換処理
                            if isinstance(field_obj, (DateTimeField, DateField)):
                                parsed_date = None
                                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y-%m-%d', '%Y/%m/%d'):
                                    try:
                                        parsed_date = datetime.strptime(value, fmt)
                                        break
                                    except ValueError: continue
                                if parsed_date is None: raise ValueError("対応する日付形式ではありません。")
                                model_data[model_field_name] = parsed_date.date() if isinstance(field_obj, DateField) else parsed_date
                            elif isinstance(field_obj, (IntegerField, PositiveIntegerField)):
                                model_data[model_field_name] = int(float(value))
                            elif isinstance(field_obj, BooleanField):
                                model_data[model_field_name] = value.lower() in ['true', '1', 'yes', 't', 'はい']
                            else:
                                model_data[model_field_name] = value
                        except (ValueError, TypeError) as e:
                            row_specific_errors.append(f"フィールド '{csv_header}' の値 '{value}' は型が不正です: {e}")
                    
                    if row_specific_errors:
                        errors_list.append(f"行 {i}: {'; '.join(row_specific_errors)}")
                        continue

                    update_kwargs = {key: model_data.pop(key) for key in update_keys_model if key in model_data and model_data[key] is not None}
                    if len(update_kwargs) != len(update_keys_model):
                        errors_list.append(f"行 {i}: 上書きキー ({', '.join(update_keys_model)}) の値が空、または見つかりません。")
                        continue

                    try:
                        defaults_data = {k: v for k, v in model_data.items() if v is not None}
                        _, created = model.objects.update_or_create(**update_kwargs, defaults=defaults_data)
                        if created: created_count += 1
                        else: updated_count += 1
                    except (IntegrityError, Exception) as e:
                        errors_list.append(f"行 {i} ({update_kwargs}): データベース保存エラー - {e}")
        except (csv.Error, Exception) as e:
            return Response({'status': 'error', 'message': f'処理中に予期せぬエラーが発生しました: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 6. 結果を返す
        return self.get_import_response(created_count, updated_count, errors_list)

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request, *args, **kwargs):
        """
        指定されたデータ種別のマッピング設定を一括で保存（上書き）する。
        """
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({'error': 'Query parameter "data_type" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        mappings_data = request.data
        if not isinstance(mappings_data, list):
            return Response({'error': 'Request body must be a list of mapping objects.'}, status=status.HTTP_400_BAD_REQUEST)

        objects_to_create = []
        validation_errors = []

        for index, data in enumerate(mappings_data):
            if not data.get('is_active') or not data.get('csv_header', '').strip():
                continue

            data['data_type'] = data_type
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                objects_to_create.append(CsvColumnMapping(**serializer.validated_data))
            else:
                validation_errors.append({'field': data.get('model_field_name', f'index {index}'), 'errors': serializer.errors})

        if validation_errors:
            return Response({'status': 'error', 'message': '入力データにエラーがあります。', 'errors': validation_errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 既存のマッピングを削除
            CsvColumnMapping.objects.filter(data_type=data_type).delete()
            # 新しいマッピングを一括作成
            CsvColumnMapping.objects.bulk_create(objects_to_create)

        return Response({'status': 'success', 'message': f'{data_type} のマッピングを保存しました。'}, status=status.HTTP_200_OK)

    def get_import_response(self, created_count, updated_count, errors_list):
        message_parts = []
        if created_count > 0: message_parts.append(f"{created_count}件のデータが新規登録されました。")
        if updated_count > 0: message_parts.append(f"{updated_count}件のデータが更新されました。")
        final_message = " ".join(message_parts) if message_parts else "処理対象の有効なデータがCSVにありませんでした。"

        if errors_list:
            status_code = status.HTTP_207_MULTI_STATUS if (created_count + updated_count > 0) else status.HTTP_400_BAD_REQUEST
            response_status_str = 'partial_success' if (created_count + updated_count > 0) else 'error'
            if response_status_str == 'error': final_message = "CSVの処理中にエラーが発生しました。詳細はエラーリストを確認してください。"
            return Response({'status': response_status_str, 'message': final_message, 'created_count': created_count, 'updated_count': updated_count, 'errors': errors_list}, status=status_code)
        
        return Response({'status': 'success', 'message': final_message, 'created_count': created_count, 'updated_count': updated_count})


class ModelDisplaySettingViewSet(viewsets.ModelViewSet):
    """
    モデル項目表示設定を管理するためのAPIビューセット。
    """
    queryset = ModelDisplaySetting.objects.all().order_by('display_order')
    serializer_class = ModelDisplaySettingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['data_type']

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request, *args, **kwargs):
        """
        指定されたデータ種別の表示設定を一括で保存（上書き）する。
        """
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({'error': 'Query parameter "data_type" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        settings_data = request.data
        if not isinstance(settings_data, list):
            return Response({'error': 'Request body must be a list of setting objects.'}, status=status.HTTP_400_BAD_REQUEST)

        objects_to_create = []
        validation_errors = []

        for index, data in enumerate(settings_data):
            data['data_type'] = data_type
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                objects_to_create.append(ModelDisplaySetting(**serializer.validated_data))
            else:
                validation_errors.append({'field': data.get('model_field_name', f'index {index}'), 'errors': serializer.errors})

        if validation_errors:
            return Response({'status': 'error', 'message': '入力データにエラーがあります。', 'errors': validation_errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            ModelDisplaySetting.objects.filter(data_type=data_type).delete()
            ModelDisplaySetting.objects.bulk_create(objects_to_create)

        return Response({'status': 'success', 'message': f'{data_type} の表示設定を保存しました。'}, status=status.HTTP_200_OK)