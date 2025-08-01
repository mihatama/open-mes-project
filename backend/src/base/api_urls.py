from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    AppInfoView, HealthCheckView, ModelFieldsView, CsvColumnMappingViewSet,
    ModelDisplaySettingViewSet
)

app_name = 'base_api'

router = DefaultRouter()
router.register(r'csv-mappings', CsvColumnMappingViewSet, basename='csv-mapping')
router.register(r'model-display-settings', ModelDisplaySettingViewSet, basename='model-display-setting')

urlpatterns = [
    path('info/', AppInfoView.as_view(), name='app-info'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('model-fields/', ModelFieldsView.as_view(), name='model-fields'),
    path('', include(router.urls)),
]