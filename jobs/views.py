from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobSeekerProfile, JobPosting, JobApplication, SavedSearch, SearchNotification
from .forms import JobSeekerProfileForm, PrivacySettingsForm
from .forms import JobPostingForm, MessageForm, EmailCandidateForm, SavedSearchForm
from .models import Message
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
from django import forms
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


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
# RECOMMENDATIONS VIEW
# -------------------------
@login_required
def recommended_jobs_view(request):
    """
    Recommend active, approved jobs based on overlap between a job seeker's skills
    and a job's required_skills. Uses simple case-insensitive token overlap.
    """
    if getattr(request.user, 'user_type', None) != 'job_seeker':
        messages.error(request, 'Only job seekers receive recommendations.')
        return redirect('dashboard')

    try:
        profile = JobSeekerProfile.objects.get(user=request.user)
    except JobSeekerProfile.DoesNotExist:
        messages.info(request, 'Create your profile to get recommendations.')
        return redirect('create_profile')

    # Normalize skills from profile
    raw_skills = profile.skills or ''
    profile_skills = [s.strip().lower() for s in raw_skills.split(',') if s.strip()]
    profile_skill_set = set(profile_skills)

    jobs_qs = JobPosting.objects.filter(status='active', moderation_status='approved')

    # Score jobs by number of overlapping skills; include jobs with at least one match
    scored = []
    for job in jobs_qs:
        job_skills = [s.strip().lower() for s in (job.required_skills or '').split(',') if s.strip()]
        overlap = profile_skill_set.intersection(job_skills)
        score = len(overlap)
        if score > 0 or not profile_skill_set:
            scored.append((score, overlap, job))

    # Sort by score desc, then recency via created_at which is desc in Meta ordering
    scored.sort(key=lambda t: t[0], reverse=True)

    # Take top N
    top = scored[:25]
    recommendations = [job for _, __, job in top]

    context = {
        'profile': profile,
        'recommendations': recommendations,
        'profile_skills': profile_skills,
    }
    return render(request, 'jobs/recommendations.html', context)


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
    
    # Get user's preferred commute radius if they're a job seeker
    preferred_radius = 25  # default
    if request.user.is_authenticated and request.user.user_type == 'job_seeker':
        try:
            profile = JobSeekerProfile.objects.get(user=request.user)
            preferred_radius = profile.preferred_commute_radius
        except JobSeekerProfile.DoesNotExist:
            pass
    
    context = {
        'jobs': jobs,
        'search_params': request.GET,
        'preferred_radius': preferred_radius,
    }
    return render(request, 'jobs/job_search.html', context)


class ApplyForm(forms.Form):
    cover_letter = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Optional cover letter'}),
        required=False
    )


@login_required
def apply_to_posting_view(request, pk):
    # Only job seekers may apply
    if getattr(request.user, 'user_type', None) != 'job_seeker':
        messages.error(request, 'Only job seekers can apply to postings.')
        return redirect('job_search')

    posting = get_object_or_404(JobPosting, pk=pk, status='active', moderation_status='approved')

    # Prevent duplicate applications
    if JobApplication.objects.filter(job=posting, applicant=request.user).exists():
        messages.info(request, 'You have already applied to this job.')
        return redirect('job_search')

    if request.method == 'POST':
        form = ApplyForm(request.POST)
        if form.is_valid():
            JobApplication.objects.create(
                job=posting,
                applicant=request.user,
                cover_letter=form.cleaned_data.get('cover_letter', '')
            )
            messages.success(request, 'Application submitted successfully.')
            return HttpResponseRedirect(reverse('job_search'))
    else:
        form = ApplyForm()

    return render(request, 'jobs/apply.html', {'posting': posting, 'form': form})


# -------------------------
# RECRUITER: LIST OWN POSTINGS
# -------------------------
@login_required
@recruiter_required
def my_postings_view(request):
    postings = JobPosting.objects.filter(recruiter=request.user)
    return render(request, 'jobs/my_postings.html', {'postings': postings})


@login_required
@recruiter_required
def posting_applicants_view(request, pk):
    posting = get_object_or_404(JobPosting, pk=pk)
    if posting.recruiter != request.user:
        return HttpResponseForbidden('You do not have permission to view applicants for this posting.')
    applications = JobApplication.objects.filter(job=posting).select_related('applicant')
    return render(request, 'jobs/applicants_list.html', {'posting': posting, 'applications': applications})


