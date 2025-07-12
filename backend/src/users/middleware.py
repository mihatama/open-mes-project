# users/middleware.py

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages # メッセージフレームワークをインポート
from django.conf import settings # settings をインポート

class PasswordExpirationMiddleware(MiddlewareMixin):
    def _should_check_password_expiration(self, request):
        """
        Determines if password expiration check should be performed for the current request.
        """
        if not request.user.is_authenticated:
            return False

        # パスワード変更関連のURLとログアウトURLは除外リストに追加
        # 無限リダイレクトループを防ぐため
        # These names come from your urls.py (e.g., name='password_change')
        exempt_url_names = [
            'password_change',
            'password_change_done',
            'users_logout',
            'users_login', # Exempt the login page itself as well
            # 必要であれば管理サイトのURLなども追加
            # 'admin:login',
            # 'admin:logout',
        ]
        # settings.py で除外URL名をカスタマイズ可能にする場合
        # exempt_url_names.extend(getattr(settings, 'PASSWORD_EXPIRATION_EXEMPT_URL_NAMES', []))

        # request.resolver_match is available in process_view
        if request.resolver_match and request.resolver_match.url_name in exempt_url_names:
            return False

        # Example: Exempt all admin paths
        # admin_url_prefix = getattr(settings, 'ADMIN_URL_PREFIX', '/admin/') # Assuming you might have such a setting
        # if request.path_info.startswith(reverse_lazy('admin:index')): # More robust way to get admin prefix if needed
        #     return False

        return True

    def process_view(self, request, view_func, view_args, view_kwargs):
        # This method is called after URL resolution, so request.resolver_match is available.

        if not self._should_check_password_expiration(request):
            return None # Continue to the view without further checks

        # is_password_expired プロパティが存在し、True かどうかをチェック
        # スーパーユーザーは有効期限チェックをスキップするオプション (必要に応じて)
        # if request.user.is_superuser:
        #     return None
        if hasattr(request.user, 'is_password_expired') and request.user.is_password_expired:
            message_text = 'パスワードの有効期限が切れています。新しいパスワードを設定してください。'
            # Avoid adding duplicate messages if any mechanism causes this to run multiple times for the same logical state
            if not any(m.message == message_text and m.level == messages.WARNING for m in messages.get_messages(request)):
                messages.warning(request, message_text)

            # パスワード変更ページにリダイレクト
            # Since exempt pages are handled by _should_check_password_expiration,
            # we know we are not already on 'password_change' if we reach here.
            return redirect(reverse_lazy('password_change')) # reverse_lazy を使用

        # 上記以外の場合は通常通り処理を続行
        return None
