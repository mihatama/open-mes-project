from django import forms
from django.forms import inlineformset_factory
from .models import InspectionItem, MeasurementDetail, InspectionResult, InspectionResultDetail

class InspectionItemForm(forms.ModelForm):
    class Meta:
        model = InspectionItem
        fields = [
            'code', 'name', 'description', 
            'inspection_type', 'target_object_type', 
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inspection_type': forms.Select(attrs={'class': 'form-control'}),
            'target_object_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MeasurementDetailForm(forms.ModelForm):
    class Meta:
        model = MeasurementDetail
        fields = [
            'name', 'measurement_type', 
            'specification_nominal', 'specification_upper_limit', 
            'specification_lower_limit', 'specification_unit',
            'expected_qualitative_result', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'measurement_type': forms.Select(attrs={'class': 'form-control form-control-sm measurement-type-select'}),
            'specification_nominal': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_upper_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_lower_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_unit': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'expected_qualitative_result': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

MeasurementDetailFormSet = inlineformset_factory(
    InspectionItem, MeasurementDetail, form=MeasurementDetailForm,
    extra=1, can_delete=True, can_order=False # `can_order=True` にするとDjangoが自動で順序フィールドを扱うが、今回は手動で'order'フィールドを設けた
)

class InspectionResultForm(forms.ModelForm):
    class Meta:
        model = InspectionResult
        fields = [
            'inspection_item', # This will be hidden and set programmatically
            'part_number', 'lot_number', 'serial_number',
            'related_order_type', 'related_order_number',
            'quantity_inspected',
            'judgment', 'remarks', 'attachment', 'equipment_used'
        ]
        widgets = {
            'inspection_item': forms.HiddenInput(),
            'part_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'related_order_type': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'related_order_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantity_inspected': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'judgment': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control-file form-control-file-sm'}),
            'equipment_used': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

class InspectionResultDetailForm(forms.ModelForm):
    measurement_name = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control-plaintext form-control-sm'}))
    measurement_type_display = forms.CharField(disabled=True, required=False, label="タイプ", widget=forms.TextInput(attrs={'class': 'form-control-plaintext form-control-sm'}))

    class Meta:
        model = InspectionResultDetail
        fields = ['measurement_detail', 'measured_value_numeric', 'result_qualitative', 'measurement_name', 'measurement_type_display']
        widgets = {
            'measurement_detail': forms.HiddenInput(),
            'measured_value_numeric': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'result_qualitative': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        measurement_detail_instance = kwargs.pop('measurement_detail_instance', None)
        super().__init__(*args, **kwargs)

        if measurement_detail_instance:
            self.fields['measurement_name'].initial = measurement_detail_instance.name
            self.fields['measurement_type_display'].initial = measurement_detail_instance.get_measurement_type_display()
            if measurement_detail_instance.measurement_type == 'quantitative':
                if 'result_qualitative' in self.fields: del self.fields['result_qualitative']
                self.fields['measured_value_numeric'].label = f"{measurement_detail_instance.name} ({measurement_detail_instance.specification_unit or '値'})"
                if measurement_detail_instance.specification_lower_limit is not None:
                    self.fields['measured_value_numeric'].widget.attrs['min'] = measurement_detail_instance.specification_lower_limit
                if measurement_detail_instance.specification_upper_limit is not None:
                    self.fields['measured_value_numeric'].widget.attrs['max'] = measurement_detail_instance.specification_upper_limit
                if measurement_detail_instance.specification_nominal is not None:
                    self.fields['measured_value_numeric'].widget.attrs['placeholder'] = f"規格値: {measurement_detail_instance.specification_nominal}"

            elif measurement_detail_instance.measurement_type == 'qualitative':
                if 'measured_value_numeric' in self.fields: del self.fields['measured_value_numeric']
                self.fields['result_qualitative'].label = measurement_detail_instance.name
                if measurement_detail_instance.expected_qualitative_result:
                     self.fields['result_qualitative'].widget.attrs['placeholder'] = f"期待結果: {measurement_detail_instance.expected_qualitative_result}"
            
            if 'measurement_detail' in self.fields:
                 self.fields['measurement_detail'].initial = measurement_detail_instance.pk

BaseInspectionResultDetailFormSet = forms.modelformset_factory(
    InspectionResultDetail,
    form=InspectionResultDetailForm,
    extra=0,
    can_delete=False
)