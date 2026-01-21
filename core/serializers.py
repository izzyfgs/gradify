# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSearchSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'avatar_url', 'profile_url']

    def get_avatar_url(self, obj):
        try:
            profile = obj.userprofile
            if profile.profile_pic and profile.profile_pic.name != 'images/default_avatar.jpg':
                return profile.profile_pic.url
            # Return the same default your model uses
            return "/static/images/default_avatar.jpg"
        except AttributeError:
            return "/static/images/default_avatar.jpg"

    def get_profile_url(self, obj):
        return f"/profile/{obj.username}/"