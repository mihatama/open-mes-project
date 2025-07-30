from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

app_name = 'inventory_api'  # このURL設定の名前空間

router = DefaultRouter()
router.register(r'inventories', rest_views.InventoryViewSet, basename='inventory')
router.register(r'purchase-orders', rest_views.PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'sales-orders', rest_views.SalesOrderViewSet, basename='salesorder')
router.register(r'stock-movements', rest_views.StockMovementViewSet, basename='stockmovement')


urlpatterns = [
    path('', include(router.urls)),

    # CSV Template and Import URLs for Purchase Orders
    # These are kept separate as they are specific actions not tied to a single resource instance.
    path('purchase-order/csv-template/', rest_views.PurchaseOrderCSVTemplateView.as_view(), name='purchase_order_csv_template'),
    path('purchase-order/import-csv/', rest_views.PurchaseOrderImportCSVView.as_view(), name='purchase_order_import_csv'),
]