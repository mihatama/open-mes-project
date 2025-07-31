from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend

from .models import CsvColumnMapping
from .serializers import CsvColumnMappingSerializer


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


class CsvColumnMappingViewSet(viewsets.ModelViewSet):
    """
    CSV列マッピング設定を管理するためのAPIビューセット。
    """
    queryset = CsvColumnMapping.objects.all().order_by('order')
    serializer_class = CsvColumnMappingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['data_type']