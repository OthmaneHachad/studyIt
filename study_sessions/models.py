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
    course = models.ForeignKey(
        "accounts.Class",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
        help_text="Optional: Label this session with a specific class/course",
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


class SessionEnrollment(models.Model):
    """Tracks a student's request to join a study session."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="session_enrollments",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["session", "student"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.name} -> {self.session.title} ({self.status})"
