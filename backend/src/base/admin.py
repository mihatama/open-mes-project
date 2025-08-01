from django.contrib import admin
from .models import BaseSetting, CsvColumnMapping, ModelDisplaySetting

@admin.register(BaseSetting)
class BaseSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'value')
    ordering = ('name',)

@admin.register(CsvColumnMapping)
class CsvColumnMappingAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'csv_header', 'model_field_name', 'order', 'is_update_key', 'is_active')
    list_filter = ('data_type', 'is_active', 'is_update_key')
    search_fields = ('csv_header', 'model_field_name')
    ordering = ('data_type', 'order')
    list_editable = ('order', 'is_update_key', 'is_active')

@admin.register(ModelDisplaySetting)
class ModelDisplaySettingAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'model_field_name', 'display_name', 'display_order', 'updated_at')
    list_filter = ('data_type',)
    search_fields = ('model_field_name', 'display_name')
    ordering = ('data_type', 'display_order')
    list_editable = ('display_name', 'display_order')