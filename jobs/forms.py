from django import forms
from .models import JobSeekerProfile
from .models import JobPosting
from .models import Message
from django.contrib.auth import get_user_model

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


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        # recruiter will be set in the view
        fields = [
            'title', 'description', 'required_skills', 'location',
            'salary_min', 'salary_max', 'is_remote', 'visa_sponsorship', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'required_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_remote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visa_sponsorship': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'profile_visible', 'show_email', 'show_phone', 'show_skills', 
            'show_education', 'show_work_experience', 'show_links', 'allow_contact'
        ]
        widgets = {
            'profile_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_skills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_education': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_work_experience': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

    def __init__(self, *args, sender=None, **kwargs):
        """
        Optionally accept a `sender` user to restrict the recipient queryset.
        - If sender is a recruiter, recipients are job seekers.
        - If sender is a job seeker, recipients are recruiters.
        If sender is None or user_type cannot be determined, fall back to no restriction.
        """
        super().__init__(*args, **kwargs)
        User = get_user_model()
        try:
            if sender is not None:
                if getattr(sender, 'user_type', None) == 'recruiter':
                    self.fields['recipient'].queryset = User.objects.filter(user_type='job_seeker')
                elif getattr(sender, 'user_type', None) == 'job_seeker':
                    self.fields['recipient'].queryset = User.objects.filter(user_type='recruiter')
                else:
                    # Unknown sender type -> no filtering
                    pass
            else:
                # Default behavior: show job seekers (preserves prior behavior)
                self.fields['recipient'].queryset = User.objects.filter(user_type='job_seeker')
        except Exception:
            # Safeguard during migrations or missing user_type attr
            pass