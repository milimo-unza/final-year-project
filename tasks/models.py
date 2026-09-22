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
    # Lower number = higher priority. Used for ordering and dot precedence.
    PRIORITY_RANK = {"high": 1, "medium": 2, "low": 3}
    CATEGORY_RANK = {"work": 0, "study": 1, "personal": 2, "health": 3}

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
    """Per-user app preferences."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="settings"
    )
    notifications_enabled = models.BooleanField(default=True)

    # v1.3 — per-user overrides
    show_public_holidays = models.BooleanField(default=True)

    # Renamable category labels (defaults match Task.CATEGORY_CHOICES).
    category_work_label = models.CharField(max_length=40, default="Work")
    category_study_label = models.CharField(max_length=40, default="Study")
    category_personal_label = models.CharField(max_length=40, default="Personal")
    category_health_label = models.CharField(max_length=40, default="Health")

    def __str__(self):
        return f"settings({self.user.username})"

    @classmethod
    def for_user(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj

    def category_labels(self):
        return {
            "work": self.category_work_label or "Work",
            "study": self.category_study_label or "Study",
            "personal": self.category_personal_label or "Personal",
            "health": self.category_health_label or "Health",
        }


class ActivityLog(models.Model):
    """Last-30-actions audit trail per user."""

    ACTION_CHOICES = [
        ("created", "Created"),
        ("edited", "Edited"),
        ("completed", "Completed"),
        ("reopened", "Re-opened"),
        ("deleted", "Moved to trash"),
        ("restored", "Restored from trash"),
        ("purged", "Permanently deleted"),
    ]

    MAX_ENTRIES_PER_USER = 30

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_log")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    task_title = models.CharField(max_length=200)
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_log"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.action} {self.task_title}"

    @classmethod
    def record(cls, user, action, task):
        """Add an entry and trim to MAX_ENTRIES_PER_USER newest rows."""
        entry = cls.objects.create(
            user=user,
            action=action,
            task_title=getattr(task, "title", "(unknown)")[:200],
            task=task if getattr(task, "pk", None) else None,
        )
        # Trim
        ids_to_keep = list(
            cls.objects.filter(user=user)
            .order_by("-created_at")
            .values_list("id", flat=True)[: cls.MAX_ENTRIES_PER_USER]
        )
        cls.objects.filter(user=user).exclude(id__in=ids_to_keep).delete()
        return entry
