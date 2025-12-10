from django.db import models
from django.utils import timezone
from accounts.models import TAProfile
from locations.models import Location


class StudySession(models.Model):
    """Study session posted by a TA/Session host."""

    host = models.ForeignKey(
        TAProfile,
        on_delete=models.CASCADE,
        related_name="study_sessions",
        help_text="TA or session host for this session",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} - {self.host.name}"

    @property
    def is_upcoming(self):
        return self.start_time >= timezone.now()
