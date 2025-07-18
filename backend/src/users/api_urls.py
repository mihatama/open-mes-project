from django.urls import path, include
# `users/views/rest.py` にビューを定義することを想定
from .views import rest as rest_views

app_name = 'users_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('login/', rest_views.CustomObtainAuthToken.as_view(), name='api_login'),
    path('logout/', rest_views.APILogoutView.as_view(), name='api_logout'),
    path('session/', rest_views.get_session_info, name='api_session_info'),
    # API endpoints for user settings
    path('settings/', rest_views.UserSettingsDetailView.as_view(), name='api_user_settings'),
    path('settings/password/', rest_views.UserPasswordChangeView.as_view(), name='api_user_password_change'),
    path('settings/token/', rest_views.APITokenView.as_view(), name='api_user_token'),
    # Manually define the ViewSet URLs to avoid the extra 'users/' prefix from the router
    path('', rest_views.UserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='user-list'),
    path('<uuid:pk>/', rest_views.UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='user-detail'),
]