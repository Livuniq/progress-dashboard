from django.urls import path, re_path
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.main_app_index, name='index'),
    path('eel.js', views.eel_js, name='eel_js'),
    path('api/call/', views.api_call, name='api_call'),
    path('upload-data/', views.upload_data_file, name='upload_data'),
    path('upload-company-template/', views.upload_company_template, name='upload_company_template'),
    path('schedule-time/', views.get_schedule_time_view, name='schedule_time'),
    path('download-output/', views.download_output_file, name='download_output'),
    re_path(r'^(?P<path>.*)$', views.serve_web_html_file, name='static_files'),
]
