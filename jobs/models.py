from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255, blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.TextField(blank=True, help_text="LinkedIn, GitHub, Portfolio URLs")
    
    # Privacy Settings (Story #5)
    profile_visible = models.BooleanField(default=True, help_text="Make your profile visible to recruiters")
    show_email = models.BooleanField(default=True, help_text="Show your email address to recruiters")
    show_phone = models.BooleanField(default=False, help_text="Show your phone number to recruiters")
    show_skills = models.BooleanField(default=True, help_text="Show your skills to recruiters")
    show_education = models.BooleanField(default=True, help_text="Show your education details to recruiters")
    show_work_experience = models.BooleanField(default=True, help_text="Show your work experience to recruiters")
    show_links = models.BooleanField(default=True, help_text="Show your portfolio/social links to recruiters")
    allow_contact = models.BooleanField(default=True, help_text="Allow recruiters to contact you directly")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class JobPosting(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('removed', 'Removed'),
        ('rejected', 'Rejected'),
    )
    
    MODERATION_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    )
    
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated skills")
    location = models.CharField(max_length=255)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    is_remote = models.BooleanField(default=False)
    visa_sponsorship = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderation_status = models.CharField(max_length=20, choices=MODERATION_STATUS_CHOICES, default='pending')
    moderation_notes = models.TextField(blank=True, help_text="Admin notes for moderation")
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_posts')
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.recruiter.username}"

    class Meta:
        ordering = ['-created_at']