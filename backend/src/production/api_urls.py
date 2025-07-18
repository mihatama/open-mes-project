from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

router = DefaultRouter()
router.register(r'plans', rest_views.ProductionPlanViewSet, basename='production-plan')
router.register(r'parts-used', rest_views.PartsUsedViewSet, basename='parts-used')
router.register(r'material-allocations', rest_views.MaterialAllocationViewSet, basename='material-allocation')
router.register(r'work-progress', rest_views.WorkProgressViewSet, basename='work-progress')

app_name = 'production_api'

urlpatterns = [
    path('', include(router.urls)),
]