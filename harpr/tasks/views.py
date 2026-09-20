import calendar as _cal
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

from .context_processors import CATEGORY_COLORS, URGENT_COLOR
from .forms import SettingsForm, TaskForm
from .models import ActivityLog, Task, UserSettings


# --- helpers -----------------------------------------------------------------

def _log(user, action, task):
    try:
        ActivityLog.record(user, action, task)
    except Exception:
        pass


def _sort_key(t):
    completed_rank = 1 if t.completed else 0
    pri_rank = Task.PRIORITY_RANK.get(t.priority, 99)
    due = t.due_date or timezone.now() + timedelta(days=3650)
    return (completed_rank, pri_rank, due)


# --- Dashboard (Today) -------------------------------------------------------

@login_required
def dashboard(request):
    user = request.user
    now = timezone.localtime()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today = start_today + timedelta(days=1)
    end_tomorrow = start_today + timedelta(days=2)

    todays_pending = sorted(
        Task.objects.filter(
            user=user, completed=False,
            due_date__gte=start_today, due_date__lt=end_today,
        ),
        key=_sort_key,
    )
    someday_pending = sorted(
        Task.objects.filter(user=user, completed=False, due_date__isnull=True),
        key=_sort_key,
    )
    tomorrows_pending = sorted(
        Task.objects.filter(
            user=user, completed=False,
            due_date__gte=end_today, due_date__lt=end_tomorrow,
        ),
        key=_sort_key,
    )

    # Overdue = incomplete tasks whose due date is strictly before today.
    overdue_tasks = sorted(
        Task.objects.filter(
            user=user, completed=False,
            due_date__lt=start_today,
        ),
        key=lambda t: t.due_date or start_today,
    )

    pending_count = Task.objects.filter(user=user, completed=False).count()

    recently_completed = (
        Task.objects.filter(user=user, completed=True)
        .order_by("-completed_at")[:5]
    )

    return render(request, "tasks/dashboard.html", {
        "todays_pending": todays_pending,
        "someday_pending": someday_pending,
        "tomorrows_pending": tomorrows_pending,
        "overdue_tasks": overdue_tasks,
        "pending_count": pending_count,
        "recently_completed": recently_completed,
        "today": now,
    })


# --- Timeline (grouped by date) ----------------------------------------------

@login_required
def timeline(request):
    user = request.user
    today = timezone.localdate()

    qs = Task.objects.filter(user=user)
    by_date = {}
    someday = []
    for t in qs:
        if not t.due_date:
            someday.append(t)
            continue
        d = timezone.localtime(t.due_date).date()
        by_date.setdefault(d, []).append(t)

    def label_for(d):
        delta = (d - today).days
        if delta == 0: return "Today"
        if delta == 1: return "Tomorrow"
        if delta == -1: return "Yesterday"
        return d.strftime("%a, %b ") + str(d.day) + (
            d.strftime(", %Y") if d.year != today.year else ""
        )

    groups = OrderedDict()

    for d in sorted(k for k in by_date if k < today):
        groups[d.isoformat()] = {
            "label": label_for(d), "tasks": sorted(by_date[d], key=_sort_key),
            "is_today": False, "is_overdue": True, "date": d,
        }

    if today in by_date:
        groups[today.isoformat()] = {
            "label": "Today", "tasks": sorted(by_date[today], key=_sort_key),
            "is_today": True, "is_overdue": False, "date": today,
        }
    else:
        groups[today.isoformat()] = {
            "label": "Today", "tasks": [], "is_today": True,
            "is_overdue": False, "date": today, "empty_today": True,
        }

    for d in sorted(k for k in by_date if k > today):
        groups[d.isoformat()] = {
            "label": label_for(d), "tasks": sorted(by_date[d], key=_sort_key),
            "is_today": False, "is_overdue": False, "date": d,
        }

    if someday:
        groups["someday"] = {
            "label": "Someday", "tasks": sorted(someday, key=_sort_key),
            "is_today": False, "is_overdue": False, "date": None,
        }

    return render(request, "tasks/timeline.html", {
        "groups": groups,
        "today": today,
        "total_count": qs.count(),
    })


