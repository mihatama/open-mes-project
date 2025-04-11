from django.urls import path
from .views import dashboard_control

urlpatterns = [
    path('dashboard/', dashboard_control, name='dashboard_control'),
]
