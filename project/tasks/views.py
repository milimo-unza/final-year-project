import csv
from collections import OrderedDict
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import SettingsForm, TaskForm
from .models import Task, UserSettings


# --- Dashboard ---------------------------------------------------------------

@login_required
def dashboard(request):
    """Today page: pending tasks (sorted by due time) + recently completed."""
    user = request.user
    now = timezone.localtime()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    todays_pending = list(
        Task.objects.filter(
            user=user,
            completed=False,
            due_date__gte=start_of_day,
            due_date__lt=end_of_day,
        ).order_by("due_date")
    )

    pending_count = Task.objects.filter(user=user, completed=False).count()

    recently_completed = (
        Task.objects.filter(user=user, completed=True)
        .order_by("-completed_at")[:5]
    )

    return render(request, "tasks/dashboard.html", {
        "todays_pending": todays_pending,
        "pending_count": pending_count,
        "recently_completed": recently_completed,
        "today": now,
    })


# --- Timeline (grouped by date — main task view) -----------------------------

@login_required
def timeline(request):
    """Group tasks by due date for the user. Replaces the old task list."""
    user = request.user
    today = timezone.localdate()

    qs = Task.objects.filter(user=user).order_by("due_date", "completed", "title")

    groups = OrderedDict()  # date_key -> {"label": str, "tasks": [...], "is_today": bool}
    upcoming = {}   # date -> tasks (today / future)
    past = {}       # date -> tasks (overdue)
    someday = []

    for t in qs:
        if not t.due_date:
            someday.append(t)
            continue
        d = timezone.localtime(t.due_date).date()
        bucket = upcoming if d >= today else past
        bucket.setdefault(d, []).append(t)

    def label_for(d):
        delta = (d - today).days
        if delta == 0:
            return "Today"
        if delta == 1:
            return "Tomorrow"
        if delta == -1:
            return "Yesterday"
        if 1 < delta <= 7:
            return d.strftime("%a, %b ") + str(d.day)
        if delta < -1 and delta >= -7:
            return d.strftime("%a, %b ") + str(d.day)
        return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")

    # Today + future first (ascending)
    for d in sorted(upcoming.keys()):
        groups[d.isoformat()] = {
            "label": label_for(d),
            "tasks": upcoming[d],
            "is_today": d == today,
            "is_overdue": False,
            "date": d,
        }

    # Then past (overdue) — most recent first
    for d in sorted(past.keys(), reverse=True):
        groups[d.isoformat()] = {
            "label": label_for(d),
            "tasks": past[d],
            "is_today": False,
            "is_overdue": True,
            "date": d,
        }

    if someday:
        groups["someday"] = {
            "label": "Someday",
            "tasks": someday,
            "is_today": False,
            "is_overdue": False,
            "date": None,
        }

    return render(request, "tasks/timeline.html", {
        "groups": groups,
        "today": today,
        "total_count": qs.count(),
    })


@login_required
def task_list_redirect(request):
    """Old /tasks/ path now redirects to the new Timeline."""
    return redirect("timeline")


# --- Task CRUD ---------------------------------------------------------------

@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, "Task added")
            return redirect(request.POST.get("next") or "timeline")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form, "is_edit": False})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated")
            return redirect(request.POST.get("next") or "timeline")
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {
        "form": form,
        "is_edit": True,
        "task": task,
    })


