# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'username': _('サイトでの表示名。'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['old_password', 'new_password1', 'new_password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
            # Django 4.0以降、PasswordChangeFormのヘルプテキストはフィールドのlabel_suffixや
            # フォームのerror_messagesなどでカスタマイズされることが多く、
            # field.help_text はデフォルトではあまり設定されていない場合があります。
            # 必要に応じて、ここで明示的に設定または削除できます。
            # self.fields[fieldname].help_text = None # 例: ヘルプテキストを削除する場合

class AdminUserCreationForm(forms.ModelForm):
    """管理者用のユーザー作成フォーム"""
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, label=_("Password confirmation"))

    class Meta:
        model = CustomUser
        fields = ('custom_id', 'username', 'email', 'is_staff', 'is_active')
        widgets = {
            'custom_id': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class AdminUserChangeForm(forms.ModelForm):
    """管理者用のユーザー編集フォーム"""
    # パスワードは任意で変更できるように、必須ではなくす
    password = forms.CharField(widget=forms.PasswordInput, required=False, label=_("New password"), help_text=_("Leave blank to keep the current password."))
    password2 = forms.CharField(widget=forms.PasswordInput, required=False, label=_("New password confirmation"))

    class Meta:
        model = CustomUser
        # custom_id は変更不可にすることが多いので、fieldsから外すか、readonlyにする
        fields = ('custom_id', 'username', 'email', 'is_staff', 'is_active')
        widgets = {
            'custom_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}), # 変更不可にする
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user