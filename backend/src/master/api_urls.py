from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

app_name = 'master_api'

router = DefaultRouter()
router.register(r'items', rest_views.ItemViewSet, basename='item')
router.register(r'suppliers', rest_views.SupplierViewSet, basename='supplier')
router.register(r'warehouses', rest_views.WarehouseViewSet, basename='warehouse')

urlpatterns = [
    path('', include(router.urls)),
]