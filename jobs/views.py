from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobSeekerProfile, JobPosting, JobApplication
from .forms import JobSeekerProfileForm, PrivacySettingsForm
from .forms import JobPostingForm, MessageForm
from .models import Message
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.db.models import Q
from django import forms
from django.urls import reverse


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
