from rest_framework import serializers
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder # StockMovement, SalesOrderモデルをインポート
# master.modelsのインポートは、将来的に関連モデルとして扱うための準備か、
# あるいはビューなどで型ヒント等に利用されている可能性があります。
# 現状このシリアライザー内では直接参照されていません。
from master.models import Item, Supplier, Warehouse # masterアプリケーションからモデルをインポート

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    入庫予定モデルのためのシリアライザ。
    作成時には、仕入先名、品目名/コード、倉庫名を文字列として受け付けます。
    応答時には、読み取り専用フィールドを含む完全なオブジェクトを返します。
    """
    # モデルのフィールド定義に合わせて CharField としています。
    # supplier, item, warehouse は現状、masterアプリのモデルとは直接リンクされていません。
    supplier = serializers.CharField(max_length=255, allow_null=True, required=False)
    item = serializers.CharField(max_length=255, allow_null=True, required=False)
    warehouse = serializers.CharField(max_length=255, allow_null=True, required=False)
    location = serializers.CharField(max_length=255, allow_null=True, required=False, help_text="入庫棚番 (文字列、省略可能)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # help_text を現状のデータ型に合わせて修正
        self.fields['supplier'].help_text = "仕入先名 (文字列、省略可能)"
        self.fields['item'].help_text = "品目名または品目コード (文字列、省略可能)"
        self.fields['warehouse'].help_text = "入庫倉庫名 (文字列、省略可能)"
        # self.fields['location'].help_text is set above
        # フィールド定義で required=False が指定されているため、ここでの再設定は不要です。



    class Meta:
        model = PurchaseOrder
        fields = [
            'id',                   # ID (自動生成、読み取り専用)
            'order_number',         # 発注番号
            'supplier',             # 仕入先 (入力はID、出力はID)
            'item',                 # 品目 (入力はID、出力はID)
            'quantity',             # 発注数量
            'part_number',          # 品番 (任意)
            'product_name',         # 品名 (任意)
            'parent_part_number',   # 親品番 (任意)
            'instruction_document', # 指示書 (任意)
            'shipment_number',      # 便番号 (任意)
            'model_type',           # 機種 (任意)
            'is_first_time',        # 初回 (デフォルトFalse)
            'color_info',           # 色情報 (任意)
            'delivery_destination', # 納入先 (任意)
            'delivery_source',      # 納入元 (任意)
            'remarks1',             # 備考1 (任意)
            'remarks2',             # 備考2 (任意)
            'remarks3',             # 備考3 (任意)
            'remarks4',             # 備考4 (任意)
            'remarks5',             # 備考5 (任意)
            'received_quantity',    # 入庫済数量 (デフォルト0、読み取り専用)
            'order_date',           # 発注日 (自動設定、読み取り専用)
            'expected_arrival',     # 入荷予定日 (任意)
            'warehouse',            # 入庫倉庫
            'location',             # 入庫棚番 (任意)
            'status'                # ステータス (デフォルト'pending'、読み取り専用)
        ]
        read_only_fields = ['id', 'received_quantity', 'order_date', 'status'] # is_first_time はデフォルト値があるので読み取り専用には含めません

    def validate_order_number(self, value):
        """
        Validate that the order_number is unique.
        """
        # If updating an instance, exclude its own pk from the uniqueness check
        instance = self.instance
        if instance and instance.pk:
            if PurchaseOrder.objects.filter(order_number=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("この発注番号は他のレコードで既に使用されています。")
        elif PurchaseOrder.objects.filter(order_number=value).exists():
            raise serializers.ValidationError("この発注番号は既に使用されています。")
        return value
class InventorySerializer(serializers.ModelSerializer):
    """
    在庫情報モデルのためのシリアライザ。
    available_quantity プロパティも読み取り専用フィールドとして含みます。
    """
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id',
            'part_number',
            'warehouse',
            'quantity',
            'reserved',
            'available_quantity', # 利用可能在庫 (プロパティ)
            'location',
            'last_updated',
            'is_active',
            'is_allocatable',
        ]
        read_only_fields = ['id', 'last_updated', 'available_quantity']


class StockMovementSerializer(serializers.ModelSerializer):
    """
    入出庫履歴モデルのためのシリアライザ。
    """
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    operator_username = serializers.CharField(source='operator.username', read_only=True, allow_null=True)
    movement_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'part_number',
            'warehouse',
            'movement_type',
            'movement_type_display', # 表示用の移動タイプ名
            'quantity',
            'movement_date',
            'description',
            'reference_document',
            'operator_username',     # 記録者のユーザー名
        ]


class SalesOrderAllocationItemSerializer(serializers.Serializer):
    """
    Serializer for an individual item in a sales order allocation request.
    """
    part_number = serializers.CharField(max_length=255, help_text="Part number to allocate.")
    warehouse = serializers.CharField(max_length=255, help_text="Warehouse to allocate from.")
    quantity_to_reserve = serializers.IntegerField(min_value=1, help_text="Quantity to reserve.")

    class Meta:
        pass # No model to link, standard serializer


class AllocateInventoryForSalesOrderRequestSerializer(serializers.Serializer):
    """
    Serializer for the request to allocate inventory for a sales order.
    """
    sales_order_reference = serializers.CharField(
        max_length=20, # Align with SalesOrder.order_number max_length
        required=True,
        help_text="Reference identifier for the sales order (e.g., order number)."
    )
    allocations = SalesOrderAllocationItemSerializer(
        many=True,
        required=True,
        help_text="List of parts and quantities to allocate."
    )


class SalesOrderSerializer(serializers.ModelSerializer):
    """
    出庫予定モデルのためのシリアライザ。
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_quantity = serializers.IntegerField(read_only=True) # プロパティを読み取り専用フィールドとして追加

    class Meta:
        model = SalesOrder
        fields = [
            'id',
            'order_number',
            'item',
            'quantity',
            'shipped_quantity',
            'remaining_quantity', # 利用可能在庫 (プロパティ)
            'order_date',
            'expected_shipment',
            'warehouse',
            'status',
            'status_display', # 表示用のステータス名
        ]
        read_only_fields = ['id', 'order_date', 'shipped_quantity', 'remaining_quantity', 'status', 'status_display']
    def validate_allocations(self, value):
        if not value:
            raise serializers.ValidationError("Allocations list cannot be empty.")
        return value