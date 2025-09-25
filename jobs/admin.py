from django.contrib import admin
from .models import JobSeekerProfile, JobPosting

@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'profile_visible', 'created_at']
    list_filter = ['profile_visible', 'show_email', 'created_at']

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'location', 'is_remote', 'status', 'created_at']
    list_filter = ['status', 'is_remote', 'visa_sponsorship', 'created_at']
    search_fields = ['title', 'description', 'location']