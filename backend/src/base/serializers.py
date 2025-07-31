from rest_framework import serializers
from .models import CsvColumnMapping

class CsvColumnMappingSerializer(serializers.ModelSerializer):
    """
    CsvColumnMappingモデル用のシリアライザー。
    """
    data_type_display = serializers.CharField(source='get_data_type_display', read_only=True)

    class Meta:
        model = CsvColumnMapping
        fields = [
            'id',
            'data_type',
            'data_type_display',
            'csv_header',
            'model_field_name',
            'display_name',
            'order',
            'is_required',
            'is_active',
        ]
        read_only_fields = ['id', 'data_type_display']