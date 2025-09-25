from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobSeekerProfile, JobPosting
from .forms import JobSeekerProfileForm

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
    jobs = JobPosting.objects.filter(status='active')
    
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
