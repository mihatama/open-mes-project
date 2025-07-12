# /home/ubuntu/git/open-mes-project/open_mes/scr/production/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views as production_rest_views

app_name = 'production_api'

router = DefaultRouter()
router.register(r'plans', production_rest_views.ProductionPlanViewSet, basename='production_plan')
router.register(r'parts-used', production_rest_views.PartsUsedViewSet, basename='parts_used')

urlpatterns = [
    path('', include(router.urls)),
]