from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobSeekerProfile, JobPosting
from .forms import JobSeekerProfileForm, PrivacySettingsForm
from .forms import JobPostingForm
from django.http import HttpResponseForbidden


def recruiter_required(view_func):
    """Decorator to allow only users with user_type 'recruiter'"""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'recruiter':
            messages.error(request, 'Only recruiters can access that page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped

# -------------------------
# DASHBOARD VIEW
# -------------------------
@login_required
def dashboard_view(request):
    """
    Renders the dashboard page. The template is in templates/accounts/dashboard.html
    """
    return render(request, 'accounts/dashboard.html')


# -------------------------
# CREATE PROFILE VIEW
# -------------------------
@login_required
def create_profile_view(request):
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can create profiles.')
        return redirect('dashboard')
    
    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
        if request.method == 'POST':
            form = JobSeekerProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('view_profile')
        else:
            form = JobSeekerProfileForm(instance=profile)
    except JobSeekerProfile.DoesNotExist:
        if request.method == 'POST':
            form = JobSeekerProfileForm(request.POST)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                messages.success(request, 'Profile created successfully!')
                return redirect('view_profile')
        else:
            form = JobSeekerProfileForm()
    
    return render(request, 'jobs/create_profile.html', {'form': form})


# -------------------------
# VIEW PROFILE VIEW
# -------------------------
@login_required
def view_profile_view(request):
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers have profiles.')
        return redirect('dashboard')
    
    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        messages.info(request, 'Please create your profile first.')
        return redirect('create_profile')
    
    return render(request, 'jobs/view_profile.html', {'profile': profile})


# -------------------------
# JOB SEARCH VIEW
# -------------------------
def job_search_view(request):
    jobs = JobPosting.objects.filter(status='active', moderation_status='approved')
    
    # Apply filters from GET parameters
    title = request.GET.get('title', '')
    location = request.GET.get('location', '')
    skills = request.GET.get('skills', '')
    salary_min = request.GET.get('salary_min', '')
    is_remote = request.GET.get('is_remote', '')
    visa_sponsorship = request.GET.get('visa_sponsorship', '')
    
    if title:
        jobs = jobs.filter(title__icontains=title)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if skills:
        jobs = jobs.filter(required_skills__icontains=skills)
    if salary_min:
        try:
            jobs = jobs.filter(salary_min__gte=int(salary_min))
        except ValueError:
            pass
    if is_remote == 'true':
        jobs = jobs.filter(is_remote=True)
    if visa_sponsorship == 'true':
        jobs = jobs.filter(visa_sponsorship=True)
    
    context = {
        'jobs': jobs,
        'search_params': request.GET,
    }
    return render(request, 'jobs/job_search.html', context)


# -------------------------
# RECRUITER: LIST OWN POSTINGS
# -------------------------
@login_required
@recruiter_required
def my_postings_view(request):
    postings = JobPosting.objects.filter(recruiter=request.user)
    return render(request, 'jobs/my_postings.html', {'postings': postings})


# -------------------------
# RECRUITER: CREATE POSTING
# -------------------------
@login_required
@recruiter_required
def create_posting_view(request):
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            posting = form.save(commit=False)
            posting.recruiter = request.user
            # Newly created postings should be visible to job seekers by default.
            # Set status and moderation_status to show up in the public search.
            try:
                posting.status = 'active'
            except Exception:
                pass
            try:
                posting.moderation_status = 'approved'
            except Exception:
                pass
            posting.save()
            messages.success(request, 'Job posting created successfully.')
            return redirect('my_postings')
    else:
        form = JobPostingForm()
    return render(request, 'jobs/create_posting.html', {'form': form})


# -------------------------
# RECRUITER: EDIT POSTING
# -------------------------
@login_required
@recruiter_required
def edit_posting_view(request, pk):
    posting = get_object_or_404(JobPosting, pk=pk)
    if posting.recruiter != request.user:
        return HttpResponseForbidden('You do not have permission to edit this posting.')

    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=posting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job posting updated successfully.')
            return redirect('my_postings')
    else:
        form = JobPostingForm(instance=posting)
    return render(request, 'jobs/edit_posting.html', {'form': form, 'posting': posting})


# -------------------------
# PRIVACY SETTINGS VIEW
# -------------------------
@login_required
def privacy_settings_view(request):
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can access privacy settings.')
        return redirect('dashboard')
    
    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        messages.info(request, 'Please create your profile first before setting privacy options.')
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = PrivacySettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privacy settings updated successfully!')
            return redirect('privacy_settings')
    else:
        form = PrivacySettingsForm(instance=profile)
    
    return render(request, 'jobs/privacy_settings.html', {'form': form, 'profile': profile})
