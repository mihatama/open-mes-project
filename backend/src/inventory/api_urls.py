from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

app_name = 'inventory_api'  # このURL設定の名前空間

router = DefaultRouter()
router.register(r'inventories', rest_views.InventoryViewSet, basename='inventory')
router.register(r'purchase-orders', rest_views.PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'sales-orders', rest_views.SalesOrderViewSet, basename='salesorder')
router.register(r'receipts', rest_views.ReceiptViewSet, basename='receipt')
router.register(r'stock-movements', rest_views.StockMovementViewSet, basename='stockmovement')


urlpatterns = [
    path('', include(router.urls)),
]