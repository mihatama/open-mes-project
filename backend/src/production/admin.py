from django.contrib import admin
from .models import ProductionPlan, PartsUsed, MaterialAllocation, WorkProgress

# Register your models here.

@admin.register(ProductionPlan)
class ProductionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'product_code', 'planned_quantity', 'planned_start_datetime', 'status', 'created_at')
    list_filter = ('status', 'planned_start_datetime')
    search_fields = ('plan_name', 'product_code')
    date_hierarchy = 'planned_start_datetime'

@admin.register(PartsUsed)
class PartsUsedAdmin(admin.ModelAdmin):
    list_display = ('production_plan', 'part_code', 'warehouse', 'quantity_used', 'used_datetime')
    list_filter = ('used_datetime', 'warehouse')
    search_fields = ('production_plan', 'part_code', 'warehouse') # production_plan は CharField になったため直接検索
    # autocomplete_fields は ForeignKey または ManyToManyField で使用されるため削除

@admin.register(MaterialAllocation)
class MaterialAllocationAdmin(admin.ModelAdmin):
    list_display = ('production_plan', 'material_code', 'allocated_quantity', 'status', 'allocation_datetime')
    list_filter = ('status', 'allocation_datetime')
    search_fields = ('production_plan__plan_name', 'material_code')
    autocomplete_fields = ['production_plan']

@admin.register(WorkProgress)
class WorkProgressAdmin(admin.ModelAdmin):
    list_display = ('production_plan', 'process_step', 'operator', 'status', 'start_datetime', 'end_datetime', 'quantity_completed', 'actual_reported_quantity', 'defective_reported_quantity')
    list_filter = ('status', 'process_step', 'operator')
    search_fields = ('production_plan__plan_name', 'process_step', 'operator__username')
    autocomplete_fields = ['production_plan', 'operator']
