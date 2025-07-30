"""
URL configuration for base project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views as authtoken_views  # authtoken の views をインポート

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API Endpoints
    path('api/token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),  # Token authentication endpoint

    # API URLs per app (alphabetical order)
    path('api/base/', include('base.api_urls', namespace='base_api')),
    # フロントエンドの実装に合わせて /api/v1/cars/ を追加
    path('api/v1/cars/', include('cars.api_urls', namespace='cars_api')),
    path('api/inventory/', include('inventory.api_urls', namespace='inventory_api')),
    path('api/machine/', include('machine.api_urls', namespace='machine_api')),
    path('api/master/', include('master.api_urls', namespace='master_api')),
    path('api/production/', include('production.api_urls', namespace='production_api')),
    path('api/quality/', include('quality.api_urls', namespace='quality_api')),
    path('api/users/', include('users.api_urls', namespace='users_api')),

    # Debug Toolbar
    path("__debug__/", include("debug_toolbar.urls")),
]
