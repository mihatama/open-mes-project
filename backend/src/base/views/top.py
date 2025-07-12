from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

class TopView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'top.html'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL を使用するため通常は不要

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
