from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin  # 追加
from rest_framework.authtoken.models import Token
from users.forms import UserProfileForm, CustomPasswordChangeForm, AdminUserCreationForm, AdminUserChangeForm # 作成したフォームをインポート
from django.contrib.auth import get_user_model, update_session_auth_hash # update_session_auth_hash をインポート
from django.http import JsonResponse
import json

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
        # ReactフロントエンドからのAPIリクエストかどうかを判定
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            user = request.user
            data = {
                'username': user.username,
                'email': user.email,
                'custom_id': user.custom_id,
                'api_token': self.get_user_token(user),
            }
            return JsonResponse(data)

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
        is_api_request = 'application/json' in request.META.get('HTTP_ACCEPT', '')
        
        try:
            if is_api_request and request.body:
                data = json.loads(request.body)
            else:
                data = request.POST
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        form_type = data.get('form_type')

        if form_type == 'profile':
            form = self.profile_form_class(data, instance=request.user)
            if form.is_valid():
                form.save()
                if is_api_request:
                    return JsonResponse({'message': 'プロフィール情報が更新されました。'})
                messages.success(request, 'プロフィール情報が更新されました。')
                return redirect('users:users_settings')
            else:
                if is_api_request:
                    return JsonResponse(form.errors, status=400)
                messages.error(request, 'プロフィールの更新に失敗しました。入力内容を確認してください。')
                # Note: Redirect loses form error details. For template-based forms, rendering the context is better.
                return redirect('users:users_settings')

        elif form_type == 'api_token':
            if data.get('regenerate_token'):
                Token.objects.filter(user=request.user).delete()
                new_token = self.get_user_token(request.user)
                if is_api_request:
                    return JsonResponse({'message': 'APIトークンが再生成されました。', 'api_token': new_token})
                messages.success(request, 'APIトークンが再生成されました。')
                return redirect('users:users_settings')
        
        elif form_type == 'password_change':
            form = self.password_change_form_class(user=request.user, data=data)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # パスワード変更後にセッションを更新
                if is_api_request:
                    return JsonResponse({'message': 'パスワードが正常に変更されました。'})
                messages.success(request, 'パスワードが正常に変更されました。')
                return redirect('users:users_settings')
            else:
                if is_api_request:
                    return JsonResponse(form.errors, status=400)
                messages.error(request, 'パスワードの変更に失敗しました。入力内容を確認してください。')
                request.session['password_change_form_has_errors'] = True
                return redirect('users:users_settings')

        if is_api_request:
            return JsonResponse({'error': 'Invalid form_type or action'}, status=400)
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
