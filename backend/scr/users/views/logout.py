from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, HttpResponseRedirect
from django.contrib.auth import logout
from django.utils.http import url_has_allowed_host_and_scheme

class CustomLogoutView(LogoutView):
    """
    カスタムログアウトビュー。
    デスクトップからの場合はログアウト後に完了ページを表示し、
    'next' パラメータが指定された場合 (モバイルなど) はそのURLにリダイレクトします。
    """
    template_name = 'users/logout.html' # ログアウト完了画面のテンプレート

    def get_context_data(self, **kwargs):
        """
        テンプレートに渡すコンテキストデータを追加
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ログアウト'  # ページタイトルを追加
        return context

    def get(self, request, *args, **kwargs):
        """
        GETリクエストで直接アクセスされた場合は、メインページにリダイレクトします。
        ログアウトはPOSTリクエストでのみ実行されます。
        """
        return redirect('main')

    def post(self, request, *args, **kwargs):
        """
        POSTリクエストでログアウトを実行します。
        'next' パラメータがあればリダイレクトし、なければ完了ページを表示します。
        """
        logout(request)
        next_page = request.POST.get('next', request.GET.get('next'))
        if next_page and url_has_allowed_host_and_scheme(
            url=next_page,
            allowed_hosts=request.get_host(),
            require_https=request.is_secure(),
        ):
            return HttpResponseRedirect(next_page)
        # 'next' がない場合や安全でない場合は、完了ページをレンダリング
        return super().get(request, *args, **kwargs)
