from django.contrib import admin
from .models import BaseSetting, CsvColumnMapping

@admin.register(BaseSetting)
class BaseSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'value')
    ordering = ('name',)

@admin.register(CsvColumnMapping)
class CsvColumnMappingAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'csv_header', 'model_field_name', 'display_name', 'order', 'is_required', 'is_active')
    list_filter = ('data_type', 'is_active', 'is_required')
    search_fields = ('csv_header', 'model_field_name', 'display_name')
    ordering = ('data_type', 'order')
    list_editable = ('order', 'is_required', 'is_active')