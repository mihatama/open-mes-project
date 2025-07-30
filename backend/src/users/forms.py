# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['old_password', 'new_password1', 'new_password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
            # Django 4.0以降、PasswordChangeFormのヘルプテキストはフィールドのlabel_suffixや
            # フォームのerror_messagesなどでカスタマイズされることが多く、
            # field.help_text はデフォルトではあまり設定されていない場合があります。
            # 必要に応じて、ここで明示的に設定または削除できます。