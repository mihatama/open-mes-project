from django.contrib import admin
from .models import BaseSetting, CsvColumnMapping, ModelDisplaySetting

class DynamicAdminMixin:
    """
    ModelDisplaySetting に基づいて Admin の表示を動的に変更する Mixin。
    使用するクラスで `_data_type` 属性を定義する必要がある。
    """
    def get_dynamic_settings(self, field_name):
        if not hasattr(self, '_data_type') or not self._data_type:
            return None
        
        filter_kwargs = {
            'data_type': self._data_type,
            field_name: True
        }
        settings = ModelDisplaySetting.objects.filter(**filter_kwargs).order_by('display_order').values_list('model_field_name', flat=True)
        
        return list(settings) if settings.exists() else None

    def get_list_display(self, request):
        dynamic_list_display = self.get_dynamic_settings('is_list_display')
        if dynamic_list_display is not None:
            editable = self.get_list_editable(request)
            editable_list = list(editable) if editable else []
            # list_editable の項目が dynamic_list_display に含まれていることを保証する
            for item in editable_list:
                if item not in dynamic_list_display:
                    dynamic_list_display.append(item)
            return dynamic_list_display
        return super().get_list_display(request)

    def get_search_fields(self, request):
        dynamic_search_fields = self.get_dynamic_settings('is_search_field')
        if dynamic_search_fields is not None:
            return dynamic_search_fields
        return super().get_search_fields(request)

    def get_list_filter(self, request):
        dynamic_list_filter = self.get_dynamic_settings('is_list_filter')
        if dynamic_list_filter is not None:
            return dynamic_list_filter
        return super().get_list_filter(request)

@admin.register(BaseSetting)
class BaseSettingAdmin(DynamicAdminMixin, admin.ModelAdmin):
    _data_type = 'base_setting'
    list_display = ('name', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'value')
    ordering = ('name',)

@admin.register(CsvColumnMapping)
class CsvColumnMappingAdmin(DynamicAdminMixin, admin.ModelAdmin):
    _data_type = 'csv_column_mapping'
    list_display = ('data_type', 'csv_header', 'model_field_name', 'order', 'is_update_key', 'is_active')
    list_filter = ('data_type', 'is_active', 'is_update_key')
    search_fields = ('csv_header', 'model_field_name')
    ordering = ('data_type', 'order')
    list_editable = ('order', 'is_update_key', 'is_active')

@admin.register(ModelDisplaySetting)
class ModelDisplaySettingAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'model_field_name', 'display_name', 'display_order', 'is_list_display', 'is_search_field', 'is_list_filter', 'updated_at')
    list_filter = ('data_type', 'is_list_display', 'is_search_field', 'is_list_filter')
    search_fields = ('model_field_name', 'display_name')
    ordering = ('data_type', 'display_order')
    list_editable = ('display_name', 'display_order', 'is_list_display', 'is_search_field', 'is_list_filter')