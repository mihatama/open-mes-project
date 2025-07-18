from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import rest_views

app_name = 'machine_api'

router = DefaultRouter()
router.register(r'machines', rest_views.MachineViewSet, basename='machine')

urlpatterns = [
    path('', include(router.urls)),
]