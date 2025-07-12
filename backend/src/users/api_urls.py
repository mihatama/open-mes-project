from django.urls import path
# `users/views/rest.py` にビューを定義することを想定
from .views import rest as rest_views

app_name = 'users_api'

urlpatterns = [
    path('logout/', rest_views.APILogoutView.as_view(), name='api_logout'),
    path('session/', rest_views.get_session_info, name='api_session_info'),
]