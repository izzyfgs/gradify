from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile


@receiver(user_logged_in)
def update_streak(sender, request, user, **kwargs):
    # This ensures a profile exists even if it wasn't created at registration
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    today = timezone.now().date()
    
    # Check if they already logged in today to avoid resetting/doubling streak
    if profile.last_login_date == today:
        return

    # If they logged in yesterday, increment streak
    yesterday = today - timezone.timedelta(days=1)
    if profile.last_login_date == yesterday:
        profile.streak += 1
    else:
        # If they missed a day, reset streak to 1
        profile.streak = 1
        
    profile.last_login_date = today
    profile.save()