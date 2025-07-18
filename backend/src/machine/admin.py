from django.contrib import admin
from .models import Machine

# Register your models here.

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_number', 'name', 'location', 'created_at')
    search_fields = ('machine_number', 'name', 'location')
    list_filter = ('created_at',)
