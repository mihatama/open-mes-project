"""
URL configuration for base project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from .views import top
from inventory.views import menu as inventory_menu
from users.views import login, logout
from django.contrib.auth import views as auth_views  # 追記：認証ビューをインポート

app_name = "base"



urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理サイトへのURL
    path('mcp/', include('mcp.urls')),
    path('', top.TopView.as_view(), name="main"),  # メインページへのURL
    path('inventory/menu/', inventory_menu.InventoryMenuView.as_view(), name="inventory_menu"),  # 在庫管理メニューページへのURL
    path('inventory/inquiry/', inventory_menu.InquiryView.as_view(), name="inventory_inquiry"),  # 在庫照会ページへのURL (在庫照会)
    path('inventory/schedule/', inventory_menu.ScheduleView.as_view(), name="inventory_schedule"),  # 入庫予定ページへのURL (入庫予定)
    path('inventory/shipment/', inventory_menu.ShipmentView.as_view(), name="inventory_shipment"),  # 出庫予定ページへのURL (出庫予定)
    path('inventory/purchase/', inventory_menu.PurchaseView.as_view(), name="inventory_purchase"),  # 入庫処理ページへのURL (入庫処置)
    path('inventory/issue/', inventory_menu.IssueView.as_view(), name="inventory_issue"),  # 出庫処理ページへのURL (出庫処理)
    path('users/login/', login.CustomLoginView.as_view(), name='users_login'),  # 追記：ログインURL
    path('users/logout/', logout.CustomLogoutView.as_view(), name='users_logout'),  # 追記：ログアウトURL
    path("__debug__/", include("debug_toolbar.urls")),
]
