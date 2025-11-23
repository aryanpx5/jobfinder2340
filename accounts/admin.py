from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_staff', 'is_active']
    list_editable = ['user_type']
    list_filter = ['user_type', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type',)}),
    )

    actions = ['make_job_seeker', 'make_recruiter', 'make_admin', 'activate_users', 'deactivate_users']

    def make_job_seeker(self, request, queryset):
        queryset.update(user_type='job_seeker')
        self.message_user(request, f"Updated {queryset.count()} users to Job Seeker")
    make_job_seeker.short_description = "Set selected users as Job Seekers"

    def make_recruiter(self, request, queryset):
        queryset.update(user_type='recruiter')
        self.message_user(request, f"Updated {queryset.count()} users to Recruiter")
    make_recruiter.short_description = "Set selected users as Recruiters"

    def make_admin(self, request, queryset):
        queryset.update(user_type='admin', is_staff=True, is_superuser=False)
        self.message_user(request, f"Updated {queryset.count()} users to Administrator (staff)")
    make_admin.short_description = "Set selected users as Administrators (staff)"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} users")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} users")
    deactivate_users.short_description = "Deactivate selected users"

admin.site.register(CustomUser, CustomUserAdmin)