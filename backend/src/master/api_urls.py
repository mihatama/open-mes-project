from django.urls import path
from . import rest_views # Import rest_views

app_name = 'master_api'

urlpatterns = [
    path('item/create/ajax/', rest_views.ItemCreateAjaxAPIView.as_view(), name='item_create_ajax'),
    path('supplier/create/ajax/', rest_views.SupplierCreateAjaxAPIView.as_view(), name='supplier_create_ajax'),
    path('warehouse/create/ajax/', rest_views.WarehouseCreateAjaxAPIView.as_view(), name='warehouse_create_ajax'),
    path('item/list/ajax/', rest_views.ItemListAjaxAPIView.as_view(), name='item_list_ajax'),
    path('supplier/list/ajax/', rest_views.SupplierListAjaxAPIView.as_view(), name='supplier_list_ajax'),
    path('warehouse/list/ajax/', rest_views.WarehouseListAjaxAPIView.as_view(), name='warehouse_list_ajax'),
    path('item/<int:pk>/detail/ajax/', rest_views.ItemDetailAjaxAPIView.as_view(), name='item_detail_ajax'),
    path('supplier/<int:pk>/detail/ajax/', rest_views.SupplierDetailAjaxAPIView.as_view(), name='supplier_detail_ajax'),
    path('warehouse/<uuid:pk>/detail/ajax/', rest_views.WarehouseDetailAjaxAPIView.as_view(), name='warehouse_detail_ajax'),
    path('item/<int:pk>/delete/ajax/', rest_views.ItemDeleteAjaxAPIView.as_view(), name='item_delete_ajax'),
    path('supplier/<int:pk>/delete/ajax/', rest_views.SupplierDeleteAjaxAPIView.as_view(), name='supplier_delete_ajax'),
    path('warehouse/<uuid:pk>/delete/ajax/', rest_views.WarehouseDeleteAjaxAPIView.as_view(), name='warehouse_delete_ajax'),

    # CSV Template Download URLs
    path('item/csv-template/', rest_views.ItemCSVTemplateAPIView.as_view(), name='item_csv_template'),
    path('supplier/csv-template/', rest_views.SupplierCSVTemplateAPIView.as_view(), name='supplier_csv_template'),
    path('warehouse/csv-template/', rest_views.WarehouseCSVTemplateAPIView.as_view(), name='warehouse_csv_template'),
    # CSV Import URLs
    path('item/import-csv/', rest_views.ItemImportCSVAPIView.as_view(), name='item_import_csv'),
    path('supplier/import-csv/', rest_views.SupplierImportCSVAPIView.as_view(), name='supplier_import_csv'),
    path('warehouse/import-csv/', rest_views.WarehouseImportCSVAPIView.as_view(), name='warehouse_import_csv'),
]