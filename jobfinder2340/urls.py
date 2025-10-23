from django.contrib import admin
from django.urls import path, include
from accounts.views import logout_view, dashboard_view, register_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),  # <-- fixed logout
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('accounts/', include('accounts.urls')),  # Include accounts URLs
    path('jobs/', include('jobs.urls')),  # Assuming you have jobs/urls.py
    path('', auth_views.LoginView.as_view(template_name='accounts/login.html')),  # root goes to login
]
