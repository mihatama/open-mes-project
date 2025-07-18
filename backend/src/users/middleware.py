# users/middleware.py

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class PasswordExpirationMiddleware(MiddlewareMixin):
    def _should_check_password_expiration(self, request):
        """
        Determines if password expiration check should be performed for the current request.
        """
        if not request.user.is_authenticated:
            return False

        # request.resolver_matchはURL解決後に利用可能 (process_view内)
        if not hasattr(request, 'resolver_match') or not request.resolver_match:
            return True  # 判定できないため、デフォルトでチェック対象とする

        # 特定のビューを完全修飾されたビュー名 (namespace:url_name) で除外する。
        # この方法はパスやURL名のみをチェックするより堅牢です。
        exempt_view_names = {
            # 認証とパスワード管理用のAPIエンドポイント
            'users_api:api_login',
            'users_api:api_logout',
            'users_api:api_user_password_change',
            'users_api:api_session_info',  # フロントエンドが常にセッション状態を確認できるように除外
            # Django管理サイトのログアウト
            'admin:logout',
        }

        if request.resolver_match.view_name in exempt_view_names:
            return False

        # 他のすべての管理サイトのパスを除外する。これは広範だが安全なルールです。
        if request.resolver_match.app_name == 'admin':
            return False

        return True

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self._should_check_password_expiration(request):
            return None

        if hasattr(request.user, 'is_password_expired') and request.user.is_password_expired:
            # パスワードの有効期限が切れています。除外されていないリクエストに対してJSONレスポンスを返します。
            # これにより、リダイレクトの責務をフロントエンドクライアントに委任します。
            return JsonResponse({
                'code': 'password_expired',
                'detail': 'パスワードの有効期限が切れています。新しいパスワードを設定してください。'
            }, status=403)  # 403 Forbidden はこの場合に適切です。
        return None
