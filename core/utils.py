# core/utils.py
from datetime import date, timedelta
from .models import Score # Or whichever model tracks daily activity

def get_streak(user):
    # This is a placeholder logic
    # You can customize this based on how you track 'daily' activity
    return 5  # For now, return a dummy number to stop the crash