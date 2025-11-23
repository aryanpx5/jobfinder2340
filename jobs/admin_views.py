from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
import csv
from .models import JobPosting, JobSeekerProfile
from accounts.models import CustomUser


def admin_required(view_func):
    """Decorator to allow only users with user_type 'admin'"""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or getattr(request.user, 'user_type', None) != 'admin':
            messages.error(request, 'Only administrators can access that page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
@admin_required
def admin_dashboard_view(request):
    """Admin dashboard with moderation overview and quick stats"""
    
    # Get statistics for the dashboard
    stats = {
        'total_jobs': JobPosting.objects.count(),
        'pending_jobs': JobPosting.objects.filter(moderation_status='pending').count(),
        'active_jobs': JobPosting.objects.filter(status='active').count(),
        'rejected_jobs': JobPosting.objects.filter(moderation_status='rejected').count(),
        'total_users': CustomUser.objects.count(),
        'job_seekers': CustomUser.objects.filter(user_type='job_seeker').count(),
        'recruiters': CustomUser.objects.filter(user_type='recruiter').count(),
    }
    
    # Recent pending jobs for quick review
    recent_pending = JobPosting.objects.filter(moderation_status='pending').order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_pending': recent_pending,
    }
    
    return render(request, 'jobs/admin_dashboard.html', context)


@login_required
@admin_required
def moderation_queue_view(request):
    """View all jobs pending moderation"""
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    jobs = JobPosting.objects.all().order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        jobs = jobs.filter(moderation_status=status_filter)
    
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(recruiter__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': JobPosting.MODERATION_STATUS_CHOICES,
    }
    
    return render(request, 'jobs/moderation_queue.html', context)


@login_required
@admin_required
def moderate_job_view(request, job_id):
    """View and moderate a specific job posting"""
    
    job = get_object_or_404(JobPosting, id=job_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('moderation_notes', '')
        
        if action == 'approve':
            job.moderation_status = 'approved'
            job.status = 'active'
            messages.success(request, f'Job posting "{job.title}" has been approved.')
        elif action == 'reject':
            job.moderation_status = 'rejected'
            job.status = 'inactive'
            messages.success(request, f'Job posting "{job.title}" has been rejected.')
        elif action == 'flag':
            job.moderation_status = 'flagged'
            messages.warning(request, f'Job posting "{job.title}" has been flagged for review.')
        elif action == 'delete':
            job.delete()
            messages.success(request, f'Job posting "{job.title}" has been deleted.')
            return redirect('moderation_queue')
        
        job.moderation_notes = notes
        job.moderated_by = request.user
        job.moderated_at = timezone.now()
        job.save()
        
        return redirect('moderate_job', job_id=job.id)
    
    context = {
        'job': job,
    }
    
    return render(request, 'jobs/moderate_job.html', context)


@login_required
@admin_required
def export_data_view(request):
    """Export data as CSV for reporting purposes"""
    
    export_type = request.GET.get('type', 'jobs')
    
    if export_type == 'jobs':
        return export_jobs_csv(request)
    elif export_type == 'users':
        return export_users_csv(request)
    elif export_type == 'analytics':
        return export_analytics_csv(request)
    else:
        messages.error(request, 'Invalid export type.')
        return redirect('admin_dashboard')


def export_jobs_csv(request):
    """Export job postings data as CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="job_postings_export.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'ID', 'Title', 'Recruiter', 'Description', 'Required Skills', 'Location',
        'Salary Min', 'Salary Max', 'Is Remote', 'Visa Sponsorship', 'Status',
        'Moderation Status', 'Moderation Notes', 'Created At', 'Updated At',
        'Moderated By', 'Moderated At'
    ])
    
    # Write data
    jobs = JobPosting.objects.all().order_by('-created_at')
    for job in jobs:
        writer.writerow([
            job.id,
            job.title,
            job.recruiter.username,
            job.description,
            job.required_skills,
            job.location,
            job.salary_min,
            job.salary_max,
            job.is_remote,
            job.visa_sponsorship,
            job.get_status_display(),
            job.get_moderation_status_display(),
            job.moderation_notes,
            job.created_at,
            job.updated_at,
            job.moderated_by.username if job.moderated_by else '',
            job.moderated_at
        ])
    
    return response


def export_users_csv(request):
    """Export user data as CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'ID', 'Username', 'Email', 'First Name', 'Last Name', 'User Type',
        'Is Active', 'Is Staff', 'Is Superuser', 'Date Joined', 'Last Login'
    ])
    
    # Write data
    users = CustomUser.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.get_user_type_display(),
            user.is_active,
            user.is_staff,
            user.is_superuser,
            user.date_joined,
            user.last_login
        ])
    
    return response


def export_analytics_csv(request):
    """Export analytics data as CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_export.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Metric', 'Count', 'Percentage'
    ])
    
    # Calculate analytics
    total_jobs = JobPosting.objects.count()
    total_users = CustomUser.objects.count()
    
    # Job statistics
    job_stats = JobPosting.objects.values('status').annotate(count=Count('status'))
    for stat in job_stats:
        percentage = (stat['count'] / total_jobs * 100) if total_jobs > 0 else 0
        writer.writerow([
            f"Jobs - {stat['status'].title()}",
            stat['count'],
            f"{percentage:.1f}%"
        ])
    
    # User statistics
    user_stats = CustomUser.objects.values('user_type').annotate(count=Count('user_type'))
    for stat in user_stats:
        percentage = (stat['count'] / total_users * 100) if total_users > 0 else 0
        writer.writerow([
            f"Users - {stat['user_type'].title()}",
            stat['count'],
            f"{percentage:.1f}%"
        ])
    
    # Moderation statistics
    moderation_stats = JobPosting.objects.values('moderation_status').annotate(count=Count('moderation_status'))
    for stat in moderation_stats:
        percentage = (stat['count'] / total_jobs * 100) if total_jobs > 0 else 0
        writer.writerow([
            f"Moderation - {stat['moderation_status'].title()}",
            stat['count'],
            f"{percentage:.1f}%"
        ])
    
    return response


@login_required
@admin_required
def bulk_moderation_view(request):
    """Bulk moderation actions"""
    
    if request.method == 'POST':
        job_ids = request.POST.getlist('job_ids')
        action = request.POST.get('bulk_action')
        
        if not job_ids:
            messages.error(request, 'No jobs selected.')
            return redirect('moderation_queue')
        
        jobs = JobPosting.objects.filter(id__in=job_ids)
        count = 0
        
        for job in jobs:
            if action == 'approve':
                job.moderation_status = 'approved'
                job.status = 'active'
                count += 1
            elif action == 'reject':
                job.moderation_status = 'rejected'
                job.status = 'inactive'
                count += 1
            elif action == 'delete':
                job.delete()
                count += 1
            
            if action != 'delete':
                job.moderated_by = request.user
                job.moderated_at = timezone.now()
                job.save()
        
        messages.success(request, f'{count} job(s) have been {action}d.')
        return redirect('moderation_queue')
    
    return redirect('moderation_queue')
