from django.contrib import admin
from .models import Item, Supplier, Warehouse

# Register your models here.

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'item_type', 'unit', 'default_warehouse', 'default_location', 'provision_type', 'created_at')
    list_filter = ('item_type', 'provision_type', 'created_at')
    search_fields = ('name', 'code', 'default_warehouse', 'default_location')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_number', 'name', 'contact_person', 'phone', 'email', 'created_at')
    search_fields = ('supplier_number', 'name', 'contact_person', 'email')

admin.site.register(Warehouse)
