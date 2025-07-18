from rest_framework import serializers
from ..models import CustomUser
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()

class CustomAuthTokenSerializer(serializers.Serializer):
    """
    Custom serializer for token authentication that uses the model's USERNAME_FIELD.
    This expects a JSON key that matches the USERNAME_FIELD (e.g., 'custom_id').
    """
    username_field_name = UserModel.USERNAME_FIELD

    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically add the username field based on the user model
        self.fields[self.username_field_name] = serializers.CharField(
            label=_(UserModel._meta.get_field(self.username_field_name).verbose_name.capitalize()),
            write_only=True
        )

    def validate(self, attrs):
        password = attrs.get('password')
        username = attrs.get(self.username_field_name)

        if username and password:
            # The `authenticate` function will use the USERNAME_FIELD to look up the user.
            user = authenticate(request=self.context.get('request'), username=username, password=password)

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "%(username_field)s" and "password".') % {
                'username_field': self.username_field_name
            }
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['custom_id', 'username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            custom_id=validated_data['custom_id'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            username=validated_data.get('username', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile fields by the user themselves.
    """
    class Meta:
        model = CustomUser
        # Users can update their username and email.
        fields = ['username', 'email', 'first_name', 'last_name']

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password1 = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("現在のパスワードが正しくありません。"))
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": _("新しいパスワードが一致しません。")})
        
        # Django's built-in password validation
        try:
            password_validation.validate_password(data['new_password1'], self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password1': e.messages})

        return data

class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for user management in the admin interface.
    Handles list, retrieve, create, and update operations.
    """
    # Password is write-only and not required for updates.
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = [
            'id', 'custom_id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'password'
        ]
        read_only_fields = ['date_joined']

    def create(self, validated_data):
        """
        Create a new user with a password.
        """
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Password is required for new users.'})
        
        user = CustomUser.objects.create_user(**validated_data, password=password)
        return user

    def update(self, instance, validated_data):
        """
        Update user instance. Handle password change separately.
        """
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password', 'password_last_changed'])
        return instance