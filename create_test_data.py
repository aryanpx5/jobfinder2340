#!/usr/bin/env python3
"""
Script to create test data for the job finder application
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/ajaydesai/jobfinder2340')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder2340.settings')
django.setup()

from accounts.models import CustomUser
from jobs.models import JobPosting

def create_test_data():
    print("Creating test data...")
    
    # Create test recruiter
    recruiter, created = CustomUser.objects.get_or_create(
        username='test_recruiter',
        defaults={
            'email': 'recruiter@example.com',
            'user_type': 'recruiter',
            'first_name': 'Test',
            'last_name': 'Recruiter'
        }
    )
    if created:
        recruiter.set_password('test123')
        recruiter.save()
        print("Created test recruiter")
    
    # Create test job postings with different moderation statuses
    job_data = [
        {
            'title': 'Senior Python Developer',
            'description': 'We are looking for a senior Python developer with Django experience.',
            'required_skills': 'Python, Django, PostgreSQL, REST APIs',
            'location': 'San Francisco, CA',
            'salary_min': 120000,
            'salary_max': 150000,
            'is_remote': True,
            'visa_sponsorship': True,
            'status': 'active',
            'moderation_status': 'approved'
        },
        {
            'title': 'Frontend React Developer',
            'description': 'Join our team as a React developer!',
            'required_skills': 'React, JavaScript, HTML, CSS',
            'location': 'New York, NY',
            'salary_min': 80000,
            'salary_max': 110000,
            'is_remote': False,
            'visa_sponsorship': False,
            'status': 'pending',
            'moderation_status': 'pending'
        },
        {
            'title': 'SPAM JOB POSTING',
            'description': 'This is clearly spam content that should be rejected.',
            'required_skills': 'Nothing',
            'location': 'Nowhere',
            'salary_min': 1000000,
            'salary_max': 2000000,
            'is_remote': True,
            'visa_sponsorship': True,
            'status': 'inactive',
            'moderation_status': 'rejected',
            'moderation_notes': 'Rejected for spam content'
        },
        {
            'title': 'Data Scientist Position',
            'description': 'Looking for a data scientist with machine learning experience.',
            'required_skills': 'Python, Machine Learning, SQL, Statistics',
            'location': 'Seattle, WA',
            'salary_min': 90000,
            'salary_max': 130000,
            'is_remote': True,
            'visa_sponsorship': True,
            'status': 'pending',
            'moderation_status': 'pending'
        }
    ]
    
    for i, job_info in enumerate(job_data, 1):
        job, created = JobPosting.objects.get_or_create(
            title=job_info['title'],
            recruiter=recruiter,
            defaults=job_info
        )
        if created:
            print(f"Created job posting: {job_info['title']}")
    
    print(f"\nTest data created successfully!")
    print(f"- Recruiter: test_recruiter (password: test123)")
    print(f"- Admin: admin (password: admin123)")
    print(f"- Total job postings: {JobPosting.objects.count()}")
    print(f"- Pending moderation: {JobPosting.objects.filter(moderation_status='pending').count()}")

if __name__ == '__main__':
    create_test_data()
