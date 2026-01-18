from django.utils import timezone

class LastSeenMiddleware:
    """
    Updates user's last_seen on every request (logged-in users only).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
                profile.last_seen = timezone.now()
                profile.save(update_fields=["last_seen"])
            except Exception:
                pass
        return self.get_response(request)
