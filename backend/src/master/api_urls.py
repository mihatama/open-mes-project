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

    # CSV Template Download URLs
    path('item/csv-template/', rest_views.ItemCSVTemplateAPIView.as_view(), name='item_csv_template'),
    path('supplier/csv-template/', rest_views.SupplierCSVTemplateAPIView.as_view(), name='supplier_csv_template'),
    path('warehouse/csv-template/', rest_views.WarehouseCSVTemplateAPIView.as_view(), name='warehouse_csv_template'),

    # CSV Import URLs
    path('item/import-csv/', rest_views.ItemImportCSVAPIView.as_view(), name='item_import_csv'),
    path('supplier/import-csv/', rest_views.SupplierImportCSVAPIView.as_view(), name='supplier_import_csv'),
    path('warehouse/import-csv/', rest_views.WarehouseImportCSVAPIView.as_view(), name='warehouse_import_csv'),
]