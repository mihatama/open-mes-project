from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from ..forms import IssueForm
from ..models import SalesOrder, Inventory, StockMovement # Make sure Inventory and StockMovement are imported
from django.contrib.auth.mixins import LoginRequiredMixin

# 在庫照会
class InquiryView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'inventory/inquiry.html'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 入出庫履歴 (旧 入庫予定)
class StockMovementHistoryView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'inventory/stock_movement_history.html' # テンプレート名を変更
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 出庫予定
class ShipmentView(LoginRequiredMixin, generic.ListView):
    model = SalesOrder
    template_name = 'inventory/shipment.html'
    context_object_name = 'sales_orders'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要

    def get_queryset(self):
        """
        Return a list of sales orders that are pending shipment.
        """
        return SalesOrder.objects.filter(status='pending').order_by('expected_shipment', 'order_number')
# 入庫処理
# (PurchaseView remains unchanged for this request)
class PurchaseView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'inventory/purchase.html'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
# 出庫処理 (Updated View)
class IssueView(LoginRequiredMixin, generic.View): # Changed from TemplateView
    """
    Displays a list of pending sales orders for issuing.
    The actual issue operation is handled by an API endpoint triggered from the frontend.
    """
    template_name = 'inventory/issue.html'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要

    def get(self, request, *args, **kwargs):
        pending_orders = SalesOrder.objects.filter(status='pending').order_by('expected_shipment', 'order_number')
        context = {
            'pending_orders': pending_orders,
        }
        return render(request, self.template_name, context)
