from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class TaskManager(models.Manager):
    """Default manager hides soft-deleted tasks."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllTaskManager(models.Manager):
    """Manager that includes deleted tasks (used for the trash bin)."""

    def get_queryset(self):
        return super().get_queryset()


class Task(models.Model):
    CATEGORY_CHOICES = [
        ("work", "Work"),
        ("study", "Study"),
        ("personal", "Personal"),
        ("health", "Health"),
    ]
    PRIORITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]
    REMIND_CHOICES = [
        (0, "Off"),
        (5, "5 minutes before"),
        (15, "15 minutes before"),
        (30, "30 minutes before"),
        (60, "1 hour before"),
        (1440, "1 day before"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="work")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Reminders
    remind_minutes_before = models.PositiveIntegerField(default=0)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskManager()
    all_objects = AllTaskManager()

    class Meta:
        ordering = ["completed", "-created_at"]

    def __str__(self):
        return self.title

    def total_minutes(self):
        agg = self.time_logs.aggregate(total=models.Sum("minutes"))
        return agg["total"] or 0

    def end_time(self):
        if self.due_date and self.duration_minutes:
            return self.due_date + timedelta(minutes=self.duration_minutes)
        return None

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class TimeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="time_logs")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_logs")
    minutes = models.PositiveIntegerField()
    note = models.CharField(max_length=200, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_at"]

    def __str__(self):
        return f"{self.task.title} — {self.minutes}m"


class UserSettings(models.Model):
    """Per-user app preferences (very small)."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="settings"
    )
    notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"settings({self.user.username})"

    @classmethod
    def for_user(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj
