from django.contrib import admin
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder

# Register your models here.

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'product_name', 'item', 'supplier', 'quantity',
        'received_quantity', 'expected_arrival', 'warehouse', 'location', 'status'
    )
    list_filter = ('status', 'supplier', 'warehouse', 'expected_arrival', 'order_date')
    search_fields = ('order_number', 'item', 'product_name', 'supplier')
    date_hierarchy = 'expected_arrival'

admin.site.register(Inventory)
admin.site.register(StockMovement)
admin.site.register(SalesOrder)
