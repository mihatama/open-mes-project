from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ItemForm, SupplierForm, WarehouseForm # Keep for DataImportView
# production.forms と inventory.forms は DataImportView の get_context_data で使用
from production.forms import ProductionPlanDataEntryForm, PartsUsedDataEntryForm
from inventory.forms import PurchaseOrderEntryForm

# Create your views here.

# DataImportView は Django TemplateView のままで、CSVアップロードフォームの表示を担当します。
# フォームの action URL の先が rest_views.py の APIView になります。
class DataImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/data_import.html'
    # inventory.formsからPurchaseOrderEntryFormをインポート
    from inventory.forms import PurchaseOrderEntryForm
    from production.forms import PartsUsedDataEntryForm # 使用部品登録フォームをインポート

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'データ投入'
        context['item_form'] = ItemForm()
        context['supplier_form'] = SupplierForm()
        context['warehouse_form'] = WarehouseForm()
        context['inventory_purchase_entry_form'] = PurchaseOrderEntryForm()
        context['parts_used_data_entry_form'] = PartsUsedDataEntryForm()
        context['production_plan_data_entry_form'] = ProductionPlanDataEntryForm()
        return context

class MasterCreationView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/master_creation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'マスター作成'
        return context

# CSVインポート関連のビュー (BaseCSVImportView およびそのサブクラス、CSVテンプレートダウンロードビュー) は
# master/rest_views.py に APIView として移動しました。
