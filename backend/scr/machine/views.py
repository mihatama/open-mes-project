from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.

class MachineMenuView(LoginRequiredMixin, View):
    """設備管理のメインメニュー"""
    template_name = 'machine/menu.html'  # テンプレートファイル名を指定
    
    def get(self, request, *args, **kwargs):
        # 必要であれば、ここでコンテキストデータを準備
        context = {}  # 例：{'message': '設備管理メニューです'}
        return render(request, self.template_name, context)

class StartInspectionView(LoginRequiredMixin, View):
    """始業点検"""
    def get(self, request, *args, **kwargs):
        return render(request, 'machine/start_inspection.html')

class InspectionHistoryView(LoginRequiredMixin, View):
    """点検履歴"""
    def get(self, request, *args, **kwargs):
        return render(request, 'machine/inspection_history.html')

class MasterCreationView(LoginRequiredMixin, View):
    """マスター作成"""
    def get(self, request, *args, **kwargs):
        return render(request, 'machine/master_creation.html')
