# /home/ubuntu/git/open-mes-project/open_mes/scr/production/forms.py
from django import forms
from .models import ProductionPlan, PartsUsed

class ProductionPlanDataEntryForm(forms.ModelForm):
    class Meta:
        model = ProductionPlan
        fields = [
            'plan_name',
            'product_code',
            'production_plan', # This is the CharField for referenced plan name/ID
            'planned_quantity',
            'planned_start_datetime',
            'planned_end_datetime',
            'remarks',
        ]
        widgets = {
            'plan_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 製品X 5月生産計画'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: PROD-001'}),
            'production_plan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: REF-PLAN-002 (任意)'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 100'}),
            'planned_start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'planned_end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'plan_name': '計画名',
            'product_code': '製品コード',
            'production_plan': '参照生産計画',
            'planned_quantity': '計画数量',
            'planned_start_datetime': '計画開始日時',
            'planned_end_datetime': '計画終了日時',
            'remarks': '備考',
        }

    def clean(self):
        cleaned_data = super().clean()
        planned_start_datetime = cleaned_data.get("planned_start_datetime")
        planned_end_datetime = cleaned_data.get("planned_end_datetime")

        if planned_start_datetime and planned_end_datetime:
            if planned_start_datetime >= planned_end_datetime:
                self.add_error('planned_end_datetime', "計画終了日時は計画開始日時より後に設定してください。")
        return cleaned_data

class PartsUsedDataEntryForm(forms.ModelForm):
    class Meta:
        model = PartsUsed
        fields = [
            'production_plan',
            'part_code',
            'warehouse',
            'quantity_used',
            'remarks',
        ]
        widgets = {
            'production_plan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: PLAN-001 (生産計画識別子)'}),
            'part_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: PART-XYZ-001'}),
            'warehouse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: WH-MAIN (任意)'}),
            'quantity_used': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 10'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'production_plan': '生産計画識別子',
            'part_code': '部品コード',
            'warehouse': '使用倉庫',
            'quantity_used': '使用数量',
            'remarks': '備考',
        }