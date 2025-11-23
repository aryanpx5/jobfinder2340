"""
Management command to check saved searches for new matches and create notifications.

Run this command periodically (e.g., via cron) to check for new candidates matching saved searches.
Example: python manage.py check_saved_searches
"""
from django.core.management.base import BaseCommand
from jobs.models import SavedSearch, JobSeekerProfile, SearchNotification
from django.utils import timezone
from django.db.models import Q


class Command(BaseCommand):
    help = 'Check all saved searches for new matches and create notifications'

    def handle(self, *args, **options):
        # Check searches that have notifications enabled
        searches = SavedSearch.objects.filter(notify_on_match=True)
        
        total_notifications = 0
        
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
            new_notifications = 0
            for profile in profiles:
                notification, created = SearchNotification.objects.get_or_create(
                    saved_search=search,
                    candidate=profile,
                    defaults={'is_read': False}
                )
                if created:
                    new_notifications += 1
            
            total_notifications += new_notifications
            
            # Update last_checked_at
            search.last_checked_at = timezone.now()
            search.save(update_fields=['last_checked_at'])
            
            if new_notifications > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {new_notifications} notification(s) for search "{search.name}"'
                    )
                )
        
        if total_notifications == 0:
            self.stdout.write(self.style.SUCCESS('No new matches found.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total: {total_notifications} new notification(s) created.'
                )
            )

