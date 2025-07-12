from django import forms
from .models import Item, Supplier, Warehouse

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'code', 'item_type', 'description', 'unit', 'default_warehouse', 'default_location', 'provision_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 製品A'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: ITEM-001'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '製品の説明や特記事項など'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: kg, 個, m'}),
            'default_warehouse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 中央倉庫'}),
            'default_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: A-01-02'}),
            'provision_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': '品番名',
            'code': '品番コード',
            'item_type': '品目タイプ',
            'description': '説明',
            'unit': '単位',
            'default_warehouse': 'デフォルト入庫倉庫',
            'default_location': 'デフォルト入庫棚番',
            'provision_type': '支給種別',
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_number', 'name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'supplier_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: SUP-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 株式会社〇〇'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 山田 太郎'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 03-1234-5678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '例: contact@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例: 東京都千代田区...'})
        }
        labels = {
            'supplier_number': 'サプライヤー番号',
            'name': 'サプライヤー名', # 既存
            'contact_person': '担当者名',
            'phone': '電話番号',
            'email': 'メールアドレス',
            'address': '住所',
        }

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['warehouse_number', 'name', 'location']
        widgets = {
            'warehouse_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: WH-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 本社倉庫'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 東京都港区...'}),
        }
        labels = {
            'warehouse_number': '倉庫番号',
            'name': '倉庫名',
            'location': '所在地',
        }