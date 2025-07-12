from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

class CustomLogoutView(LogoutView):
    """
    カスタムログアウトビュー
    """
    next_page = reverse_lazy('main')  # ログアウト後のリダイレクト先をトップページ('main')に変更
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
        GETリクエストを処理する
        """
        return render(request, self.template_name, self.get_context_data())
