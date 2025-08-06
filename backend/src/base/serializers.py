from rest_framework import serializers
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from .models import CsvColumnMapping, ModelDisplaySetting, QrCodeAction, DATA_TYPE_MODEL_MAPPING


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


class QrCodeActionSerializer(serializers.ModelSerializer):
    """
    QrCodeActionモデル用のシリアライザー。
    """
    class Meta:
        model = QrCodeAction
        fields = [
            'id',
            'name',
            'description',
            'qr_code_pattern',
            'script',
            'is_active',
        ]
        read_only_fields = ['id']


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
            'search_order',
            'is_list_display',
            'is_search_field',
            'is_list_filter',
        ]
        validators = [] # bulk-save時にUniqueTogetherValidatorを無効化するため

    def get_verbose_name(self, obj):
        """
        モデルフィールド名からverbose_nameを取得する。
        'goods_receipt' は PurchaseOrder と Receipt の両方のフィールドを含む可能性があるため、
        両方のモデルをチェックする。
        """
        # チェック対象のモデルを決定
        models_to_check_strings = []
        if obj.data_type == 'goods_receipt':
            # goods_receipt は purchase_order と receipt のフィールドを持つ
            models_to_check_strings.append(DATA_TYPE_MODEL_MAPPING.get('purchase_order'))
            models_to_check_strings.append(DATA_TYPE_MODEL_MAPPING.get('goods_receipt'))
        else:
            models_to_check_strings.append(DATA_TYPE_MODEL_MAPPING.get(obj.data_type))

        # モデルを順番にチェックしてフィールドを探す
        for model_string in filter(None, models_to_check_strings):
            try:
                app_label, model_name = model_string.split('.')
                model = apps.get_model(app_label=app_label, model_name=model_name)
                field = model._meta.get_field(obj.model_field_name)
                return str(field.verbose_name) or obj.model_field_name
            except (LookupError, ValueError, FieldDoesNotExist):
                # このモデルにはフィールドがなかったので、次のモデルを試す
                continue

        # モデルフィールドに見つからなかった場合、プロパティをチェック
        if obj.data_type == 'goods_receipt' and obj.model_field_name == 'remaining_quantity': return '残数量'
        if obj.data_type == 'inventory' and obj.model_field_name == 'available_quantity': return '利用可能数'
        
        # それでも見つからなければフィールド名をそのまま返す
        return obj.model_field_name
