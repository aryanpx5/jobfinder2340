from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Login / Logout
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Redirects to login

    # Register
    path('register/', views.register_view, name='register'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