@login_required
def task_delete(request, pk):
    """Soft delete: move task to trash bin. Always POST (modal-driven)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        task.soft_delete()
        messages.info(request, "Task moved to trash")
        return redirect(request.POST.get("next") or "timeline")
    # Fallback: simple confirmation page (modal is preferred).
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.completed_at = timezone.now() if task.completed else None
    task.save()
    return redirect(request.POST.get("next") or "timeline")


# --- Trash bin ---------------------------------------------------------------

@login_required
def trash_list(request):
    qs = Task.all_objects.filter(user=request.user, is_deleted=True).order_by("-deleted_at")
    return render(request, "tasks/trash.html", {"tasks": qs})


@login_required
@require_POST
def trash_restore(request, pk):
    task = get_object_or_404(Task.all_objects, pk=pk, user=request.user, is_deleted=True)
    task.restore()
    messages.success(request, "Task restored")
    return redirect("trash_list")


@login_required
@require_POST
def trash_purge(request, pk):
    task = get_object_or_404(Task.all_objects, pk=pk, user=request.user, is_deleted=True)
    task.delete()
    messages.info(request, "Task permanently deleted")
    return redirect("trash_list")


@login_required
@require_POST
def trash_clear(request):
    Task.all_objects.filter(user=request.user, is_deleted=True).delete()
    messages.info(request, "Trash cleared")
    return redirect("trash_list")


# --- Calendar ----------------------------------------------------------------

@login_required
def calendar(request):
    return render(request, "tasks/calendar.html")


CATEGORY_COLORS = {
    "work":     "#10b981",
    "study":    "#71717a",
    "personal": "#a1a1aa",
    "health":   "#3f3f46",
}


@login_required
def calendar_events(request):
    qs = Task.objects.filter(user=request.user, due_date__isnull=False)
    events = []
    for t in qs:
        evt = {
            "id": t.id,
            "title": t.title,
            "start": t.due_date.isoformat(),
            "color": CATEGORY_COLORS.get(t.category, "#71717a"),
            "extendedProps": {
                "category": t.get_category_display(),
                "priority": t.get_priority_display(),
                "completed": t.completed,
            },
        }
        end = t.end_time()
        if end:
            evt["end"] = end.isoformat()
        events.append(evt)
    return JsonResponse(events, safe=False)


@login_required
def calendar_day_tasks(request, year, month, day):
    """Return tasks for a single day as JSON for the calendar day-modal."""
    try:
        target = date(int(year), int(month), int(day))
    except ValueError:
        raise Http404("Bad date")

    tz = timezone.get_current_timezone()
    start = datetime.combine(target, datetime.min.time(), tzinfo=tz)
    end = start + timedelta(days=1)

    qs = (
        Task.objects.filter(user=request.user, due_date__gte=start, due_date__lt=end)
        .order_by("completed", "due_date")
    )
    tasks = []
    for t in qs:
        tasks.append({
            "id": t.id,
            "title": t.title,
            "category": t.get_category_display(),
            "priority": t.get_priority_display(),
            "completed": t.completed,
            "time": timezone.localtime(t.due_date).strftime("%H:%M") if t.due_date else "",
            "edit_url": f"/tasks/{t.id}/edit/",
            "toggle_url": f"/tasks/{t.id}/toggle/",
        })
    return JsonResponse({
        "date": target.isoformat(),
        "label": target.strftime("%A, %B ") + str(target.day) + target.strftime(", %Y"),
        "tasks": tasks,
    })


# --- Reminders endpoint ------------------------------------------------------

@login_required
def reminders_due(request):
    now = timezone.now()
    horizon = now + timedelta(seconds=60)
    qs = Task.objects.filter(
        user=request.user,
        completed=False,
        due_date__isnull=False,
        remind_minutes_before__gt=0,
    )
    due = []
    for t in qs:
        remind_at = t.due_date - timedelta(minutes=t.remind_minutes_before)
        if now <= remind_at <= horizon:
            due.append({
                "id": t.id,
                "title": t.title,
                "due": timezone.localtime(t.due_date).strftime("%H:%M, %b ") + str(timezone.localtime(t.due_date).day),
                "remind_minutes_before": t.remind_minutes_before,
            })
    return JsonResponse({"reminders": due, "checked_at": now.isoformat()})


# --- Tasks CSV export --------------------------------------------------------

@login_required
def timeline_export_csv(request):
    """Download all tasks for the user as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="harpr_tasks.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Title", "Description", "Due date", "Duration (minutes)",
        "Category", "Priority", "Completed", "Completed at", "Reminder (min before)",
    ])
    for t in Task.objects.filter(user=request.user).order_by("due_date"):
        writer.writerow([
            t.title,
            t.description,
            timezone.localtime(t.due_date).strftime("%Y-%m-%d %H:%M") if t.due_date else "",
            t.duration_minutes or "",
            t.get_category_display(),
            t.get_priority_display(),
            "yes" if t.completed else "no",
            timezone.localtime(t.completed_at).strftime("%Y-%m-%d %H:%M") if t.completed_at else "",
            t.remind_minutes_before or "",
        ])
    return response


# --- Settings ----------------------------------------------------------------

@login_required
def settings_view(request):
    settings_obj = UserSettings.for_user(request.user)
    if request.method == "POST":
        form = SettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated")
            return redirect("settings")
    else:
        form = SettingsForm(instance=settings_obj)
    return render(request, "tasks/settings.html", {
        "form": form,
        "settings": settings_obj,
    })
