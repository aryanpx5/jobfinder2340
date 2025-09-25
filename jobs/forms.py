from django import forms
from .models import JobSeekerProfile

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['headline', 'skills', 'education', 'work_experience', 'links']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Software Developer'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Python, Django, React, JavaScript'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., BS Computer Science, Georgia Tech, 2024'}),
            'work_experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'e.g., Software Intern at Google (Summer 2023)'}),
            'links': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'LinkedIn: linkedin.com/in/yourname\nGitHub: github.com/yourname'}),
        }