@login_required
@recruiter_required
def applicant_locations_api(request, posting_pk):
    """Return JSON grouped counts of applicants by their profile.location for a posting."""
    posting = get_object_or_404(JobPosting, pk=posting_pk)
    if posting.recruiter != request.user:
        return JsonResponse({'error': 'forbidden'}, status=403)

    apps = JobApplication.objects.filter(job=posting).select_related('applicant')
    counts = {}
    for a in apps:
        loc = ''
        try:
            profile = a.applicant.jobseekerprofile
            loc = (profile.location or '').strip()
        except Exception:
            loc = ''
        if not loc:
            continue
        counts[loc] = counts.get(loc, 0) + 1

    data = [{'location': loc, 'count': cnt} for loc, cnt in counts.items()]
    return JsonResponse({'posting': posting.pk, 'locations': data})


@login_required
@recruiter_required
def applicants_map_view(request, posting_pk):
    posting = get_object_or_404(JobPosting, pk=posting_pk)
    if posting.recruiter != request.user:
        return HttpResponseForbidden('You do not have permission to view this map.')
    return render(request, 'jobs/applicants_map.html', {'posting': posting})


@login_required
@recruiter_required
def posting_recommendations_view(request, pk):
    """Recommend job seeker profiles for a specific posting based on skill overlap."""
    posting = get_object_or_404(JobPosting, pk=pk)
    if posting.recruiter != request.user:
        return HttpResponseForbidden('You do not have permission to view recommendations for this posting.')

    # Normalize required skills for the job
    job_skill_set = set(
        s.strip().lower()
        for s in (posting.required_skills or '').split(',')
        if s.strip()
    )

    # Exclude people who already applied to this posting
    applied_ids = JobApplication.objects.filter(job=posting).values_list('applicant_id', flat=True)

    profiles = JobSeekerProfile.objects.filter(profile_visible=True).exclude(user_id__in=applied_ids)

    recommendations = []
    for profile in profiles:
        seeker_skills = [
            s.strip().lower() for s in (profile.skills or '').split(',') if s.strip()
        ]
        overlap = job_skill_set.intersection(seeker_skills) if job_skill_set else set()
        score = len(overlap)

        # If the job lists skills, keep only profiles with at least one match
        if job_skill_set and score == 0:
            continue

        coverage_pct = 0
        if job_skill_set:
            coverage_pct = round((score / len(job_skill_set)) * 100)

        recommendations.append({
            'profile': profile,
            'overlap': sorted(overlap),
            'score': score,
            'coverage_pct': coverage_pct,
            'allow_contact': getattr(profile, 'allow_contact', True),
        })

    # Sort by score desc, then coverage, then most recently updated profile
    recommendations.sort(key=lambda r: (r['score'], r['coverage_pct'], r['profile'].updated_at), reverse=True)

    context = {
        'posting': posting,
        'recommendations': recommendations,
        'job_skill_set': sorted(job_skill_set),
    }
    return render(request, 'jobs/posting_recommendations.html', context)


@login_required
@recruiter_required
def conversation_view(request, posting_pk, applicant_pk):
    posting = get_object_or_404(JobPosting, pk=posting_pk)
    if posting.recruiter != request.user:
        return HttpResponseForbidden('You do not have permission to view this conversation.')

    # Ensure the applicant applied to this posting (defensive)
    User = get_user_model()
    applicant = get_object_or_404(User, pk=applicant_pk)
    applied = JobApplication.objects.filter(job=posting, applicant=applicant).exists()
    if not applied:
        messages.error(request, 'That user has not applied to this posting.')
        return redirect('posting_applicants', pk=posting.pk)

    # Fetch messages between recruiter (request.user) and applicant
    convo = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=applicant)) |
        (Q(sender=applicant) & Q(recipient=request.user))
    ).order_by('created_at')

    return render(request, 'jobs/conversation.html', {'posting': posting, 'applicant': applicant, 'messages': convo})


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
            
            # Get latitude and longitude from POST data
            try:
                lat = request.POST.get('latitude')
                lon = request.POST.get('longitude')
                if lat and lon:
                    posting.latitude = float(lat)
                    posting.longitude = float(lon)
            except (ValueError, TypeError):
                pass
            
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
            updated_posting = form.save(commit=False)
            
            # Get latitude and longitude from POST data
            try:
                lat = request.POST.get('latitude')
                lon = request.POST.get('longitude')
                if lat and lon:
                    updated_posting.latitude = float(lat)
                    updated_posting.longitude = float(lon)
            except (ValueError, TypeError):
                pass
            
            updated_posting.save()
            messages.success(request, 'Job posting updated successfully.')
            return redirect('my_postings')
    else:
        form = JobPostingForm(instance=posting)
    return render(request, 'jobs/edit_posting.html', {'form': form, 'posting': posting})