@login_required
def task_list_redirect(request):
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
            _log(request.user, "created", task)
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
            _log(request.user, "edited", task)
            messages.success(request, "Task updated")
            return redirect(request.POST.get("next") or "timeline")
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {
        "form": form, "is_edit": True, "task": task,
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == "POST":
        task.soft_delete()
        _log(request.user, "deleted", task)
        messages.info(request, "Task moved to trash")
        return redirect(request.POST.get("next") or "timeline")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.completed_at = timezone.now() if task.completed else None
    task.save()
    _log(request.user, "completed" if task.completed else "reopened", task)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        n_pending = Task.objects.filter(user=request.user, completed=False).count()
        return JsonResponse({
            "ok": True,
            "id": task.pk,
            "completed": task.completed,
            "pending_count": n_pending,
        })
    return redirect(request.POST.get("next") or "timeline")


@login_required
@require_POST
def task_move_to_today(request, pk):
    """Push an overdue task's due date to today (keep the time, or set 5pm)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    now = timezone.localtime()
    if task.due_date:
        old = timezone.localtime(task.due_date)
        # Keep the original time of day, move the date to today.
        new_due = now.replace(hour=old.hour, minute=old.minute, second=0, microsecond=0)
    else:
        new_due = now.replace(hour=17, minute=0, second=0, microsecond=0)
    task.due_date = new_due
    task.save(update_fields=["due_date"])
    _log(request.user, "edited", task)
    messages.success(request, "Task moved to today")
    return redirect(request.POST.get("next") or "dashboard")


# --- Trash -------------------------------------------------------------------

@login_required
def trash_list(request):
    qs = Task.all_objects.filter(user=request.user, is_deleted=True).order_by("-deleted_at")
    return render(request, "tasks/trash.html", {"tasks": qs})


@login_required
@require_POST
def trash_restore(request, pk):
    task = get_object_or_404(Task.all_objects, pk=pk, user=request.user, is_deleted=True)
    task.restore()
    _log(request.user, "restored", task)
    messages.success(request, "Task restored")
    return redirect(request.POST.get("next") or "trash_list")


@login_required
@require_POST
def trash_purge(request, pk):
    task = get_object_or_404(Task.all_objects, pk=pk, user=request.user, is_deleted=True)
    title = task.title
    task.delete()
    ActivityLog.objects.create(user=request.user, action="purged", task_title=title[:200])
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


_EASTER = {
    2024: (date(2024, 3, 29), date(2024, 4, 1)),
    2025: (date(2025, 4, 18), date(2025, 4, 21)),
    2026: (date(2026, 4, 3),  date(2026, 4, 6)),
    2027: (date(2027, 3, 26), date(2027, 3, 29)),
    2028: (date(2028, 4, 14), date(2028, 4, 17)),
}


def _first_monday(year, month):
    cal = _cal.Calendar()
    for d in cal.itermonthdates(year, month):
        if d.month == month and d.weekday() == 0:
            return d
    return None


def zambian_holidays(year):
    out = [
        (date(year, 1, 1),   "New Year's Day"),
        (date(year, 3, 8),   "Women's Day"),
        (date(year, 3, 12),  "Youth Day"),
        (date(year, 5, 1),   "Labour Day"),
        (date(year, 5, 25),  "Africa Day"),
        (date(year, 10, 24), "Independence Day"),
        (date(year, 12, 25), "Christmas Day"),
        (date(year, 12, 26), "Boxing Day"),
    ]
    if year in _EASTER:
        gf, em = _EASTER[year]
        out += [(gf, "Good Friday"), (em, "Easter Monday")]
    heroes = _first_monday(year, 7)
    if heroes:
        out.append((heroes, "Heroes' Day"))
        out.append((heroes + timedelta(days=1), "Unity Day"))
    farmers = _first_monday(year, 8)
    if farmers:
        out.append((farmers, "Farmers' Day"))
    out.sort(key=lambda x: x[0])
    return out


@login_required
def calendar_events(request):
    """Return events (holidays) + per-day dot info for the calendar."""
    user = request.user
    settings_obj = UserSettings.for_user(user)

    qs = Task.objects.filter(user=user, due_date__isnull=False)

    per_day = {}
    for t in qs:
        iso = timezone.localtime(t.due_date).date().isoformat()
        slot = per_day.setdefault(iso, {"urgent": False, "cat_rank": 99, "cat": None})
        if t.priority == "urgent":
            slot["urgent"] = True
        r = Task.CATEGORY_RANK.get(t.category, 99)
        if r < slot["cat_rank"]:
            slot["cat_rank"] = r
            slot["cat"] = t.category

    dots = {}
    for d, slot in per_day.items():
        if slot["urgent"]:
            dots[d] = {"cls": "dot-urgent", "color": URGENT_COLOR}
        elif slot["cat"]:
            dots[d] = {"cls": "dot-" + slot["cat"], "color": CATEGORY_COLORS[slot["cat"]]}

    events = []
    if settings_obj.show_public_holidays:
        today = timezone.localdate()
        for y in {today.year, today.year + 1}:
            for d, name in zambian_holidays(y):
                events.append({
                    "title": name,
                    "start": d.isoformat(),
                    "allDay": True,
                    "display": "block",
                    "classNames": ["holiday-event"],
                    "backgroundColor": "#9ca3af",
                    "borderColor": "#9ca3af",
                    "textColor": "#ffffff",
                    "editable": False,
                    "extendedProps": {"holiday": True},
                })
    return JsonResponse({"events": events, "dots": dots})



@login_required
def calendar_day_tasks(request, year, month, day):
    try:
        target = date(int(year), int(month), int(day))
    except ValueError:
        raise Http404("Bad date")

    tz = timezone.get_current_timezone()
    start = datetime.combine(target, datetime.min.time(), tzinfo=tz)
    end = start + timedelta(days=1)

    qs = sorted(
        Task.objects.filter(user=request.user, due_date__gte=start, due_date__lt=end),
        key=_sort_key,
    )
    settings_obj = UserSettings.for_user(request.user)
    cat_labels = settings_obj.category_labels()

    tasks = []
    for t in qs:
        tasks.append({
            "id": t.id,
            "title": t.title,
            "category": cat_labels.get(t.category, t.get_category_display()),
            "category_key": t.category,
            "priority": t.get_priority_display(),
            "priority_key": t.priority,
            "completed": t.completed,
            "time": timezone.localtime(t.due_date).strftime("%H:%M") if t.due_date else "",
            "edit_url": f"/tasks/{t.id}/edit/",
            "toggle_url": f"/tasks/{t.id}/toggle/",
        })

    holidays_today = []
    if settings_obj.show_public_holidays:
        for d, name in zambian_holidays(target.year):
            if d == target:
                holidays_today.append(name)

    label = target.strftime("%A, %B ") + str(target.day) + target.strftime(", %Y")
    return JsonResponse({
        "date": target.isoformat(),
        "label": label,
        "tasks": tasks,
        "holidays": holidays_today,
    })


# --- Reminders ---------------------------------------------------------------

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
            local = timezone.localtime(t.due_date)
            due.append({
                "id": t.id,
                "title": t.title,
                "due": local.strftime("%H:%M, %b ") + str(local.day),
                "remind_minutes_before": t.remind_minutes_before,
            })
    return JsonResponse({"reminders": due, "checked_at": now.isoformat()})


# --- CSV export --------------------------------------------------------------

@login_required
def timeline_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="harpr_tasks.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Title", "Description", "Due date", "Duration (minutes)",
        "Category", "Priority", "Completed", "Completed at", "Reminder (min before)",
    ])
    cat_labels = UserSettings.for_user(request.user).category_labels()
    for t in Task.objects.filter(user=request.user).order_by("due_date"):
        writer.writerow([
            t.title,
            t.description,
            timezone.localtime(t.due_date).strftime("%Y-%m-%d %H:%M") if t.due_date else "",
            t.duration_minutes or "",
            cat_labels.get(t.category, t.get_category_display()),
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


# --- Activity log ------------------------------------------------------------

@login_required
def activity_log_view(request):
    entries = ActivityLog.objects.filter(user=request.user).order_by("-created_at")[:30]
    return render(request, "tasks/activity_log.html", {
        "entries": entries,
    })
