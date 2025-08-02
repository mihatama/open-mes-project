from rest_framework import serializers
from .models import CsvColumnMapping, ModelDisplaySetting

class CsvColumnMappingSerializer(serializers.ModelSerializer):
    """
    CsvColumnMappingモデル用のシリアライザー。
    """
    data_type_display = serializers.CharField(source='get_data_type_display', read_only=True)

    class Meta:
        model = CsvColumnMapping
        fields = [
            'data_type',
            'data_type_display',
            'csv_header',
            'model_field_name',
            'order',
            'is_update_key',
            'is_active',
        ]
        read_only_fields = ['data_type_display']
        validators = [] # bulk-save時にUniqueTogetherValidatorを無効化するため


class ModelDisplaySettingSerializer(serializers.ModelSerializer):
    """
    ModelDisplaySettingモデル用のシリアライザー。
    """
    class Meta:
        model = ModelDisplaySetting
        fields = [
            'data_type',
            'model_field_name',
            'display_name',
            'display_order',
            'is_list_display',
            'is_search_field',
            'is_list_filter',
        ]
        validators = [] # bulk-save時にUniqueTogetherValidatorを無効化するため