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
