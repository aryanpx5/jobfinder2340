from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create_profile/', views.create_profile_view, name='create_profile'),
    path('view_profile/', views.view_profile_view, name='view_profile'),
    path('job_search/', views.job_search_view, name='job_search'),

    # Optionally, make dashboard the root
    path('', views.dashboard_view, name='home'),  
]
