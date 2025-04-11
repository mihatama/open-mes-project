from django.urls import path
from .views import dashboard_control, data_stream

urlpatterns = [
    path('dashboard/', dashboard_control, name='dashboard_control'),
    path('dashboard/stream/', data_stream, name='data_stream'),
]
