from django.urls import path
from . import views

app_name = 'mobile'
urlpatterns = [
    path('', views.MobileIndexView.as_view(), name='index'),
    path('login/', views.MobileLoginView.as_view(), name='login'), # モバイル用ログインページのURL
    path('goods-receipt/', views.MobileGoodsReceiptView.as_view(), name='goods_receipt'),
    path('goods-issue/', views.MobileGoodsIssueView.as_view(), name='goods_issue'),
    path('location-transfer/', views.MobileLocationTransferView.as_view(), name='location_transfer'),
]