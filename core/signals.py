from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile

@receiver(user_logged_in)
def update_streak(sender, request, user, **kwargs):
    # Get or create the profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    today = timezone.now().date()
    
    # 1. If they already logged in today, do nothing
    if profile.last_login_date == today:
        return

    # 2. If it's their first login ever OR they missed more than one day
    yesterday = today - timezone.timedelta(days=1)
    
    if profile.last_login_date == yesterday:
        # Logged in yesterday? Increment the streak
        profile.streak += 1
    else:
        # Missed a day (or first time)? Reset/Start streak at 1
        profile.streak = 1
        
    # 3. Update the date and save
    profile.last_login_date = today
    profile.save()

    # core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Follow, Notification  # ← safe here, models are already loaded

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.following,
            message=f"{instance.follower.username} started following you!",
            link=f"/profile/{instance.follower.username}/",
            is_read=False
        )