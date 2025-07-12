from rest_framework import serializers
from .models import Item, Supplier, Warehouse

class ItemSerializer(serializers.ModelSerializer):
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    provision_type_display = serializers.CharField(source='get_provision_type_display', read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'code', 'item_type', 'item_type_display', 'description', 'unit',
            'default_warehouse', 'default_location', 'provision_type', 'provision_type_display',
            'created_at'
        ]
        # For create/update, we might not want to expose all fields or handle choices differently.
        # For now, this covers list/detail. Create/update will use forms or a more specific serializer.

class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'code', 'item_type', 'description', 'unit', 'default_warehouse', 'default_location', 'provision_type']


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'supplier_number', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at']

class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'supplier_number', 'name', 'contact_person', 'phone', 'email', 'address']


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'warehouse_number', 'name', 'location']

class WarehouseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'warehouse_number', 'name', 'location']