from django.urls import path
from . import rest_views # inventory/rest_views.py をインポート
from . import views      # views.py をインポート (CSV関連ビューのため)

app_name = 'inventory_api'  # このURL設定の名前空間

urlpatterns = [
    # 問題のあった材料引当APIエンドポイント
    path('allocate-for-sales-order/', rest_views.allocate_inventory_for_sales_order_api, name='api_allocate_inventory_for_sales_order'),

    # その他の在庫関連APIエンドポイント
    path('purchase-orders/create/', rest_views.create_purchase_order_api, name='api_create_purchase_order'),
    path('stock-movements/data/', rest_views.get_stock_movement_data, name='api_get_stock_movement_data'), # APIパスを変更
    path('purchase-receipts/process/', rest_views.process_purchase_receipt_api, name='api_process_purchase_receipt'),
    path('data/', rest_views.get_inventory_data, name='api_get_inventory_data'),
    path('issue-single-order/', rest_views.process_single_sales_order_issue_api, name='api_process_single_sales_order_issue'),
    path('update/', rest_views.update_inventory_api, name='api_update_inventory'),
    path('move/', rest_views.move_inventory_api, name='api_move_inventory'), # New endpoint for moving inventory
    path('by-location/', rest_views.get_inventory_by_location_api, name='api_get_inventory_by_location'), # New endpoint for mobile screen
    path('location-transfer/', rest_views.location_transfer_api, name='api_location_transfer'), # New endpoint for mobile location transfer

    # Endpoint for the purchase.html page to fetch purchase order data
    path('schedules/data/', rest_views.get_purchase_orders_api, name='api_get_purchase_schedules_data'),

    # AJAX endpoint for creating Purchase Orders from the data_import page
    path('purchase-order/create/ajax/', rest_views.PurchaseOrderCreateAjaxAPIView.as_view(), name='purchase_order_create_ajax'),
    path('purchase-order/list/ajax/', rest_views.PurchaseOrderListAjaxAPIView.as_view(), name='purchase_order_list_ajax'),
    path('purchase-order/<uuid:pk>/detail/ajax/', rest_views.PurchaseOrderDetailAjaxAPIView.as_view(), name='purchase_order_detail_ajax'),
    path('sales-orders/data/', rest_views.get_sales_orders_for_issue_api, name='api_get_sales_orders_for_issue'), # 新しい出庫予定一覧API
    path('purchase-order/<uuid:pk>/delete/ajax/', rest_views.PurchaseOrderDeleteAjaxAPIView.as_view(), name='purchase_order_delete_ajax'),

    # CSV Template and Import URLs for Purchase Orders
    path('purchase-order/csv-template/', views.PurchaseOrderCSVTemplateView.as_view(), name='purchase_order_csv_template'),
    path('purchase-order/import-csv/', views.PurchaseOrderImportCSVView.as_view(), name='purchase_order_import_csv'),
]