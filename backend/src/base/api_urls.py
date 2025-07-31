from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

app_name = 'base_api'

router = DefaultRouter()
router.register(r'', api.CsvColumnMappingViewSet, basename='csv-mapping')

urlpatterns = [
    path('info/', api.AppInfoView.as_view(), name='app-info'),
    path('health/', api.HealthCheckView.as_view(), name='health-check'),
    path('csv-mappings/', include(router.urls)),
]