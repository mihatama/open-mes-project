from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.apps import apps
from django.db import transaction, IntegrityError

from .models import CsvColumnMapping, ModelDisplaySetting
from .serializers import CsvColumnMappingSerializer, ModelDisplaySettingSerializer

DATA_TYPE_MODEL_MAPPING = {
    'item': 'master.Item',
    'supplier': 'master.Supplier',
    'warehouse': 'master.Warehouse',
    'purchase_order': 'inventory.PurchaseOrder',
    'production_plan': 'production.ProductionPlan',
    'parts_used': 'production.PartsUsed',
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