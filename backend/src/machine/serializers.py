from rest_framework import serializers
from .models import Machine
from rest_framework.validators import UniqueValidator

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ['id', 'machine_number', 'name', 'location', 'description', 'created_at']

class MachineCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ['id', 'machine_number', 'name', 'location', 'description']
        extra_kwargs = {
            'machine_number': {
                'validators': [UniqueValidator(queryset=Machine.objects.all(), message='この設備番号は既に使用されています。')],
            },
        }