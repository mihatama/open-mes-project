from django.db import models
# from master.models import Item, Supplier, Warehouse
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
import uuid
from uuid6 import uuid7
# 在庫情報
class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")  # UUIDv7を使用
    part_number = models.CharField(max_length=255, null=True, blank=True, verbose_name="品番")  # 管理対象の製品/材料の品番 (文字列として保持)
    warehouse = models.CharField(max_length=255, null=True, blank=True, verbose_name="倉庫")  # 倉庫 (文字列として保持)
    quantity = models.IntegerField(default=0, verbose_name="在庫数量")  # 在庫
    reserved = models.IntegerField(default=0, verbose_name="引当済数量")  # 引当在庫
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="棚番")  # 倉庫や棚の場所
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最終更新日時")  # 更新日時
    is_active = models.BooleanField(default=True, verbose_name="有効フラグ")  # 在庫が有効かどうか
    is_allocatable = models.BooleanField(default=True, verbose_name="引当可能フラグ")  # 引き当て可能かどうか
    
    @property
    def available_quantity(self):
        """実際に利用可能な在庫（total - reserved）"""
        if not self.is_active or not self.is_allocatable:
            return 0  # 在庫が無効または引き当て不可なら利用不可
        return max(0, self.quantity - self.reserved)

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        allocatable = "Allocatable" if self.is_allocatable else "Not Allocatable"
        part_number_display = self.part_number if self.part_number else "N/A"
        warehouse_display = self.warehouse if self.warehouse else "N/A"
        return f"{part_number_display} - {self.quantity} in {warehouse_display} ({self.location}) [{status}, {allocatable}]"



# 入出庫履歴
class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    MOVEMENT_TYPE_CHOICES = [
        ('incoming', '入庫'),
        ('outgoing', '出庫'),
        ('used', '生産使用'),
        ('PRODUCTION_OUTPUT', '生産完了入庫'),
        ('PRODUCTION_REVERSAL', '生産完了取消'),
        ('adjustment', '在庫調整'),
    ]

    part_number = models.CharField(max_length=255, null=True, blank=True, verbose_name="品番")  # 在庫対象の製品/材料の品番 (文字列として保持)
    warehouse = models.CharField(max_length=255, null=True, blank=True, verbose_name="倉庫") # どの倉庫に関連する移動か
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="棚番") # どの棚番に関連する移動か
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES, verbose_name="移動タイプ")  # 入庫・出庫・使用
    quantity = models.PositiveIntegerField(verbose_name="数量")  # 数量
    movement_date = models.DateTimeField(default=timezone.now, verbose_name="移動日時")  # 変更日時
    description = models.TextField(blank=True, null=True, verbose_name="備考")  # 備考
    reference_document = models.CharField(max_length=255, blank=True, null=True, verbose_name="参照ドキュメント") # 例: PO-123, SO-456, ProductionPlan-789
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="記録者"
    )

    def __str__(self):
        return f"{self.part_number or 'N/A'} - {self.movement_type} - {self.quantity}"


# 入庫予定
class PurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="発注番号", null=True, blank=True)  # 発注番号
    supplier = models.CharField(max_length=255,  null=True, blank=True, verbose_name="仕入先")  # 仕入れ先
    item = models.CharField(max_length=255,  null=True, blank=True, verbose_name="品目")  # 発注対象（製品・材料）
    quantity = models.PositiveIntegerField(verbose_name="発注数量", null=True, blank=True)  # 発注数量
    received_quantity = models.PositiveIntegerField(default=0, verbose_name="入庫済数量")
    part_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="品番")
    product_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="品名")
    parent_part_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="親品番")
    instruction_document = models.CharField(max_length=255, blank=True, null=True, verbose_name="指示書")
    shipment_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="便番号")
    model_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="機種")
    is_first_time = models.BooleanField(default=False, verbose_name="初回", null=True, blank=True)
    color_info = models.CharField(max_length=100, blank=True, null=True, verbose_name="色情報")
    delivery_destination = models.CharField(max_length=255, blank=True, null=True, verbose_name="納入先")
    delivery_source = models.CharField(max_length=255, blank=True, null=True, verbose_name="納入元")
    remarks1 = models.TextField(blank=True, null=True, verbose_name="備考1")
    remarks2 = models.TextField(blank=True, null=True, verbose_name="備考2")
    remarks3 = models.TextField(blank=True, null=True, verbose_name="備考3")
    remarks4 = models.TextField(blank=True, null=True, verbose_name="備考4")
    remarks5 = models.TextField(blank=True, null=True, verbose_name="備考5")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="発注日")  # 発注日
    expected_arrival = models.DateTimeField(blank=True, null=True, verbose_name="入荷予定日時")  # 到着予定日
    warehouse = models.CharField(max_length=255, blank=True, null=True, verbose_name="入庫倉庫") # どの倉庫に入庫するかを追加
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="入庫棚番") # どの棚番に入庫するかを追加
    status = models.CharField(max_length=20, choices=[
        ('pending', '未入庫'),
        ('partially_received', '一部入庫'),
        ('fully_received', '全量入庫済み'),
        ('canceled', 'キャンセル')
    ], default='pending', verbose_name="ステータス", null=True, blank=True)
    def __str__(self):
        item_display = self.item if self.item else "N/A"
        return f"PO {self.order_number} - {item_display} ({self.status})"

    @property
    def remaining_quantity(self):
        """残りの未入庫数量を計算して返す"""
        return self.quantity - self.received_quantity

# 入庫実績
class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='receipts',
        verbose_name="入庫予定"
    )
    received_quantity = models.PositiveIntegerField(verbose_name="入庫数量")
    received_date = models.DateTimeField(default=timezone.now, verbose_name="入庫日")
    warehouse = models.CharField(max_length=255, verbose_name="入庫倉庫")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="入庫棚番")
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="作業者"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")

    def __str__(self):
        return f"Receipt for {self.purchase_order.order_number} - Qty: {self.received_quantity}"

    class Meta:
        verbose_name = "入庫実績"
        verbose_name_plural = "入庫実績"
        ordering = ['-received_date']

# 出庫予定
class SalesOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="受注番号")  # 受注番号
    item = models.CharField(max_length=255, null=True, blank=True, verbose_name="出庫対象（製品・材料）")  # 出庫対象（製品・材料）
    quantity = models.PositiveIntegerField(verbose_name="出庫予定数量")  # 出庫予定数量
    shipped_quantity = models.PositiveIntegerField(default=0, verbose_name="出庫済数量") # 実際に出庫した数量を保持
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="受注日")  # 受注日
    expected_shipment = models.DateTimeField(blank=True, null=True, verbose_name="出庫予定日時")  # 出庫予定日
    warehouse = models.CharField(max_length=255, null=True, blank=True, verbose_name="出庫倉庫") # どの倉庫から出庫するかを追加
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),  # 未出庫
        ('shipped', 'Shipped'),  # 出庫済み
        ('canceled', 'Canceled')  # キャンセル
    ], default='pending', verbose_name="ステータス")

    def __str__(self):
        item_display = self.item if self.item else "N/A"
        return f"SO {self.order_number} - {item_display} ({self.status})"

    @property
    def remaining_quantity(self):
        return self.quantity - self.shipped_quantity
