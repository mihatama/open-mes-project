from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    """ユーザーオブジェクト用のシリアライザー"""
    class Meta:
        model = CustomUser
        fields = ('custom_id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """暗号化されたパスワードで新しいユーザーを作成して返す"""
        return CustomUser.objects.create_user(**validated_data)

class CustomAuthTokenSerializer(serializers.Serializer):
    """ユーザー認証オブジェクト用のシリアライザー"""
    custom_id = serializers.CharField(label=_("Custom ID"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        custom_id = attrs.get('custom_id')
        password = attrs.get('password')

        if custom_id and password:
            user = authenticate(request=self.context.get('request'),
                                custom_id=custom_id, password=password)

            if not user:
                msg = _('提供された認証情報でログインできません。')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('"custom_id" と "password" を含める必要があります。')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class AdminUserSerializer(serializers.ModelSerializer):
    """管理者によるユーザー管理用のシリアライザー"""
    class Meta:
        model = CustomUser
        fields = [
            'id', 'custom_id', 'username', 'email', 'is_staff', 'is_superuser', 'is_active',
            'date_joined', 'last_login', 'password_last_changed'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'password_last_changed']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """ユーザープロファイル更新用のシリアライザー"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email']

class PasswordChangeSerializer(serializers.Serializer):
    """パスワード変更エンドポイント用のシリアライザー"""
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("現在のパスワードが正しくありません。"))
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": _("2つのパスワードフィールドが一致しません。")})
        # ここでDjangoのパスワードバリデーションを呼び出すことも可能です
        # from django.contrib.auth import password_validation
        # password_validation.validate_password(data['new_password1'], self.context['request'].user)
        return data