from django.utils import timezone


class UserActivityMiddleware:
    """Simple middleware to update `last_activity` on the user if the attribute exists.

    Keeps startup safe by providing the class referenced in settings.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            user = getattr(request, 'user', None)
            if user and user.is_authenticated and hasattr(user, 'last_activity'):
                user.last_activity = timezone.now()
                # save only the field to minimize DB writes
                user.save(update_fields=['last_activity'])
        except Exception:
            # Do not break requests for any reason here
            pass
        return response
