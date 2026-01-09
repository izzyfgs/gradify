from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile


@receiver(user_logged_in)
def update_streak(sender, user, request, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    today = timezone.localdate()

    if profile.last_login_date is None:
        profile.streak_days = 1
    else:
        diff = (today - profile.last_login_date).days
        if diff == 0:
            # same day login, streak stays
            pass
        elif diff == 1:
            profile.streak_days += 1
        else:
            profile.streak_days = 0

    profile.last_login_date = today
    profile.save()
