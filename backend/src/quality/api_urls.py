from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

app_name = 'quality_api'

router = DefaultRouter()
router.register(r'inspection-items', rest_views.InspectionItemViewSet, basename='inspection-item')
router.register(r'inspection-results', rest_views.InspectionResultViewSet, basename='inspection-result')

urlpatterns = [
    path('', include(router.urls)),
]