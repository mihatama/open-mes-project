from django.urls import path
from .views import api

app_name = 'base_api'

urlpatterns = [
    path('info/', api.AppInfoView.as_view(), name='app-info'),
]