from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin  # 追加
from rest_framework.authtoken.models import Token
from users.forms import UserProfileForm, CustomPasswordChangeForm, AdminUserCreationForm, AdminUserChangeForm # 作成したフォームをインポート
from django.contrib.auth import get_user_model, update_session_auth_hash # update_session_auth_hash をインポート

CustomUser = get_user_model()

# Create your views here.
class UserSettingsView(LoginRequiredMixin, generic.View): # generic.View を継承
    template_name = 'users/settings.html'
    profile_form_class = UserProfileForm
    password_change_form_class = CustomPasswordChangeForm # カスタムパスワード変更フォームを使用

    def get_user_token(self, user):
        try:
            token = Token.objects.get(user=user)
            return token.key
        except Token.DoesNotExist:
            # トークンが存在しない場合、シグナルで作成されるはずだが、念のためここで作成も試みる
            token, created = Token.objects.get_or_create(user=user)
            return token.key


    def get(self, request, *args, **kwargs):
        profile_form = self.profile_form_class(instance=request.user)
        password_change_form = self.password_change_form_class(user=request.user)
        api_token = self.get_user_token(request.user)

        context = {
            'page_title': 'ユーザー設定',
            'profile_form': profile_form,
            'password_change_form': password_change_form,
            'api_token': api_token,
            'password_change_form_has_errors': request.session.pop('password_change_form_has_errors', False) # エラーフラグをセッションから取得・削除
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = self.profile_form_class(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'プロフィール情報が更新されました。')
            else:
                messages.error(request, 'プロフィールの更新に失敗しました。入力内容を確認してください。')
            # フォーム処理後は常にリダイレクトしてGETリクエストを生成
            return redirect('users:users_settings')

        elif form_type == 'api_token':
            if 'regenerate_token' in request.POST:
                Token.objects.filter(user=request.user).delete()
                # get_user_token は呼び出されるとトークンがなければ作成するので、ここで再取得するだけでよい
                self.get_user_token(request.user)
                messages.success(request, f'APIトークンが再生成されました。')
            return redirect('users:users_settings')
        
        elif form_type == 'password_change':
            password_change_form = self.password_change_form_class(user=request.user, data=request.POST)
            if password_change_form.is_valid():
                user = password_change_form.save()
                update_session_auth_hash(request, user)  # パスワード変更後にセッションを更新
                messages.success(request, 'パスワードが正常に変更されました。')
                return redirect('users:users_settings')
            else:
                messages.error(request, 'パスワードの変更に失敗しました。入力内容を確認してください。')
                # エラーがあったことをセッションに保存し、リダイレクト後にJSでモーダルを開く
                request.session['password_change_form_has_errors'] = True
                # エラーのあるフォームデータ自体はリダイレクトで失われるため、
                # GET側でエラーフラグに基づいて空のフォームを再度表示し、エラーメッセージはmessagesフレームワークで表示する。
                # より詳細なエラーフィールドをモーダル内に表示したい場合は、renderアプローチかAjaxが必要。
                return redirect('users:users_settings')

        # 不明なform_typeやPOST内容の場合は、単にリダイレクト
        return redirect('users:users_settings')

class AdminUserManagementView(LoginRequiredMixin, UserPassesTestMixin, generic.TemplateView):
    template_name = 'users/admin_user_management.html'

    def test_func(self):
        # 管理者権限を持つユーザーのみアクセスを許可
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, '管理者権限が必要です。')
        return redirect('main') # 例: トップページへリダイレクト

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ユーザー管理'
        users = CustomUser.objects.all()  # すべてのユーザーを取得
        context['users'] = users
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

class AdminUserCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = CustomUser
    form_class = AdminUserCreationForm
    template_name = 'users/admin_user_create.html'
    success_url = reverse_lazy('users:admin_user_management')

    def test_func(self):
        # 管理者権限を持つユーザーのみアクセスを許可
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, '管理者権限が必要です。')
        return redirect('main')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '新規ユーザー作成'
        return context

    def form_valid(self, form):
        # フォームが有効な場合にメッセージを追加
        messages.success(self.request, f'ユーザー "{form.cleaned_data["custom_id"]}" が正常に作成されました。')
        return super().form_valid(form)

class AdminUserUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = CustomUser
    form_class = AdminUserChangeForm
    template_name = 'users/admin_user_edit.html'
    success_url = reverse_lazy('users:admin_user_management')
    pk_url_kwarg = 'pk' # URLからプライマリキーを取得するためのキーワード

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, '管理者権限が必要です。')
        return redirect('main')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'ユーザー編集: {self.object.custom_id}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'ユーザー "{self.object.custom_id}" の情報が正常に更新されました。')
        return super().form_valid(form)
