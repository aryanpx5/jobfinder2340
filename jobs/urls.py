from django.urls import path
from . import views

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

    # Optionally, make dashboard the root
    path('', views.dashboard_view, name='home'),  
]
