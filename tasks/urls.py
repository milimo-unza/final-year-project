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
    path("tasks/<int:pk>/move-to-today/", views.task_move_to_today, name="task_move_to_today"),

    # Quick add
    path("tasks/quick-add/", views.quick_add, name="quick_add"),

    # Time logging
    path("tasks/<int:pk>/log-time/", views.log_time, name="log_time"),
    path("time-logs/<int:pk>/delete/", views.delete_time_log, name="delete_time_log"),

    # Calendar
    path("calendar/", views.calendar, name="calendar"),
    path("calendar/events/", views.calendar_events, name="calendar_events"),
    path("calendar/day/<int:year>-<int:month>-<int:day>/",
         views.calendar_day_tasks, name="calendar_day_tasks"),

    # Activity log
    path("activity-log/", views.activity_log_view, name="activity_log"),
]
