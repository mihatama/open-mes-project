from rest_framework import serializers
from .models import Item, Supplier, Warehouse
from rest_framework.validators import UniqueValidator

class ItemSerializer(serializers.ModelSerializer):
    # Override choice fields to return their display names for list views, as expected by the frontend.
    item_type = serializers.CharField(source='get_item_type_display', read_only=True)
    provision_type = serializers.CharField(source='get_provision_type_display', read_only=True)

    class Meta:
        model = Item
        fields = ('id', 'name', 'code', 'item_type', 'description', 'unit', 'default_warehouse', 'default_location', 'provision_type', 'created_at')
        # For create/update, we might not want to expose all fields or handle choices differently.
        # For now, this covers list/detail. Create/update will use forms or a more specific serializer.

class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'code', 'item_type', 'description', 'unit', 
            'default_warehouse', 'default_location', 'provision_type'
        ]
        # Add custom error messages for unique fields
        extra_kwargs = {
            'code': {
                'validators': [UniqueValidator(queryset=Item.objects.all(), message='この品番コードは既に使用されています。')],
            },
            'name': {
                'validators': [UniqueValidator(queryset=Item.objects.all(), message='この品番名は既に使用されています。')],
            },
        }


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'supplier_number', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at']

class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    # Explicitly define email to allow null and add custom validator
    email = serializers.EmailField(allow_blank=True, required=False, allow_null=True)

    class Meta:
        model = Supplier
        fields = ['id', 'supplier_number', 'name', 'contact_person', 'phone', 'email', 'address']
        extra_kwargs = {
            'supplier_number': {
                'validators': [UniqueValidator(queryset=Supplier.objects.all(), message='このサプライヤー番号は既に使用されています。')],
            },
        }

    def validate_name(self, value):
        # Custom validation to enforce name uniqueness, which is not a DB constraint.
        qs = Supplier.objects.filter(name=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("このサプライヤー名は他のサプライヤーで既に使用されています。")
        return value

    def validate_email(self, value):
        # Custom validation for email uniqueness (if provided).
        if not value:
            return value
        qs = Supplier.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("このメールアドレスは他のサプライヤーで既に使用されています。")
        return value


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'warehouse_number', 'name', 'location']

class WarehouseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'warehouse_number', 'name', 'location']
        extra_kwargs = {
            'warehouse_number': {
                'validators': [UniqueValidator(queryset=Warehouse.objects.all(), message='この倉庫番号は既に使用されています。')],
            },
        }