# -------------------------
# MESSAGING
# -------------------------
@login_required
def inbox_view(request):
    messages_qs = Message.objects.filter(recipient=request.user)
    return render(request, 'jobs/messages/inbox.html', {'messages': messages_qs})


@login_required
def message_detail_view(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if msg.recipient != request.user and msg.sender != request.user:
        return HttpResponseForbidden('You do not have permission to view this message.')
    if msg.recipient == request.user and not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=['is_read'])
    return render(request, 'jobs/messages/detail.html', {'message': msg})


@login_required
def compose_message_view(request):
    # Allow any authenticated user to compose messages. Job seekers may ONLY reply
    # to messages that a recruiter sent them (reply_to=<message_id>); they cannot
    # initiate new conversations to arbitrary recruiters.
    recipient_prefill = request.GET.get('recipient')
    reply_to = request.GET.get('reply_to')
    orig_msg = None
    if reply_to:
        try:
            orig_msg = get_object_or_404(Message, pk=int(reply_to))
        except Exception:
            orig_msg = None

    # If the user is a job seeker and not replying to a recruiter message, block.
    if getattr(request.user, 'user_type', None) == 'job_seeker' and not orig_msg:
        messages.error(request, 'Job seekers cannot start new conversations. Reply to a recruiter message instead.')
        return redirect('inbox')

    if request.method == 'POST':
        form = MessageForm(request.POST, sender=request.user)
        if form.is_valid():
            m = form.save(commit=False)
            m.sender = request.user

            # If sender is a job seeker, ensure they're replying to the same recruiter
            if getattr(request.user, 'user_type', None) == 'job_seeker':
                if not orig_msg or form.cleaned_data.get('recipient') != orig_msg.sender:
                    messages.error(request, 'You may only reply to the recruiter who contacted you.')
                    return redirect('inbox')

            # If recipient is a job seeker, respect their allow_contact setting
            try:
                profile = JobSeekerProfile.objects.get(user=m.recipient)
                if not profile.allow_contact and getattr(request.user, 'user_type', None) == 'recruiter':
                    messages.error(request, 'This candidate has disabled direct contact.')
                    return redirect('inbox')
            except JobSeekerProfile.DoesNotExist:
                pass

            m.save()
            messages.success(request, 'Message sent.')
            return redirect('inbox')
    else:
        initial = {}
        preset_recipient = None
        if orig_msg:
            # Pre-fill recipient to original sender (the recruiter)
            initial['recipient'] = orig_msg.sender.id
            if orig_msg.subject:
                initial['subject'] = f"Re: {orig_msg.subject}"
        elif recipient_prefill:
            try:
                initial['recipient'] = int(recipient_prefill)
            except Exception:
                pass

        form = MessageForm(initial=initial, sender=request.user)

        # If we have a preset recipient id, resolve the User object to display username
        rid = initial.get('recipient')
        if rid:
            try:
                User = get_user_model()
                preset_recipient = User.objects.get(pk=rid)
            except Exception:
                preset_recipient = None

    return render(request, 'jobs/messages/compose.html', {'form': form, 'preset_recipient': preset_recipient})


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


