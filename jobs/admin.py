from django.contrib import admin
from .models import JobSeekerProfile, JobPosting
from .models import Message

@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'profile_visible', 'created_at']
    list_filter = ['profile_visible', 'show_email', 'created_at']

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'location', 'is_remote', 'status', 'created_at']
    list_filter = ['status', 'is_remote', 'visa_sponsorship', 'created_at']
    search_fields = ['title', 'description', 'location', 'recruiter__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('recruiter', 'title', 'description', 'required_skills', 'location', 'salary_min', 'salary_max', 'is_remote', 'visa_sponsorship')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'moderation_status' in form.changed_data:
            obj.moderated_by = request.user
            from django.utils import timezone
            obj.moderated_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'recipient', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'body', 'sender__username', 'recipient__username']