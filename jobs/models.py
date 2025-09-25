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
    profile_visible = models.BooleanField(default=True)
    show_email = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class JobPosting(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('removed', 'Removed'),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.recruiter.username}"

    class Meta:
        ordering = ['-created_at']