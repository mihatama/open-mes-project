from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render

class CustomLoginView(LoginView):
    """
    カスタムログインビュー
    """
    template_name = 'users/login.html'  # ログインフォームのテンプレート
    form_class = AuthenticationForm  # ログインフォームのクラス
    redirect_authenticated_user = True  # 認証済みユーザーがアクセスした場合、リダイレクトする
    success_url = reverse_lazy('main')  # ログイン成功時のリダイレクト先をトップページ('main')に変更

    def get_context_data(self, **kwargs):
        """
        テンプレートに渡すコンテキストデータを追加
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ログイン'  # ページタイトルを追加
        return context
    
    def form_invalid(self, form):
        """
        フォームが無効な場合の処理
        """
        return render(self.request, self.template_name, {'form': form, 'page_title': 'ログイン'})
