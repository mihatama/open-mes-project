from rest_framework import serializers
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from .models import CsvColumnMapping, ModelDisplaySetting, DATA_TYPE_MODEL_MAPPING


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
    verbose_name = serializers.SerializerMethodField()

    class Meta:
        model = ModelDisplaySetting
        fields = [
            'data_type',
            'model_field_name',
            'display_name',
            'verbose_name',
            'display_order',
            'is_list_display',
            'is_search_field',
            'is_list_filter',
        ]
        validators = [] # bulk-save時にUniqueTogetherValidatorを無効化するため

    def get_verbose_name(self, obj):
        """
        モデルフィールド名からverbose_nameを取得する。
        モデルに存在しないプロパティなどの場合は、ハードコードした値を返す。
        """
        model_string = DATA_TYPE_MODEL_MAPPING.get(obj.data_type)
        if not model_string:
            return obj.model_field_name
        try:
            app_label, model_name = model_string.split('.')
            model = apps.get_model(app_label=app_label, model_name=model_name)
            field = model._meta.get_field(obj.model_field_name)
            # verbose_nameが空文字列の場合も考慮し、フォールバックする
            return str(field.verbose_name) or obj.model_field_name
        except (LookupError, ValueError, FieldDoesNotExist):
            # Handle properties/custom fields that are not real model fields
            if obj.data_type == 'purchase_order':
                if obj.model_field_name == 'remaining_quantity':
                    return '残数量'
                if obj.model_field_name == 'received_quantity':
                    return '入庫済数量'
            # Fallback to the field name itself
            return obj.model_field_name
