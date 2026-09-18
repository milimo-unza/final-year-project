from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Main task view
    path("timeline/", views.timeline, name="timeline"),
    path("timeline/export.csv", views.timeline_export_csv, name="timeline_export_csv"),

    # Backward-compat
    path("tasks/", views.task_list_redirect, name="task_list"),

    # Task CRUD
    path("tasks/new/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:pk>/toggle/", views.task_toggle, name="task_toggle"),

    # Trash
    path("trash/", views.trash_list, name="trash_list"),
    path("trash/<int:pk>/restore/", views.trash_restore, name="trash_restore"),
    path("trash/<int:pk>/purge/", views.trash_purge, name="trash_purge"),
    path("trash/clear/", views.trash_clear, name="trash_clear"),

    # Calendar
    path("calendar/", views.calendar, name="calendar"),
    path("calendar/events/", views.calendar_events, name="calendar_events"),
    path("calendar/day/<int:year>-<int:month>-<int:day>/",
         views.calendar_day_tasks, name="calendar_day_tasks"),

    # Reminders
    path("reminders/due/", views.reminders_due, name="reminders_due"),

    # Settings & activity log
    path("settings/", views.settings_view, name="settings"),
    path("activity-log/", views.activity_log_view, name="activity_log"),
]