# -------------------------
# SAVE COMMUTE RADIUS (AJAX)
# -------------------------
@login_required
@require_POST
def save_commute_radius_view(request):
    """Save the user's preferred commute radius via AJAX"""
    if request.user.user_type != 'job_seeker':
        return JsonResponse({'success': False, 'error': 'Only job seekers can save commute preferences'}, status=403)
    
    try:
        radius = int(request.POST.get('radius', 25))
        if radius < 5 or radius > 100:
            return JsonResponse({'success': False, 'error': 'Radius must be between 5 and 100 miles'}, status=400)
        
        profile, created = JobSeekerProfile.objects.get_or_create(user=request.user)
        profile.preferred_commute_radius = radius
        profile.save(update_fields=['preferred_commute_radius'])
        
        return JsonResponse({'success': True, 'radius': radius})
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid radius value'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# -------------------------
# USER STORY 14: EMAIL CANDIDATE
# -------------------------
@login_required
@recruiter_required
def email_candidate_view(request, candidate_id):
    """Allow recruiters to email candidates through the platform."""
    User = get_user_model()
    candidate = get_object_or_404(User, pk=candidate_id, user_type='job_seeker')
    
    # Check if recruiter has an email address
    if not request.user.email:
        messages.error(request, 'You must have an email address set in your profile to send emails. Please update your profile.')
        return redirect('dashboard')
    
    # Check if candidate allows contact
    try:
        profile = JobSeekerProfile.objects.get(user=candidate)
        if not profile.allow_contact:
            messages.error(request, 'This candidate has disabled direct contact.')
            return redirect('dashboard')
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, 'Candidate profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmailCandidateForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            
            # Get candidate's email
            candidate_email = candidate.email
            if not candidate_email:
                messages.error(request, 'Candidate does not have an email address on file.')
                return render(request, 'jobs/email_candidate.html', {'form': form, 'candidate': candidate})
            
            # Prepare email content
            email_subject = f"[JobFinder] {subject}"
            email_message = f"""Hello {candidate.get_full_name() or candidate.username},

You received this message from {request.user.get_full_name() or request.user.username} ({request.user.email}) through the JobFinder platform.

Message:
{message_body}

---
This message was sent through JobFinder. Please reply directly to {request.user.email} if you wish to respond.
"""
            
            # Determine from_email - use recruiter's email if available, otherwise use DEFAULT_FROM_EMAIL
            from_email = request.user.email if request.user.email else (
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@jobfinder.com'
            )
            
            try:
                # Log the email attempt
                logger.info(f"Attempting to send email from {from_email} to {candidate_email}")
                
                # Send email
                send_mail(
                    email_subject,
                    email_message,
                    from_email,
                    [candidate_email],
                    fail_silently=False,
                )
                
                logger.info(f"Email sent successfully from {from_email} to {candidate_email}")
                messages.success(request, f'Email sent successfully to {candidate_email}')
                
                # If using console backend, inform the user
                if hasattr(settings, 'EMAIL_BACKEND') and 'console' in settings.EMAIL_BACKEND:
                    messages.info(request, 'Note: Email was printed to console (development mode). Check your terminal/console output.')
                
                return redirect('dashboard')
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to send email: {error_msg}")
                messages.error(request, f'Failed to send email: {error_msg}')
                # Re-render form with error
                return render(request, 'jobs/email_candidate.html', {'form': form, 'candidate': candidate})
    else:
        form = EmailCandidateForm()
    
    return render(request, 'jobs/email_candidate.html', {'form': form, 'candidate': candidate})


# -------------------------
# USER STORY 15: SAVED SEARCHES
# -------------------------
@login_required
@recruiter_required
def candidate_search_view(request):
    """Search for candidates based on criteria."""
    profiles = JobSeekerProfile.objects.filter(profile_visible=True)
    
    # Apply filters from GET parameters
    skills = request.GET.get('skills', '')
    location = request.GET.get('location', '')
    headline = request.GET.get('headline', '')
    
    if skills:
        # Filter profiles that have any of the specified skills
        skill_list = [s.strip().lower() for s in skills.split(',') if s.strip()]
        for skill in skill_list:
            profiles = profiles.filter(skills__icontains=skill)
    
    if location:
        profiles = profiles.filter(location__icontains=location)
    
    if headline:
        profiles = profiles.filter(headline__icontains=headline)
    
    # Check if this is a save request
    save_search = request.GET.get('save_search') == 'true'
    search_name = request.GET.get('search_name', '')
    
    context = {
        'profiles': profiles,
        'search_params': {
            'skills': skills,
            'location': location,
            'headline': headline,
        },
        'save_search': save_search,
        'search_name': search_name,
    }
    
    return render(request, 'jobs/candidate_search.html', context)


@login_required
@recruiter_required
def save_search_view(request):
    """Save a candidate search."""
    if request.method == 'POST':
        form = SavedSearchForm(request.POST)
        if form.is_valid():
            saved_search = form.save(commit=False)
            saved_search.recruiter = request.user
            saved_search.save()
            messages.success(request, f'Search "{saved_search.name}" saved successfully!')
            return redirect('saved_searches')
    else:
        # Pre-fill form with current search parameters
        initial = {
            'skills': request.GET.get('skills', ''),
            'location': request.GET.get('location', ''),
            'headline': request.GET.get('headline', ''),
            'name': request.GET.get('name', ''),
        }
        form = SavedSearchForm(initial=initial)
    
    return render(request, 'jobs/save_search.html', {'form': form})


