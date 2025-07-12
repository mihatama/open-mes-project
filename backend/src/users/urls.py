# users/urls.py
from django.urls import path, reverse_lazy
from .views import views as general_views # UserSettingsView がある views.py
from .views import login, logout # login, logout ビューもインポート
from django.contrib.auth import views as auth_views  # 追記：認証ビューをインポート

app_name = 'users'

urlpatterns = [
    path('settings/', general_views.UserSettingsView.as_view(), name='users_settings'),
    path('admin/users/', general_views.AdminUserManagementView.as_view(), name='admin_user_management'), # 追加
    path('admin/users/create/', general_views.AdminUserCreateView.as_view(), name='admin_user_create'), # 追加
    path('admin/users/<uuid:pk>/edit/', general_views.AdminUserUpdateView.as_view(), name='admin_user_edit'), # 追加
    path('login/', login.CustomLoginView.as_view(), name='login'),
    path('logout/', logout.CustomLogoutView.as_view(), name='logout'),
        # --- Django標準のパスワード変更ビューのURLを追加 ---
    path('password_change/',
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change_form.html', # 使用するテンプレートを指定
             success_url=reverse_lazy('users:password_change_done') # 変更成功後のリダイレクト先
         ),
         name='password_change'), # ミドルウェアで指定した名前と同じにする
    path('password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html' # 使用するテンプレートを指定
         ),
         name='password_change_done'),
    # --- ここまで ---
]