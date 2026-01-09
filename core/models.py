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

