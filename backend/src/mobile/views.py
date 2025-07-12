from django.shortcuts import render
from django.views import generic
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

# Create your views here.

class MobileIndexView(generic.TemplateView):
    template_name = 'mobile/mobile_index.html'

class MobileLoginView(auth_views.LoginView):
    template_name = 'mobile/login.html'

    def get_success_url(self):
        # next パラメータがあればそちらを優先
        # なければ mobile:index へ
        url = self.get_redirect_url()
        return url or reverse_lazy('mobile:index')

class MobileGoodsReceiptView(generic.TemplateView):
    template_name = 'mobile/goods_receipt.html'

class MobileGoodsIssueView(generic.TemplateView):
    template_name = 'mobile/goods_issue.html'

class MobileLocationTransferView(generic.TemplateView):
    template_name = 'mobile/location_transfer.html'
