from django.db import models
from django.conf import settings
from django.utils import timezone
from uuid6 import uuid7

# Create your models here.

class InspectionItem(models.Model):
    """
    検査項目マスターモデル
    どのような検査を、どのような基準で行うかを定義します。
    """
    INSPECTION_TYPE_CHOICES = [
        ('acceptance', '受入検査'),
        ('in_process', '工程内検査'),
        ('final', '最終検査'),
        ('shipping', '出荷検査'),
        ('patrol', '巡回検査'),
    ]
    TARGET_OBJECT_CHOICES = [
        ('raw_material', '原材料'),
        ('component', '部品'),
        ('wip', '仕掛品'),
        ('finished_good', '完成品'),
        ('equipment', '設備'),
        ('process', '工程'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    code = models.CharField(max_length=50, unique=True, verbose_name="検査項目コード", help_text="検査項目を一意に識別するコード")
    name = models.CharField(max_length=255, verbose_name="検査項目名")
    description = models.TextField(blank=True, null=True, verbose_name="説明")
    inspection_type = models.CharField(
        max_length=20,
        choices=INSPECTION_TYPE_CHOICES,
        verbose_name="検査種別"
    )
    target_object_type = models.CharField(
        max_length=20,
        choices=TARGET_OBJECT_CHOICES,
        verbose_name="対象物タイプ"
    )

    is_active = models.BooleanField(default=True, verbose_name="有効フラグ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "検査項目マスター"
        verbose_name_plural = "検査項目マスター"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

class MeasurementDetail(models.Model):
    """
    検査項目に紐づく個別の測定・判定詳細モデル
    """
    MEASUREMENT_TYPE_CHOICES = [
        ('quantitative', '定量測定'),
        ('qualitative', '定性判定'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    inspection_item = models.ForeignKey(InspectionItem, related_name='measurement_details', on_delete=models.CASCADE, verbose_name="検査項目")
    name = models.CharField(max_length=255, verbose_name="測定・判定名", help_text="例: 外観確認, 寸法A測定")
    measurement_type = models.CharField(
        max_length=20,
        choices=MEASUREMENT_TYPE_CHOICES,
        verbose_name="測定タイプ"
    )
    
    # 定量測定の場合
    specification_nominal = models.FloatField(null=True, blank=True, verbose_name="規格値（中心値）")
    specification_upper_limit = models.FloatField(null=True, blank=True, verbose_name="規格上限値")
    specification_lower_limit = models.FloatField(null=True, blank=True, verbose_name="規格下限値")
    specification_unit = models.CharField(max_length=50, blank=True, null=True, verbose_name="単位")

    # 定性判定の場合
    expected_qualitative_result = models.CharField(max_length=100, blank=True, null=True, verbose_name="期待結果（定性）", help_text="例: OK, 異常なし, 傷なし")

    order = models.PositiveIntegerField(default=0, verbose_name="表示順")

    class Meta:
        verbose_name = "測定・判定詳細"
        verbose_name_plural = "測定・判定詳細"
        ordering = ['inspection_item', 'order', 'name']

    def __str__(self):
        return f"{self.inspection_item.code} - {self.name} ({self.get_measurement_type_display()})"


class InspectionResult(models.Model):
    """
    検査実績モデル
    実際に行われた検査の結果を記録します。
    """
    JUDGMENT_CHOICES = [
        ('pass', '合格'),
        ('fail', '不合格'),
        ('pending', '保留'),
        ('conditional_pass', '条件付き合格'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    inspection_item = models.ForeignKey(
        InspectionItem,
        on_delete=models.PROTECT, # マスターデータは実績があっても保護
        related_name='results',
        verbose_name="検査項目"
    )
    inspected_at = models.DateTimeField(default=timezone.now, verbose_name="検査日時")
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # 検査員が削除されても記録は残す
        null=True,
        blank=True,
        verbose_name="検査員"
    )
    
    # 検査対象の識別情報
    part_number = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="品番")
    lot_number = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="ロット番号")
    serial_number = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="シリアル番号")
    
    related_order_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="関連オーダータイプ", help_text="例: 製造指示, 購買発注, 出荷指示")
    related_order_number = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="関連オーダー番号")

    quantity_inspected = models.PositiveIntegerField(null=True, blank=True, verbose_name="検査数量")
    
    # 実際の検査結果
    measured_value_numeric = models.FloatField(null=True, blank=True, verbose_name="測定値（定量）")
    result_qualitative = models.CharField(max_length=100, blank=True, null=True, verbose_name="結果（定性）")
    
    judgment = models.CharField(
        max_length=20,
        choices=JUDGMENT_CHOICES,
        default='pending', # 検査記録作成時のデフォルト判定を「保留」に設定
        verbose_name="判定結果"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    attachment = models.FileField(upload_to='quality/inspection_attachments/%Y/%m/%d/', null=True, blank=True, verbose_name="添付ファイル")
    
    equipment_used = models.CharField(max_length=255, blank=True, null=True, verbose_name="使用設備/測定器")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "検査実績"
        verbose_name_plural = "検査実績"
        ordering = ['-inspected_at', 'inspection_item']

    def __str__(self):
        return f"検査結果 {self.id} ({self.inspection_item.name} - {self.get_judgment_display()})"


class InspectionResultDetail(models.Model):
    """
    検査実績に紐づく個別の測定・判定結果詳細モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name="ID")
    inspection_result = models.ForeignKey(
        InspectionResult,
        related_name='details',
        on_delete=models.CASCADE,
        verbose_name="検査実績"
    )
    measurement_detail = models.ForeignKey(
        MeasurementDetail,
        on_delete=models.PROTECT, # マスターデータは保護
        verbose_name="測定・判定詳細"
    )
    measured_value_numeric = models.FloatField(null=True, blank=True, verbose_name="測定値（定量）")
    result_qualitative = models.CharField(max_length=100, blank=True, null=True, verbose_name="結果（定性）")

    class Meta:
        verbose_name = "検査実績詳細"
        verbose_name_plural = "検査実績詳細"
        ordering = ['inspection_result', 'measurement_detail__order']

    def __str__(self):
        return f"結果: {self.measurement_detail.name} (実績ID: {self.inspection_result.id})"
