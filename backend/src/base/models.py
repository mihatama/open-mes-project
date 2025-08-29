import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


# 共通のデータ種別選択肢
DATA_TYPE_CHOICES = [
    ('item', _('品番マスター')),
    ('inventory', _('在庫')),
    ('supplier', _('サプライヤーマスター')),
    ('warehouse', _('倉庫マスター')),
    ('purchase_order', _('入庫予定')),
    ('sales_order', _('出庫予定')),
    ('goods_receipt', _('入庫実績')),
    ('production_plan', _('生産計画')),
    ('parts_used', _('使用部品')),
    ('base_setting', _('基本設定')),
    ('csv_column_mapping', _('CSV列マッピング')),
    ('model_display_setting', _('モデル項目表示設定')),
    ('qr_code_action', _('QRコードアクション')),
    ('stock_movement', _('入出庫履歴')),
]

# APIなどでモデル文字列とモデルクラスをマッピングするために使用
DATA_TYPE_MODEL_MAPPING = {
    'item': 'master.Item',
    'inventory': 'inventory.Inventory',
    'supplier': 'master.Supplier',
    'warehouse': 'master.Warehouse',
    'purchase_order': 'inventory.PurchaseOrder',
    'sales_order': 'inventory.SalesOrder',
    'goods_receipt': 'inventory.Receipt',
    'production_plan': 'production.ProductionPlan',
    'parts_used': 'production.PartsUsed',
    'base_setting': 'base.BaseSetting',
    'csv_column_mapping': 'base.CsvColumnMapping',
    'model_display_setting': 'base.ModelDisplaySetting',
    'qr_code_action': 'base.QrCodeAction',
}

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
    order = models.PositiveIntegerField(_("表示順"), default=0, help_text=_("テンプレート生成や表示順を制御するための数値です。小さい順に表示されます。"))
    is_update_key = models.BooleanField(
        _("上書きキー"),
        default=False,
        help_text=_("インポート時にこの列をキーとして既存データを検索し、更新します。")
    )
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


class ModelDisplaySetting(models.Model):
    """
    各モデルの管理画面での項目表示を管理します。
    表示項目、順序、検索・フィルタ設定ができます。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_type = models.CharField(
        _("データ種別"),
        max_length=50,
        choices=DATA_TYPE_CHOICES,
        help_text=_("どのデータモデルの表示設定かを選択します。")
    )
    display_name = models.CharField(
        _("カスタム表示名"),
        max_length=255,
        blank=True,
        help_text=_("一覧画面で表示されるカスタム名。空の場合はモデルのverbose_nameが使用されます。")
    )
    model_field_name = models.CharField(
        _("モデルフィールド名"),
        max_length=255,
        help_text=_("対応するDjangoモデルのフィールド名です。")
    )
    display_order = models.PositiveIntegerField(
        _("表示順"),
        default=10,
        help_text=_("一覧画面での表示順を制御します。小さい順に表示されます。")
    )
    search_order = models.PositiveIntegerField(
        _("検索順"),
        default=10,
        help_text=_("検索項目としての表示順を制御します。小さい順に表示されます。")
    )
    is_list_display = models.BooleanField(
        _("一覧表示"),
        default=True,
        help_text=_("この項目を一覧画面に表示するかどうかを示します。")
    )
    is_search_field = models.BooleanField(
        _("検索対象"),
        default=False,
        help_text=_("この項目を管理画面の検索ボックスの対象にするかを示します。")
    )
    is_list_filter = models.BooleanField(
        _("フィルタ対象"),
        default=False,
        help_text=_("この項目を管理画面のフィルタサイドバーに表示するかを示します。")
    )
    created_at = models.DateTimeField(_("作成日時"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新日時"), auto_now=True)

    class Meta:
        verbose_name = _("モデル項目表示設定")
        verbose_name_plural = _("モデル項目表示設定")
        ordering = ['data_type', 'display_order']
        unique_together = [['data_type', 'model_field_name']]

    def __str__(self):
        return f"{self.get_data_type_display()}: {self.model_field_name}"


class QrCodeAction(models.Model):
    """
    QRコード読み取り後のアクションを定義するモデル。
    特定のパターンにマッチするQRコードが読み取られた際に、
    定義されたPythonスクリプトを実行します。

    アクションタイプ:
    - 正規表現で判定 (regex): `qr_code_pattern` にマッチした場合に `script` を実行します。
    - スクリプトで判定 (script): `script` 内でQRデータの内容を判定し、アクションを決定します。
      `qr_code_pattern` は使用されません。
    """
    ACTION_TYPE_CHOICES = [
        ('regex', _('正規表現で判定')),
        ('script', _('スクリプトで判定')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        _("アクション名"),
        max_length=100,
        unique=True,
        help_text=_("アクションを一意に識別する名前。")
    )
    description = models.TextField(
        _("説明"),
        blank=True,
        help_text=_("このアクションが何をするかの説明。")
    )
    action_type = models.CharField(
        _("アクションタイプ"),
        max_length=10,
        choices=ACTION_TYPE_CHOICES,
        default='regex',
        help_text=_("アクションをトリガーする条件のタイプを選択します。")
    )
    qr_code_pattern = models.CharField(
        _("QRコードパターン"),
        max_length=255,
        blank=True,
        help_text=_("アクションタイプが「正規表現で判定」の場合に、マッチング対象となる正規表現パターン。例: '^ITEM-.+'")
    )
    script = models.TextField(
        _("実行スクリプト"),
        help_text=_("QRコードがマッチした際、またはスクリプト判定で実行されるPythonスクリプト。")
    )
    is_active = models.BooleanField(
        _("有効"),
        default=True,
        help_text=_("このアクションが現在有効であるかを示します。")
    )
    created_at = models.DateTimeField(_("作成日時"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新日時"), auto_now=True)

    class Meta:
        verbose_name = _("QRコードアクション")
        verbose_name_plural = _("QRコードアクション")
        ordering = ['name']

    def __str__(self):
        return self.name
