from django.contrib import admin
from .models import Task, TimeLog, UserSettings


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "priority", "completed", "due_date", "is_deleted")
    list_filter = ("category", "priority", "completed", "is_deleted")
    search_fields = ("title", "description")


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "minutes", "logged_at")
    list_filter = ("logged_at",)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "notifications_enabled")
