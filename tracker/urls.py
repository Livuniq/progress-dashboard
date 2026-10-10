from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('item/create/', views.item_create, name='item_create'),
    path('item/<int:pk>/update/', views.item_update, name='item_update'),
    path('item/<int:pk>/json/', views.item_get_json, name='item_get_json'),
    path('item/<int:pk>/status/', views.item_quick_status, name='item_quick_status'),
    path('item/<int:pk>/priority/', views.item_toggle_priority, name='item_toggle_priority'),
    path('item/<int:pk>/inline-update/', views.item_inline_update, name='item_inline_update'),
    path('item/<int:pk>/history/', views.item_history_json, name='item_history_json'),
    path('item/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('import/excel/', views.import_excel, name='import_excel'),
    path('reset/demo/', views.reset_demo_data, name='reset_demo_data'),
    path('columns/save/', views.save_column_config, name='save_column_config'),
    path('columns/<int:pk>/delete/', views.delete_column_config, name='delete_column_config'),
    path('columns/reset/', views.reset_column_config, name='reset_column_config'),
    path('colors/save/', views.save_status_colors, name='save_status_colors'),
    path('colors/reset/', views.reset_status_colors, name='reset_status_colors'),
]