@login_required
@recruiter_required
def saved_searches_view(request):
    """List all saved searches for the recruiter."""
    searches = SavedSearch.objects.filter(recruiter=request.user)
    
    # Get notification counts for each search
    for search in searches:
        search.unread_count = SearchNotification.objects.filter(
            saved_search=search,
            is_read=False
        ).count()
    
    return render(request, 'jobs/saved_searches.html', {'searches': searches})


@login_required
@recruiter_required
def run_saved_search_view(request, search_id):
    """Run a saved search and show results."""
    saved_search = get_object_or_404(SavedSearch, pk=search_id, recruiter=request.user)
    
    profiles = JobSeekerProfile.objects.filter(profile_visible=True)
    
    # Apply saved search criteria
    if saved_search.skills:
        skill_list = [s.strip().lower() for s in saved_search.skills.split(',') if s.strip()]
        for skill in skill_list:
            profiles = profiles.filter(skills__icontains=skill)
    
    if saved_search.location:
        profiles = profiles.filter(location__icontains=saved_search.location)
    
    if saved_search.headline:
        profiles = profiles.filter(headline__icontains=saved_search.headline)
    
    # If notifications are enabled, check for new matches
    if saved_search.notify_on_match:
        # Get profiles that are new or updated since last check
        new_profiles = profiles
        if saved_search.last_checked_at:
            new_profiles = new_profiles.filter(
                Q(created_at__gt=saved_search.last_checked_at) | Q(updated_at__gt=saved_search.last_checked_at)
            )
        
        # Create notifications for new matches
        new_notifications_count = 0
        for profile in new_profiles:
            notification, created = SearchNotification.objects.get_or_create(
                saved_search=saved_search,
                candidate=profile,
                defaults={'is_read': False}
            )
            if created:
                new_notifications_count += 1
        
        if new_notifications_count > 0:
            messages.info(request, f'Found {new_notifications_count} new match(es)! Check your notifications.')
    
    # Update last_checked_at
    saved_search.last_checked_at = timezone.now()
    saved_search.save(update_fields=['last_checked_at'])
    
    context = {
        'saved_search': saved_search,
        'profiles': profiles,
    }
    
    return render(request, 'jobs/saved_search_results.html', context)


@login_required
@recruiter_required
@require_POST
def delete_saved_search_view(request, search_id):
    """Delete a saved search."""
    saved_search = get_object_or_404(SavedSearch, pk=search_id, recruiter=request.user)
    search_name = saved_search.name
    saved_search.delete()
    messages.success(request, f'Search "{search_name}" deleted successfully.')
    return redirect('saved_searches')


@login_required
@recruiter_required
def search_notifications_view(request):
    """View notifications for new matches in saved searches."""
    notifications = SearchNotification.objects.filter(
        saved_search__recruiter=request.user
    ).select_related('saved_search', 'candidate', 'candidate__user').order_by('-created_at')
    
    return render(request, 'jobs/search_notifications.html', {'notifications': notifications})


@login_required
@recruiter_required
@require_POST
def mark_notification_read_view(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(
        SearchNotification,
        pk=notification_id,
        saved_search__recruiter=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return JsonResponse({'success': True})


def check_saved_searches_for_matches():
    """Check all saved searches for new matches and create notifications.
    This should be called periodically (e.g., via a management command or cron job).
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Check searches that have notifications enabled
    searches = SavedSearch.objects.filter(notify_on_match=True)
    
    for search in searches:
        # Get profiles matching the search criteria
        profiles = JobSeekerProfile.objects.filter(profile_visible=True)
        
        if search.skills:
            skill_list = [s.strip().lower() for s in search.skills.split(',') if s.strip()]
            for skill in skill_list:
                profiles = profiles.filter(skills__icontains=skill)
        
        if search.location:
            profiles = profiles.filter(location__icontains=search.location)
        
        if search.headline:
            profiles = profiles.filter(headline__icontains=search.headline)
        
        # Only consider profiles created/updated after last check (or all if never checked)
        if search.last_checked_at:
            profiles = profiles.filter(
                Q(created_at__gt=search.last_checked_at) | Q(updated_at__gt=search.last_checked_at)
            )
        
        # Create notifications for new matches
        for profile in profiles:
            SearchNotification.objects.get_or_create(
                saved_search=search,
                candidate=profile,
                defaults={'is_read': False}
            )
        
        # Update last_checked_at
        search.last_checked_at = timezone.now()
        search.save(update_fields=['last_checked_at'])
