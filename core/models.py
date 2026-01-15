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

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    streak_days = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"

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