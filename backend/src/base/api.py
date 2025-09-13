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
from django.core.files.storage import FileSystemStorage
import csv
import re
import io
import os
import uuid
import django_filters

from .models import CsvColumnMapping, ModelDisplaySetting, QrCodeAction, AsyncTask
from .serializers import CsvColumnMappingSerializer, ModelDisplaySettingSerializer, QrCodeActionSerializer
from .tasks import import_csv_task

DATA_TYPE_MODEL_MAPPING = {
    'item': 'master.Item',
    'supplier': 'master.Supplier',
    'warehouse': 'master.Warehouse',
    'purchase_order': 'inventory.PurchaseOrder',
    'goods_receipt': 'inventory.Receipt',
    'sales_order': 'inventory.SalesOrder',
    'inventory': 'inventory.Inventory',
    'stock_movement': 'inventory.StockMovement',
    'production_plan': 'production.ProductionPlan',
    'parts_used': 'production.PartsUsed',
    'base_setting': 'base.BaseSetting',
    'csv_column_mapping': 'base.CsvColumnMapping',
    'model_display_setting': 'base.ModelDisplaySetting',
    'qr_code_action': 'base.QrCodeAction',
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


class ModelDisplaySettingFilter(django_filters.FilterSet):
    data_type = django_filters.ChoiceFilter(choices=[(k, k) for k in DATA_TYPE_MODEL_MAPPING.keys()])

    class Meta:
        model = ModelDisplaySetting
        fields = ['data_type']

class CsvColumnMappingFilter(django_filters.FilterSet):
    data_type = django_filters.ChoiceFilter(choices=[(k, k) for k in DATA_TYPE_MODEL_MAPPING.keys()])

    class Meta:
        model = CsvColumnMapping
        fields = ['data_type']


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
    filterset_class = CsvColumnMappingFilter

    def get_permissions(self):
        """
        アクションに応じてパーミッションを動的に設定する。
        'csv_template'アクションは認証済みユーザーなら誰でもアクセス可能とする。
        """
        if self.action in ['csv_template', 'import_csv', 'get_task_status', 'cancel_task']:
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
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({'status': 'error', 'message': 'Query parameter "data_type" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=status.HTTP_400_BAD_REQUEST)

        # 一時ファイルに保存
        fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'temp_csv_uploads'))
        filename = fs.save(f"{uuid.uuid4()}.csv", csv_file)
        file_path = fs.path(filename)

        # 非同期タスクを開始
        task = import_csv_task.delay(data_type, file_path)

        # タスク情報をDBに保存
        AsyncTask.objects.create(
            task_id=task.id,
            task_name=f'CSV Import: {data_type}',
            status='PENDING'
        )

        return Response({'status': 'processing', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='csv-import-status')
    def get_task_status(self, request, pk=None):
        try:
            task = AsyncTask.objects.get(task_id=pk)
            response_data = {
                'task_id': task.task_id,
                'status': task.status,
                'progress': task.progress,
                'total': task.total,
                'result': task.result
            }
            return Response(response_data)
        except AsyncTask.DoesNotExist:
            return Response({'status': 'error', 'message': 'タスクが見つかりません。'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='csv-import-cancel')
    def cancel_task(self, request, pk=None):
        try:
            task = AsyncTask.objects.get(task_id=pk)
            if task.status in ['PENDING', 'STARTED']:
                import_csv_task.AsyncResult(task.task_id).revoke(terminate=True)
                task.status = 'REVOKED'
                task.save()
                return Response({'status': 'success', 'message': 'タスクのキャンセルをリクエストしました。'})
            else:
                return Response({'status': 'error', 'message': 'このタスクはすでに完了またはキャンセルされています。'}, status=status.HTTP_400_BAD_REQUEST)
        except AsyncTask.DoesNotExist:
            return Response({'status': 'error', 'message': 'タスクが見つかりません。'}, status=status.HTTP_404_NOT_FOUND)

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

class QrCodeActionViewSet(viewsets.ModelViewSet):
    """
    QRコードアクションを管理するためのAPIビューセット。
    """
    queryset = QrCodeAction.objects.all().order_by('name')
    serializer_class = QrCodeActionSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    @action(detail=False, methods=['post'], url_path='execute', permission_classes=[permissions.IsAuthenticated])
    def execute_action(self, request, *args, **kwargs):
        """
        QRコードのデータを受け取り、マッチするアクションを実行する。
        注意: スクリプトの実行はセキュリティリスクを伴います。
              本番環境では、安全なサンドボックス環境で実行するか、
              許可された関数のみを呼び出すように制限する必要があります。
        """
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({'error': 'qr_data is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # スクリプト判定を先に、正規表現判定を後に評価する
        actions = QrCodeAction.objects.filter(is_active=True).order_by('-action_type')
        
        for action in actions:
            try:
                # **セキュリティ警告**: execの使用は非常に危険です。
                # これはあくまで概念実証のためのコードです。
                # 実際のアプリケーションでは、より安全な方法を検討してください。
                script_body = '\n'.join([f'    {line}' for line in action.script.splitlines()])
                wrapped_script = f"""
def run_action(qr_data):
{script_body}
"""
                script_globals = {}
                exec(wrapped_script, script_globals)
                action_func = script_globals['run_action']

                result = None
                matched = False

                if action.action_type == 'regex':
                    if action.qr_code_pattern and re.match(action.qr_code_pattern, qr_data):
                        matched = True
                        result = action_func(qr_data)
                
                elif action.action_type == 'script':
                    # スクリプト判定では、スクリプト自体が判定と結果返却を行う
                    result = action_func(qr_data)
                    if result is not None:
                        matched = True

                if matched:
                    # スクリプトがNoneを返した場合、それは「マッチしなかった」と見なす
                    if result is None:
                        continue

                    return Response({
                        'status': 'success',
                        'action_name': action.name,
                        'result': result,
                    })

            except re.error as e:
                # パターンが無効な場合はログに記録するなど
                # logger.warning(f"Invalid regex pattern for action '{action.name}': {e}")
                continue
            except Exception as e:
                return Response({
                    'status': 'error',
                    'action_name': action.name,
                    'message': f"An error occurred while executing action '{action.name}': {e}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'status': 'not_found', 'message': 'No matching action found for the given QR data.'}, status=status.HTTP_404_NOT_FOUND)

class ModelDisplaySettingViewSet(viewsets.ModelViewSet):
    """
    モデル項目表示設定を管理するためのAPIビューセット。
    """
    queryset = ModelDisplaySetting.objects.all().order_by('display_order')
    serializer_class = ModelDisplaySettingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ModelDisplaySettingFilter

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
