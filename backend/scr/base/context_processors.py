# version数値渡し用
from django.conf import settings

def my_settings(request):
    return {
        'VERSION': settings.VERSION,
    }