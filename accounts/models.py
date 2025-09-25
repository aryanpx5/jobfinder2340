from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Administrator'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"