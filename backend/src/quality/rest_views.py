import json
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import ProtectedError
from .models import InspectionItem, InspectionResult, InspectionResultDetail, MeasurementDetail
from .serializers import (
    InspectionItemListSerializer,
    InspectionItemDetailSerializer,
    InspectionResultSerializer,
    MeasurementDetailSerializer,
)

# 検査結果登録フォームの動的な定義
# フロントエンドの InspectionResultModal.jsx で使用されます
INSPECTION_RESULT_FORM_FIELDS = [
    {'name': 'lot_number', 'label': 'ロット番号', 'type': 'text'},
    {'name': 'equipment_used', 'label': '使用設備', 'type': 'text'},
    # 'operator' はリクエストユーザーから自動的に設定するため、フォームには含めません
    {'name': 'attachment', 'label': '添付ファイル', 'type': 'file'},
    {'name': 'remarks', 'label': '備考', 'type': 'textarea'},
]

class CustomSuccessMessageMixin:
    """
    Mixin to customize success messages for create, update, and destroy actions.
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': 'success', 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        model_name = self.queryset.model._meta.verbose_name
        return Response(
            {'status': 'success', 'message': f'{model_name}を登録しました。', 'data': serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True) # Default to PATCH
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        model_name = self.queryset.model._meta.verbose_name
        return Response(
            {'status': 'success', 'message': f'{model_name}を更新しました。', 'data': serializer.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        model_name = self.queryset.model._meta.verbose_name
        instance_repr = str(instance)
        try:
            self.perform_destroy(instance)
            return Response({'status': 'success', 'message': f'{model_name}「{instance_repr}」を削除しました。'}, status=status.HTTP_200_OK)
        except ProtectedError:
            return Response({'status': 'error', 'message': f'この{model_name}は実績データが関連付けられているため削除できません。'}, status=status.HTTP_400_BAD_REQUEST)

class InspectionItemViewSet(CustomSuccessMessageMixin, viewsets.ModelViewSet):
    """
    API endpoint for Inspection Items (検査項目マスター).
    """
    queryset = InspectionItem.objects.prefetch_related('measurement_details').all().order_by('code')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return InspectionItemListSerializer
        return InspectionItemDetailSerializer

    @action(detail=True, methods=['get'], url_path='form-data')
    def form_data(self, request, pk=None):
        """
        検査結果モーダルのためのフォーム定義と測定詳細を返す
        """
        try:
            inspection_item = self.get_object()
            measurement_details = inspection_item.measurement_details.all().order_by('order')
            details_serializer = MeasurementDetailSerializer(measurement_details, many=True)

            response_data = {
                'success': True,
                'result_form_fields': INSPECTION_RESULT_FORM_FIELDS,
                'measurement_details': details_serializer.data
            }
            return Response(response_data)
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='record-result')
    def record_result(self, request, pk=None):
        """
        検査結果を登録する
        """
        inspection_item = self.get_object()

        try:
            # フロントエンドはFormDataで送信し、詳細はJSON文字列で渡される
            measurement_payload_str = request.data.get('measurement_details_payload', '[]')
            measurement_payload = json.loads(measurement_payload_str)

            # 各詳細の測定タイプを特定するために、MeasurementDetailオブジェクトを取得
            detail_ids = [d.get('measurement_detail_id') for d in measurement_payload]
            measurement_details_map = {
                str(md.id): md for md in inspection_item.measurement_details.filter(id__in=detail_ids)
            }

            details_data_for_serializer = []
            for measurement_data in measurement_payload:
                detail_id = measurement_data.get('measurement_detail_id')
                value = measurement_data.get('value')
                measurement_detail = measurement_details_map.get(detail_id)

                if not measurement_detail:
                    return Response({'success': False, 'message': f'無効な測定詳細IDです: {detail_id}'}, status=status.HTTP_400_BAD_REQUEST)

                detail_dict = {'measurement_detail': detail_id}
                if measurement_detail.measurement_type == 'quantitative':
                    detail_dict['measured_value_numeric'] = value if value not in [None, ''] else None
                else:  # qualitative
                    detail_dict['result_qualitative'] = value if value not in [None, ''] else None
                details_data_for_serializer.append(detail_dict)

            # シリアライザ用のメインデータオブジェクトを構築
            result_data = {
                'inspection_item': inspection_item.id,
                'lot_number': request.data.get('lot_number'),
                'equipment_used': request.data.get('equipment_used'),
                'remarks': request.data.get('remarks'),
                'attachment': request.data.get('attachment'),
                'details': details_data_for_serializer
            }

            serializer = InspectionResultSerializer(data=result_data, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({'success': True, 'message': f'検査項目「{inspection_item.name}」の結果を登録しました。'}, status=status.HTTP_201_CREATED)

        except json.JSONDecodeError:
            return Response({'success': False, 'message': '測定詳細のデータ形式が不正です。'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            errors = getattr(e, 'detail', str(e))
            return Response({'success': False, 'message': '検査結果の登録中にエラーが発生しました。', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

class InspectionResultViewSet(CustomSuccessMessageMixin, viewsets.ModelViewSet):
    """
    API endpoint for Inspection Results (検査実績).
    """
    queryset = InspectionResult.objects.all().order_by('-inspected_at')
    serializer_class = InspectionResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """
        Pass request context to the serializer.
        """
        return {'request': self.request}