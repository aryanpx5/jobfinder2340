from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create_profile/', views.create_profile_view, name='create_profile'),
    path('view_profile/', views.view_profile_view, name='view_profile'),
    path('job_search/', views.job_search_view, name='job_search'),

    # Recruiter routes
    path('my_postings/', views.my_postings_view, name='my_postings'),
    path('postings/create/', views.create_posting_view, name='create_posting'),
    path('postings/<int:pk>/edit/', views.edit_posting_view, name='edit_posting'),

    # Privacy settings for job seekers
    path('privacy_settings/', views.privacy_settings_view, name='privacy_settings'),

    # Admin routes
    path('admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/moderation/', admin_views.moderation_queue_view, name='moderation_queue'),
    path('admin/moderate/<int:job_id>/', admin_views.moderate_job_view, name='moderate_job'),
    path('admin/export/', admin_views.export_data_view, name='export_data'),
    path('admin/bulk-moderation/', admin_views.bulk_moderation_view, name='bulk_moderation'),

    # Optionally, make dashboard the root
    path('', views.dashboard_view, name='home'),  
]
