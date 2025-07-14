from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

router = DefaultRouter()
router.register(r'production-plans', rest_views.ProductionPlanViewSet, basename='productionplan')
router.register(r'parts-used', rest_views.PartsUsedViewSet, basename='partsused')

app_name = 'production_api'

urlpatterns = [
    path('', include(router.urls)),
    # AJAX endpoints for DataImport page
    path('production-plan/create/ajax/', rest_views.ProductionPlanCreateAjaxAPIView.as_view(), name='production_plan_create_ajax'),
    path('production-plan/list/ajax/', rest_views.ProductionPlanListAjaxAPIView.as_view(), name='production_plan_list_ajax'),
    path('production-plan/<uuid:pk>/detail/ajax/', rest_views.ProductionPlanDetailAjaxAPIView.as_view(), name='production_plan_detail_ajax'),
    path('production-plan/<uuid:pk>/delete/ajax/', rest_views.ProductionPlanDeleteAjaxAPIView.as_view(), name='production_plan_delete_ajax'),

    path('parts-used/create/ajax/', rest_views.PartsUsedCreateAjaxAPIView.as_view(), name='parts_used_create_ajax'),
    path('parts-used/list/ajax/', rest_views.PartsUsedListAjaxAPIView.as_view(), name='parts_used_list_ajax'),
    path('parts-used/<uuid:pk>/detail/ajax/', rest_views.PartsUsedDetailAjaxAPIView.as_view(), name='parts_used_detail_ajax'),
    path('parts-used/<uuid:pk>/delete/ajax/', rest_views.PartsUsedDeleteAjaxAPIView.as_view(), name='parts_used_delete_ajax'),
]