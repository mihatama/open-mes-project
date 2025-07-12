from django import forms
from .models import PurchaseOrder

class IssueForm(forms.Form):
    sales_order_number = forms.CharField(
        label="受注番号 (またはスキャンデータ)",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': '受注番号を入力またはスキャン', 'autofocus': 'autofocus'})
    )
    quantity_to_ship = forms.IntegerField(
        label="出庫数量",
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '出庫する数量'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If you need to dynamically update choices or fields, you can do it here.
        # For example, if barcode input should dynamically populate sales_order_selector:
        # self.fields['sales_order_selector'].choices = ...

class PurchaseOrderEntryForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'order_number',
            'supplier',
            'item',
            'part_number',
            'product_name',
            'quantity',
            'expected_arrival',
            'warehouse',
            'location', # Add new location field
            'parent_part_number',
            'instruction_document',
            'shipment_number',
            'model_type',
            'is_first_time',
            'color_info',
            'delivery_destination',
            'delivery_source',
            'remarks1',
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: PO-00123'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 株式会社仕入先商事'}),
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 主要部品セットA'}),
            'part_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: ABC-12345'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 高性能モーターユニット'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'expected_arrival': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'warehouse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 中央倉庫'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: A-01-02'}), # Add widget for location
            'parent_part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'instruction_document': forms.TextInput(attrs={'class': 'form-control'}),
            'shipment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.TextInput(attrs={'class': 'form-control'}),
            'is_first_time': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color_info': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_destination': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_source': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'order_number': '一意の発注番号を入力してください。',
        }

    def clean_order_number(self):
        order_number = self.cleaned_data.get('order_number')
        # If updating an instance, exclude its own pk from the uniqueness check
        if self.instance and self.instance.pk:
            if PurchaseOrder.objects.filter(order_number=order_number).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("この発注番号は他のレコードで既に使用されています。")
        # If creating a new instance
        elif PurchaseOrder.objects.filter(order_number=order_number).exists():
            raise forms.ValidationError("この発注番号は既に使用されています。")
        return order_number