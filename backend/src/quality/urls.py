from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    path('menu/', views.QualityMenuView.as_view(), name="menu"), # Changed name for consistency
    path('process_inspection/', views.ProcessInspectionView.as_view(), name="process_inspection"),
    path('acceptance_inspection/', views.AcceptanceInspectionView.as_view(), name="acceptance_inspection"),

    # Inspection Item Master URLs
    path('master_creation/', views.InspectionItemMasterView.as_view(), name='master_creation'),
    path('master_creation/list/', views.inspection_item_create, name='inspection_item_list'), # Add this line
    path('master_creation/create/', views.inspection_item_create, name='inspection_item_create'),
    path('master_creation/update/<uuid:pk>/', views.inspection_item_update, name='inspection_item_update'),
    path('master_creation/delete/<uuid:pk>/', views.inspection_item_delete, name='inspection_item_delete'),
    path('api/inspection_item_form_data/<uuid:item_pk>/', views.get_inspection_item_form_data, name='get_inspection_item_form_data'),
    path('api/record_inspection_result/<uuid:item_pk>/', views.record_inspection_result_view, name='record_inspection_result'),
]