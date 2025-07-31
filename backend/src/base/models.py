import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseSetting(models.Model):
    """
    システム全体の設定を管理するキーバリューモデル。
    各設定は個別のレコードとして保存されます。
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        _("項目名"),
        max_length=255,
        unique=True,
        help_text=_("設定項目を一意に識別するキー（例: 'site_name'）。")
    )
    value = models.TextField(
        _("設定値"),
        blank=True,
        help_text=_("設定項目の値。")
    )
    is_active = models.BooleanField(
        _("有効"),
        default=True,
        help_text=_("この設定が現在有効であるかを示します。")
    )
    is_deleted = models.BooleanField(
        _("削除フラグ"),
        default=False,
        help_text=_("レコードが論理的に削除されているかを示します。")
    )
    created_at = models.DateTimeField(_("作成日時"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新日時"), auto_now=True)

    class Meta:
        verbose_name = _("基本設定")
        verbose_name_plural = _("基本設定")
        ordering = ['name']

    def __str__(self):
        return self.name


class CsvColumnMapping(models.Model):
    """
    CSVインポート時の列名とモデルフィールドのマッピングを管理します。
    この設定はメモリにキャッシュして利用することを想定しています。
    """
    DATA_TYPE_CHOICES = [
        ('item', '品番マスター'),
        ('supplier', 'サプライヤーマスター'),
        ('warehouse', '倉庫マスター'),
        ('purchase_order', '入庫予定'),
        ('production_plan', '生産計画'),
        ('parts_used', '使用部品'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_type = models.CharField(
        _("データ種別"),
        max_length=50,
        choices=DATA_TYPE_CHOICES,
        help_text=_("どのデータのインポート設定かを選択します。")
    )
    csv_header = models.CharField(
        _("CSVヘッダー名"),
        max_length=255,
        help_text=_("CSVファイルで使用される列のヘッダー名です。")
    )
    model_field_name = models.CharField(
        _("モデルフィールド名"),
        max_length=255,
        help_text=_("対応するDjangoモデルのフィールド名です。")
    )
    display_name = models.CharField(
        _("表示名"),
        max_length=255,
        help_text=_("画面表示やテンプレート生成時に使用される人間可読な名前です。")
    )
    order = models.PositiveIntegerField(_("表示順"), default=0, help_text=_("テンプレート生成や表示順を制御するための数値です。小さい順に表示されます。"))
    is_required = models.BooleanField(_("必須項目"), default=True, help_text=_("CSVインポート時にこの列が必須かどうかを示します。"))
    is_active = models.BooleanField(_("有効"), default=True, help_text=_("このマッピングが現在有効であるかを示します。"))
    created_at = models.DateTimeField(_("作成日時"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新日時"), auto_now=True)

    class Meta:
        verbose_name = _("CSV列マッピング")
        verbose_name_plural = _("CSV列マッピング")
        ordering = ['data_type', 'order', 'csv_header']
        unique_together = [['data_type', 'csv_header'], ['data_type', 'model_field_name']]

    def __str__(self):
        return f"{self.get_data_type_display()}: {self.csv_header} -> {self.model_field_name}"
