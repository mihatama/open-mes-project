from django.urls import path
from . import views # DataImportView, MasterCreationView のため

app_name = 'master'

urlpatterns = [
    path('data-import/', views.DataImportView.as_view(), name='data_import'),
    path('master-creation/', views.MasterCreationView.as_view(), name='master_creation'), # Note: This view seems separate
]