from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    AppInfoView, HealthCheckView, ModelFieldsView, CsvColumnMappingViewSet,
    ModelDisplaySettingViewSet, QrCodeActionViewSet
)

app_name = 'base_api'

router = DefaultRouter()
router.register(r'csv-mappings', CsvColumnMappingViewSet, basename='csv-mapping')
router.register(r'model-display-settings', ModelDisplaySettingViewSet, basename='model-display-setting')
router.register(r'qr-code-actions', QrCodeActionViewSet, basename='qr-code-action')

urlpatterns = [
    path('info/', AppInfoView.as_view(), name='app-info'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('model-fields/', ModelFieldsView.as_view(), name='model-fields'),
    path('csv-import-status/<str:pk>/', CsvColumnMappingViewSet.as_view({'get': 'get_task_status'}), name='csv-import-status'),
    path('csv-import-cancel/<str:pk>/', CsvColumnMappingViewSet.as_view({'post': 'cancel_task'}), name='csv-import-cancel'),
    path('', include(router.urls)),
]