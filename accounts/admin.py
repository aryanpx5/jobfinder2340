from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)