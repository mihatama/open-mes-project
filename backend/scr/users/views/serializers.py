from rest_framework import serializers
from ..models import CustomUser

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