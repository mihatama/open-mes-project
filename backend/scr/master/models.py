from django.db import models
from uuid6 import uuid7


# 品番マスター
class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('product', 'Product'),  # 製品
        ('material', 'Material')  # 材料
    ]
    PROVISION_TYPE_CHOICES = [
        ('paid', '有償支給'),
        ('free', '無償支給'),
        ('none', '支給なし'),
    ]

    name = models.CharField(max_length=255, unique=True)  # 名称
    code = models.CharField(max_length=50, unique=True)  # 製品/材料コード
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)  # 製品 or 材料
    description = models.TextField(blank=True, null=True)  # 説明
    unit = models.CharField(max_length=10, default="kg")  # 単位 (例: kg, 個)
    default_warehouse = models.CharField(max_length=255, blank=True, null=True, verbose_name="デフォルト入庫倉庫") # デフォルト入庫倉庫
    default_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="デフォルト入庫棚番") # デフォルト入庫棚番
    provision_type = models.CharField(
        max_length=10,
        choices=PROVISION_TYPE_CHOICES,
        default='none',  # デフォルト値を「支給なし」に設定
        blank=True, null=True,
        verbose_name="支給種別"
    ) # 有償支給、無償支給等
    created_at = models.DateTimeField(auto_now_add=True)  # 登録日時

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"
# サプライヤーマスター
class Supplier(models.Model):
    supplier_number = models.CharField(max_length=50, unique=True, verbose_name="サプライヤー番号") # 新規追加
    name = models.CharField(max_length=255, verbose_name="サプライヤー名")  # unique=True を削除 (サプライヤー番号を主キーとするため)
    contact_person = models.CharField(max_length=255, blank=True, null=True)  # 担当者名
    phone = models.CharField(max_length=50, blank=True, null=True)  # 電話番号
    email = models.EmailField(blank=True, null=True)  # メールアドレス
    address = models.TextField(blank=True, null=True)  # 住所
    created_at = models.DateTimeField(auto_now_add=True)  # 登録日時

    def __str__(self):
        return f"{self.supplier_number} - {self.name}"
    
# 倉庫マスター
class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)  # UUIDv7 を使用
    warehouse_number = models.CharField(max_length=50, unique=True)  # 倉庫番号（ユニーク）
    name = models.CharField(max_length=255)  # 倉庫名
    location = models.CharField(max_length=255, blank=True, null=True)  # 住所や場所情報

    def __str__(self):
        return f"{self.warehouse_number} - {self.name}"