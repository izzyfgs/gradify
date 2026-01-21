# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile

# Add UserProfile as inline to User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('profile_pic', 'cover_pic', 'bio', 'streak')  # show only relevant fields

# Extend the default UserAdmin to include the inline
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

# Unregister default User admin, register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register other models if needed
admin.site.register(UserProfile)