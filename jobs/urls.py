from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create_profile/', views.create_profile_view, name='create_profile'),
    path('view_profile/', views.view_profile_view, name='view_profile'),
    path('recommendations/', views.recommended_jobs_view, name='recommendations'),
    path('job_search/', views.job_search_view, name='job_search'),
    path('job_map/', views.job_map_view, name='job_map'),
    path('api/job_map/', views.job_map_api, name='job_map_api'),
    path('postings/<int:pk>/apply/', views.apply_to_posting_view, name='apply_to_posting'),

    # Recruiter routes
    path('my_postings/', views.my_postings_view, name='my_postings'),
    path('postings/create/', views.create_posting_view, name='create_posting'),
    path('postings/<int:pk>/edit/', views.edit_posting_view, name='edit_posting'),

    # Applicants and applications
    path('postings/<int:pk>/applicants/', views.posting_applicants_view, name='posting_applicants'),
    path('postings/<int:posting_pk>/applicants/<int:applicant_pk>/conversation/', views.conversation_view, name='conversation_view'),
    path('applications/<int:application_id>/update-status/', views.update_application_status_view, name='update_application_status'),
    
    # Job seeker applications tracking
    path('my_applications/', views.my_applications_view, name='my_applications'),

    # Messaging
    path('messages/inbox/', views.inbox_view, name='inbox'),
    path('messages/compose/', views.compose_message_view, name='compose_message'),
    path('messages/<int:pk>/', views.message_detail_view, name='message_detail'),

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
