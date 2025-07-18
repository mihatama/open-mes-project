from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import ProtectedError
from .models import InspectionItem, InspectionResult
from .serializers import (
    InspectionItemListSerializer,
    InspectionItemDetailSerializer,
    InspectionResultSerializer,
)

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