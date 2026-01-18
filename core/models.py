from django.conf import settings
from django.db import models


from django.db import models
from django.contrib.auth.models import User

class UserSubject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=80)

    class Meta:
        unique_together = ("user", "name")  # prevents duplicates per user

    def __str__(self):
        return f"{self.user.username} - {self.name}"



from django.db import models
from django.conf import settings

class Score(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    subject = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    correct = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "subject", "year")
        ordering = ["-created_at"]

    @property
    def percentage(self) -> float:
        """Returns the precise percentage (e.g., 95.5) for text display."""
        if self.total <= 0:
            return 0.0
        return round((self.correct / self.total) * 100, 1)

    @property
    def percentage_int(self) -> int:
        """Returns a whole number for CSS width calculations (e.g., 95)."""
        if self.total <= 0:
            return 0
        return int((self.correct / self.total) * 100)

    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.year}): {self.correct}/{self.total}"

from django.db import models
from django.contrib.auth.models import User

# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    
    # Missing field causing the AttributeError:
    last_login_date = models.DateField(null=True, blank=True)
    streak_count = models.IntegerField(default=0) # Often used with login signals
    
    profile_pic = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        default='default_avatar.png'
    )
    
    cover_pic = models.ImageField(
        upload_to='cover_pics/', 
        blank=True, 
        null=True
    )
    
    bio = models.TextField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
from django.db import models

class SupportFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    # keywords like: "login, password, subjects, streak, score"
    keywords = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

from django.conf import settings
from django.db import models


class AIConversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AIConversation({self.user.username})"


class AIMessage(models.Model):
    SENDER_CHOICES = (
        ("user", "User"),
        ("ai", "AI"),
    )

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.text[:35]}"

from django.db import models
from django.conf import settings

class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.CharField(max_length=10, choices=(("user", "User"), ("ai", "AI")))
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} [{self.sender}] {self.created_at:%Y-%m-%d %H:%M}"
    

from django.conf import settings
from django.db import models
from django.utils import timezone


class FAQ(models.Model):
    """
    Stores the knowledge base used by the AI (200+ Q/A).
    """
    category = models.CharField(max_length=80, default="General")
    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.category}] {self.question}"


class ChatSession(models.Model):
    """
    One session per user (we keep it simple: 1 active session per user).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=120, default="Gradify Support Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Used to make the bot more realistic:
    awaiting_clarification = models.BooleanField(default=False)
    last_unresolved_question = models.TextField(blank=True, default="")

    def __str__(self):
        return f"ChatSession({self.user.username})"


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"

class ChatMessage(models.Model):
    # Set null=True so existing messages don't need a session ID number
    session = models.ForeignKey('ChatSession', on_delete=models.CASCADE, null=True, blank=True)
    
    # Set a default string for the role
    role = models.CharField(max_length=50, default='user')
    
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:20]}"
    

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserSubject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=80)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Score(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    subject = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    correct = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "subject", "year")
        ordering = ["-created_at"]

    @property
    def percentage(self) -> float:
        if self.total <= 0:
            return 0.0
        return round((self.correct / self.total) * 100, 1)

    @property
    def percentage_int(self) -> int:
        if self.total <= 0:
            return 0
        return int((self.correct / self.total) * 100)

    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.year}): {self.correct}/{self.total}"


# ✅ USER PROFILE (DATABASE SAVED)
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL




# ✅ FOLLOW SYSTEM
class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# ✅ POSTS
class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def can_edit(self):
        return timezone.now() <= self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"Post by {self.user.username}"


# ✅ LIKES
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


# ✅ COMMENTS
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented"


# ✅ NOTIFICATIONS
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=200)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

from django.conf import settings
from django.db import models
from django.utils import timezone


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    pin_hash = models.CharField(max_length=128, blank=True, null=True)  # store hashed pin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_pin(self):
        return bool(self.pin_hash)

    def __str__(self):
        return f"{self.user.username} Wallet"
    
class Transaction(models.Model):
    STATUS_CHOICES = (("SUCCESS", "SUCCESS"), ("FAILED", "FAILED"))
    code = models.CharField(max_length=15, unique=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_trans")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="received_trans")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="SUCCESS")
    created_at = models.DateTimeField(default=timezone.now)

# models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import random

class CoinFlipBet(models.Model):
    CHOICES = [('HEADS', 'Heads'), ('TAILS', 'Tails')]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    choice = models.CharField(max_length=5, choices=CHOICES)
    result = models.CharField(max_length=5, choices=CHOICES, blank=True)
    is_win = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            # 1. Deduct balance from user profile (assumes Profile model has 'balance')
            profile = self.user.profile
            if profile.balance < self.amount:
                raise ValidationError("Insufficient balance")
            
            profile.balance -= self.amount
            
            # 2. Flip the coin
            self.result = random.choice(['HEADS', 'TAILS'])
            self.is_win = (self.choice == self.result)
            
            # 3. If win, add 2x amount back
            if self.is_win:
                profile.balance += (self.amount * 2)
            
            profile.save()
        super().save(*args, **kwargs)

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = settings.AUTH_USER_MODEL

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    user1 = models.ForeignKey(User, related_name="conversations_as_user1", on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name="conversations_as_user2", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="unique_conversation_pair"),
        ]

    @staticmethod
    def normalize_pair(a, b):
        return (a, b) if a.id < b.id else (b, a)

    @staticmethod
    def get_or_create_between(user_a, user_b):
        u1, u2 = Conversation.normalize_pair(user_a, user_b)
        conv, _ = Conversation.objects.get_or_create(user1=u1, user2=u2)
        return conv

    def other_user(self, me):
        return self.user2 if self.user1_id == me.id else self.user1


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    text = models.TextField(max_length=2000, blank=True)           # ← allow blank
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    audio = models.FileField(upload_to='chat_audio/', null=True, blank=True)   # ← ADD THIS

    read_by_user1 = models.BooleanField(default=False)
    read_by_user2 = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

from django.db import models
from django.contrib.auth.models import User

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    
    # Notifications
    notify_likes = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=True)
    notify_follows = models.BooleanField(default=True)

    # Appearance
    dark_mode = models.BooleanField(default=False) # <--- Ensure this is here
    compact_mode = models.BooleanField(default=False)
    
    # Privacy
    public_profile = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.username}"
    
from django.db import models
from django.contrib.auth.models import User

class UserBlock(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_made")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "blocked")


class UserMute(models.Model):
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mutes_made")
    muted = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mutes_received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("muter", "muted")

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    notify_likes = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=True)
    notify_follows = models.BooleanField(default=True)

    dark_mode = models.BooleanField(default=False)
    # ...anything else

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")  # receiver
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="actions")      # who did it
    notif_type = models.CharField(max_length=30)  # like/comment/follow
    post = models.ForeignKey("Post", null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey("Comment", null=True, blank=True, on_delete=models.CASCADE)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


