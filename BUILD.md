# Build Document — Harpr (Time & Activity Planner)

**Author**: Milimo Kasamba Mukkuli
**Programme**: BSc Computer Science, University of Zambia
**Supervisor**: Prof. J. Phiri
**Project duration**: 16 weeks core build + a v1.1 polish sprint

This document is my honest account of how I built Harpr. The first
seven chapters cover the original eight-week build (when the project was
still codenamed *Cosmos AI Planner*). Chapter 8 covers the v1.1 sprint that
rebranded the app to **Harpr** and added twelve new features after my
supervisor's mid-project review.

---

## Week 1 — Setting up Django and authentication

I started by installing Python 3.11 and creating a fresh Django 5.2 project
called `timeplanner`. I picked Django because the built-in admin, auth, and
ORM are exactly what a one-person project needs — no third-party packages to
keep up with. I went with SQLite because it ships with Python and a one-file
database is easy to back up and submit with my report.

```bash
pip install Django whitenoise
django-admin startproject timeplanner .
python manage.py startapp accounts
python manage.py startapp tasks
```

Authentication came next. Instead of writing my own user system I used
`django.contrib.auth` — `LoginView`, `LogoutView`, and a thin custom
`register` view that wraps `UserCreationForm` and adds an email field.

```python
# accounts/forms.py
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
```

Routing the three URLs took five minutes:

```python
# accounts/urls.py
path("login/",    auth_views.LoginView.as_view(template_name="accounts/login.html"),  name="login"),
path("logout/",   auth_views.LogoutView.as_view(next_page="login"),                   name="logout"),
path("register/", views.register,                                                     name="register"),
```

I set `LOGIN_URL`, `LOGIN_REDIRECT_URL`, and `LOGOUT_REDIRECT_URL` in settings
so unauthenticated users always end up on the login page.

**Challenge:** my first login template was the default Django one and looked
ugly. I parked the styling for week 6 and pressed on with functionality.

---

## Week 2 — The Task model and CRUD

Two simple models. No fancy relationships beyond a `ForeignKey` to `User`
and one from `TimeLog` to `Task`.

```python
# tasks/models.py
class Task(models.Model):
    CATEGORY_CHOICES = [("work","Work"),("study","Study"),
                        ("personal","Personal"),("health","Health")]
    PRIORITY_CHOICES = [("high","High"),("medium","Medium"),("low","Low")]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date    = models.DateTimeField(null=True, blank=True)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="work")
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    completed   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
```

For CRUD I used **function-based views** (FBVs) — they read top-to-bottom
which is easier when explaining the project to my supervisor. Each view is
guarded with `@login_required` and starts with
`Task.objects.filter(user=request.user, ...)` so users only see their own data.

```python
@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form})
```

Filtering pending vs completed is just a query-string check (`?status=pending`)
so I didn't have to invent a routing scheme.

**Challenge:** `due_date` as a `DateTimeField` initially didn't pre-populate the
edit form correctly — the HTML5 `datetime-local` input expects
`YYYY-MM-DDTHH:MM`. Fixed by setting both `widget format` and
`input_formats` on the form field.

---

## Week 3 — Calendar with FullCalendar.js

I needed a monthly view but didn't want to build it from scratch.
**FullCalendar 6** is free, has a nice JSON-feed pattern, and loads from a CDN
so I don't have to manage another build tool.

The page is plain HTML with a `<div id="calendar"></div>`. Initialisation lives
in `static/js/calendar.js`:

```javascript
var cal = new FullCalendar.Calendar(el, {
  initialView: 'dayGridMonth',
  events: '/calendar/events/',  // Django JSON feed
  ...
});
cal.render();
```

The Django side is a single view that returns a list of dicts:

```python
@login_required
def calendar_events(request):
    qs = Task.objects.filter(user=request.user, due_date__isnull=False)
    events = []
    for t in qs:
        events.append({
            "id": t.id, "title": t.title,
            "start": t.due_date.isoformat(),
            "color": CATEGORY_COLORS[t.category],
            "url": f"/tasks/{t.id}/edit/",
        })
    return JsonResponse(events, safe=False)
```

Each task is colour-coded by category. Clicking an event jumps to its edit page.

**Challenge:** my first attempt used the FullCalendar npm package — I gave up
quickly when I realised I'd need a bundler. The CDN version dropped in cleanly.

---

## Week 4 — Time tracking (TimeLog)

`TimeLog` is even simpler than `Task`:

```python
class TimeLog(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="time_logs")
    task      = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_logs")
    minutes   = models.PositiveIntegerField()
    note      = models.CharField(max_length=200, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
```

The form has two number inputs (Hours and Minutes), and I combine them in
`clean()` so the model still stores a single integer:

```python
def clean(self):
    cleaned = super().clean()
    h = cleaned.get("hours") or 0
    m = cleaned.get("minutes_part") or 0
    total = h * 60 + m
    if total <= 0:
        raise forms.ValidationError("Please enter a duration greater than zero.")
    cleaned["minutes"] = total
    return cleaned
```

The Timeline page is the chronological list of these logs.
The dashboard's "time logged today" stat uses `Sum("minutes")` over today's logs.

**Challenge:** I forgot to scope the `task` dropdown to the current user, so
the log form was showing every task in the database. Fixed by overriding the
form's `__init__` to take a `user` argument.

---

## Week 5 — Charts (Chart.js)

The analytics page has three charts. Each gets its data from the **same**
context dict, serialised with Django's `json_script` template tag:

```html
{{ chart_data|json_script:"chart-data" }}
<script>
var data = JSON.parse(document.getElementById('chart-data').textContent);
new Chart(document.getElementById('lineChart'), { ... });
</script>
```

Aggregations happen server-side in the view, using Django's ORM:

```python
# Pie: minutes per category
cat_rows = (TimeLog.objects.filter(user=user)
            .values("task__category")
            .annotate(total=Sum("minutes")))

# Line: last 7 days of minutes
for i in range(6, -1, -1):
    day_start = start_of_today - timedelta(days=i)
    total = TimeLog.objects.filter(user=user,
        logged_at__gte=day_start,
        logged_at__lt=day_start + timedelta(days=1)
    ).aggregate(s=Sum("minutes"))["s"] or 0
```

I deliberately kept the bar chart at completed-vs-pending per category rather
than a percentage, so an empty category shows zero (rather than a misleading
0% with no context).

**Challenge:** my first version of the daily line chart showed weeks in the
wrong order because I was sorting strings. Fixed by building the labels from
the same `datetime` objects used in the query.

---

## Week 6 — Design (the "Mono Grid" theme)

Up to this point everything looked like default browser HTML. I'd been keeping
my eye on a clean monochromatic dashboard look — hairline borders, monospace
numerals, a single accent colour — so I built it as one CSS file.

```css
:root {
  --bg: hsl(0 0% 100%);
  --fg: hsl(240 6% 10%);
  --border: hsl(240 6% 90%);
  --accent: hsl(161 94% 30%);   /* emerald-600 */
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
  ...
}
[data-theme="dark"] { --bg: hsl(240 10% 4%); ... }
```

Every component (KPI grid, task row, sidebar, button, form input) consumes
those variables, so dark mode is just a matter of overriding the same handful
of CSS custom properties under `[data-theme="dark"]`. The toggle lives in the
sidebar footer:

```javascript
btn.addEventListener('click', function () {
  var cur  = document.documentElement.getAttribute('data-theme');
  var next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('cosmos-theme', next);
});
```

A small inline script in `<head>` reads `localStorage` *before* paint to avoid
the flash-of-wrong-theme on every refresh.

I used **Inter** for body text and **JetBrains Mono** for numbers and metadata
— both via Google Fonts, no `npm` involved.

**Challenge:** my first dashboard layout used `<table>` and rendered fine on
my laptop but cramped on my phone. Refactored everything to CSS Grid with
`grid-template-columns: repeat(4, 1fr)` and a media query that collapses to two
columns under 880px.

---

## Week 7 — Testing and debugging

I wrote a small smoke-test script that logs in as a fixture user and `GET`s
every URL, asserting status 200:

```python
c = Client()
c.login(username='milimo', password='cosmos123')
for u in ['/', '/tasks/', '/calendar/', '/calendar/events/',
          '/log/', '/timeline/', '/analytics/']:
    assert c.get(u).status_code == 200
```

Bugs I found and fixed:

1. **`due_date` was not displayed in the edit form** — wrong widget format
   string. Fixed in `tasks/forms.py`.
2. **The dashboard's "time logged today" KPI tried to do arithmetic in
   templates** (Django templates don't support `//` and `%`). I moved the
   formatting to plain "X min" rather than splitting into hours/minutes.
3. **CSRF blocked POST from the Replit preview iframe** — added
   `https://*.replit.dev` to `CSRF_TRUSTED_ORIGINS`.
4. **The preview iframe blocked the page** because Django sets
   `X-Frame-Options: DENY` by default. I removed `XFrameOptionsMiddleware`
   from `MIDDLEWARE`. (This is fine for development; in production we'd add
   the middleware back and use `@xframe_options_exempt` only where needed.)

I also seeded a few tasks and time logs so my screenshots in the report show
realistic data instead of empty states.

---

## Other challenges and what I'd do differently

**Picking a CSS framework.** I started with Bootstrap, replaced it with
Tailwind CDN, and finally dropped both because the design I wanted (hairline
borders, mono numerals, emerald accent) was easier to maintain as plain CSS
custom properties. About 600 lines of CSS in one file is a lot less than the
megabyte of utility classes Tailwind would have shipped.

**Time zones.** I set `TIME_ZONE = "Africa/Lusaka"` and `USE_TZ = True`. The
calendar, timeline, and "today" filters all behave naturally as a result.

**Future work I deliberately skipped at v1.0:**

- An AI assistant powered by Gemini for chat-based planning.
- WhatsApp reminders via Twilio.
- A mobile app.

Each of those is enough work for its own dissertation.

---

## Week 8 — The Harpr v1.1 sprint (rebrand + 12 features)

After the mid-project demo, my supervisor pointed out that "Cosmos AI
Planner" promised an AI it didn't ship, and that the app — although tidy —
was missing a few things he expected from a planner. I agreed, and spent
the polish week doing both: a rebrand and a focused feature pass.

### The rebrand: Cosmos AI Planner → Harpr

The new name had to be:

- short (one word, four-to-six letters),
- not pretending to be something it isn't (no "AI"),
- evocative of *time* and *rhythm*.

I landed on **Harpr** — a misspelling of *harp*, which felt right because
each task is a string in your day's chord. The tagline became
**"Time & Activity Planner"** and the favicon became a simple emerald harp
SVG (six strings, drawn in 24×24 viewport space).

Because the brand string appears in dozens of templates, I added a
context processor so every template gets `APP_NAME` and `APP_TAGLINE` for
free:

```python
# tasks/context_processors.py
def branding(_request):
    return {"APP_NAME": "Harpr", "APP_TAGLINE": "Time & Activity Planner"}
```

That single change let me delete every hard-coded "Cosmos" string in the
codebase and replace it with `{{ APP_NAME }}`.

### The 12 features

I scoped the sprint as a numbered checklist so I'd know when I was done:

| # | Feature                            | Where it lives                                |
|---|------------------------------------|-----------------------------------------------|
| 1 | Browser notifications + reminders  | `harpr.js`, `views.reminders_due`             |
| 2 | Task duration field                | `Task.duration_minutes`, `Task.end_time()`    |
| 3 | Mobile-responsive layout           | `cosmos.css` `@media (max-width: 720px)`      |
| 4 | 115% base font size                | `html { font-size: 115%; }`                   |
| 5 | Modal popups (New task / Log time) | `harpr.js`, `_task_form_inner.html`           |
| 6 | Search & filter on Tasks           | `task_list.html`, `views.task_list`           |
| 7 | Completed archive                  | filter `status=completed` + `completed_at`    |
| 8 | Soft-delete trash                  | `Task.is_deleted` + `TaskManager`             |
| 9 | Pomodoro timer                     | dashboard card + `harpr.js` `Pomodoro` IIFE   |
|10 | Keyboard shortcuts                 | `harpr.js` global `keydown` handler           |
|11 | Quick "done" button                | inline `<form>` per row in `task_list.html`   |
|12 | CSV export of timeline             | `views.timeline_export_csv`                   |

A few of these were a single afternoon's work; others bled into each other.
Notes on the trickier ones:

**Reminders without a worker.** I didn't want to add Celery or Redis just
to fire reminders. Instead the front-end polls a small endpoint:

```python
# tasks/views.py
@login_required
def reminders_due(request):
    now = timezone.now()
    window_end = now + timezone.timedelta(seconds=60)
    qs = (Task.objects
          .filter(user=request.user, completed=False,
                  remind_minutes_before__gt=0,
                  due_date__isnull=False)
          .annotate(remind_at=ExpressionWrapper(
              F("due_date") - F("remind_minutes_before") * timedelta(minutes=1),
              output_field=DateTimeField(),
          ))
          .filter(remind_at__gte=now, remind_at__lte=window_end))
    return JsonResponse({"reminders": [...]})
```

`harpr.js` calls it every 60 s and uses `sessionStorage` to dedupe so a
single reminder doesn't fire twice. The honest limitation — and the one I
called out in the README — is that this only works while a tab is open.

**Soft delete.** I added `is_deleted` and `deleted_at` to `Task`, plus a
custom manager that filters them out by default:

```python
class TaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Task(models.Model):
    ...
    objects = TaskManager()
    all_objects = models.Manager()
```

The `delete()` view now calls `task.soft_delete()`; the trash view uses
`Task.all_objects.filter(is_deleted=True)`. Permanent delete is a separate
endpoint that calls `super().delete()` directly. This caught me out once —
I forgot to update the `TimeLog` cascade and ended up with orphan logs
pointing at "ghost" tasks. Now permanent delete cascades, restore preserves.

**Modals over full pages.** I really didn't want to bring in HTMX or Alpine
for one feature. The pattern is fifty lines of vanilla JS in `harpr.js`:

1. Click a button with `data-modal-fetch="/tasks/new/"`.
2. `fetch()` the URL, parse the response HTML, lift `.form-grid` out.
3. Open a `<dialog>`-style overlay containing that form.
4. Intercept submit, `POST` via `fetch`, and on `2xx` reload the page; on
   `400` swap the form body with the server-rendered errors.

The same view handles both regular full-page renders and the modal
fetch, because the modal just yanks the form fragment out of the
already-rendered template.

**Pomodoro.** A 25-minute countdown using `setInterval`, with a single
`OscillatorNode` beep at the end. Roughly 60 lines of JS, no library.

### Process notes

- I built the new features behind a single migration
  (`0002_harpr_features`) so reviewers see one tidy diff for the data
  layer.
- I deliberately kept the look-and-feel — the emerald accent and the
  hairline borders carried over without changes. Only the brand mark
  (top-left of the sidebar) moved from a gradient block to the harp SVG.
- After the sprint I re-ran the smoke-test script from week 7 and added
  three new endpoints to it: `/trash/`, `/settings/`, `/timeline/export.csv`.
  All 200 OK on first try, which felt good.

### What's still on the wish-list (Future work)

- True push notifications (Service Worker + VAPID) so reminders fire when
  the tab is closed.
- AI assistant via Gemini (the original "Cosmos" promise — postponed, not
  abandoned).
- WhatsApp reminders via Twilio.
- Recurring tasks (daily / weekly / monthly).
- A native mobile app.

---

## Acknowledgements

Thanks to **Prof. J. Phiri** for weekly check-ins, the **Department of
Computer Science** at UNZA, and the open-source maintainers of Django,
Chart.js, and FullCalendar.

---

## Week 17 — v1.2 polish sprint (the "make it actually feel finished" pass)

After the v1.1 demo my supervisor's main feedback was: *"The bones are good,
now declutter."* He pointed out that I had two parallel concepts in the app
(Tasks vs Time Logs) and most of my screens were trying to display both. The
v1.2 sprint was about leaning fully into **tasks** as the primary unit of
work, and clearing out everything that wasn't pulling its weight.

### Decisions I made up front

- **Keep the `TimeLog` table in the database** — but remove all of its UI.
  This way no data is lost, and if I (or a future maintainer) want to bring
  time-logging back, the model is still there. I removed the form, the
  views, the URL routes, and the templates, but left `models.TimeLog`,
  `admin.TimeLogAdmin`, and the `0001_initial` migration untouched.
- **Keep "Mono Grid"** as the visual identity. The whole point of v1.2 is
  that the app gets *quieter*, not louder.
- **Target 120% font-size everywhere** so the desktop and mobile reading
  experience are consistent.

### What I actually built

1. **Background and type scale** — switched the page background to the warm
   `#f5f5f0` paper colour (with `--card` and `--muted-bg` adjusted to match)
   and bumped `html { font-size: 120% }` for both desktop and mobile. The UI
   reads bigger without me having to touch any individual widget.
2. **Sidebar slimmed** — the nav is now just **Today / Timeline / Calendar
   / Trash / Settings**. No "Log time" modal trigger, no "Analytics" link.
   The mobile bottom-nav drops to four buttons (Today / Timeline / Calendar
   / Settings) so the thumb-targets are bigger.
3. **Dashboard rebuild**:
   - Single **Pending KPI** at the top (the only number that matters).
   - **Today list** is pending-only, sorted by due time. The list is
     wrapped in a `.task-scroll` container with `max-height` so it shows
     about 7 rows on desktop and 5 on mobile before scrolling — you don't
     need to scroll the page to see everything else.
   - Removed "Next 7 days"; added **Recently completed** (the last five
     completed tasks with their completion timestamps). It's a tiny win-list
     and people genuinely like seeing it.
   - The Pomodoro card now has a **⚙ Settings** button. Clicking it opens a
     modal with a number input (1–180 min) that shows a friendly hint
     ("1hr 56min") for any value over an hour. The choice persists in
     `localStorage`. I removed the "Linked task" picker — without time
     logging it had no purpose.
4. **Timeline rebuild** — this used to be the time-log history; now it's
   **the main task view, grouped by due date**. The grouping order is
   Today → Tomorrow → next few weekdays → future dates → "Earlier"
   (overdue, most-recent-first) → "Someday" (no date). Each group shows
   its own row count. Overdue tasks **stay on their original date** rather
   than getting silently moved to today, which my supervisor felt was much
   more honest.
5. **CSV export** now writes `harpr_tasks.csv` with one row per task and
   the columns Title / Description / Due date / Duration / Category /
   Priority / Completed / Completed at / Reminder.
6. **Calendar dots + day-click modal**:
   - Replaced the per-day event chips with a single **green dot** placed by
     `dayCellDidMount` on any cell whose date appears in the events list.
   - Wired up `dateClick` (and `eventClick`) to fetch
     `/calendar/day/<y>-<m>-<d>/` and pop a modal with the day's tasks,
     each with its own toggle button and edit link.
7. **Delete confirmation modal** — every Delete button (on Timeline and in
   the edit modal) carries `data-delete-task="…"`. A global click handler
   in `harpr.js` opens a small dialog ("Move *X* to the Trash?") and POSTs
   the form for you. The full-page `task_confirm_delete.html` is kept as a
   fallback for non-JS users.
8. **Toast notifications** — I added a fixed `#toast-container` to
   `base.html` and a `toast(msg, kind)` helper in `harpr.js`. Two pathways
   feed it:
   - On every page load, the JS scans `[data-messages] .message` for any
     server-rendered Django messages and pops them as toasts.
   - For modal-form submits, the JS queues the success toast in
     `sessionStorage` *before* reloading the page, then drains the queue
     after reload. The result is that "Task added" / "Task updated" /
     "Task moved to trash" all show as a small notification in the corner
     instead of as a banner inside the page.
9. **Natural-language date parser on the title field** — added the
   chrono-node 2.7.5 CDN script to `base.html` and a small helper in
   `harpr.js` (`attachChronoToForm`) that runs after the task modal loads.
   It debounces input on the title field, parses the text with `chrono`,
   and (only if the user hasn't manually set a date) fills the
   `datetime-local` input. A small green hint shows the detected phrase
   and the parsed timestamp, with a one-click **clear** link.
10. **Notifications-button fix** — in v1.1 the Settings page had a
    "Request browser permission" button but the `click` listener was
    declared inside an immediately-invoked function that referenced
    `btn.disabled = true` only on the unsupported branch, and the
    listener wasn't always attached on first paint. I rewrote the script
    to wait for `DOMContentLoaded`, double-checked the button exists,
    pop a toast on grant/deny, and added an inline note in the card body
    explaining that mobile notifications work best on Android Chrome and
    on iOS only when added to the Home Screen.
11. **Dark-mode toggle in Settings** — a checkbox that simply mirrors
    `data-theme` on `<html>` and persists `cosmos-theme` in
    `localStorage`. The sidebar's ☀ / ☾ button still works the same.
12. **Cleanup** — deleted the now-orphaned templates
    (`analytics.html`, `task_list.html`, `timelog_form.html`,
    `_timelog_form_inner.html`), removed `TimeLogForm` from `forms.py`,
    and pruned all references to `log_time` / `analytics` from the
    sidebar, the dashboard, and the keyboard-shortcut help.

### Files I touched or replaced

- `tasks/views.py` — rewrote `dashboard`, replaced the old `timeline` view
  with the new date-grouped task view, removed `analytics` and `log_time`,
  added `task_list_redirect` and `calendar_day_tasks`.
- `tasks/urls.py` — removed `/log/`, `/analytics/`, the old `/timeline/`
  route; added `/timeline/`, `/timeline/export.csv`, `/calendar/day/...`,
  and a backward-compat redirect for `/tasks/`.
- `tasks/forms.py` — removed `TimeLogForm`; added the `data-chrono="1"`
  attribute to the task title input so the JS knows where to attach.
- `static/css/cosmos.css` — new `--bg` and friends, 120% font-size both
  desktop and mobile, plus brand-new sections for `.timeline-group`,
  `.task-scroll`, calendar `.has-tasks` dot, `#toast-container`,
  `.chrono-hint`, `.pomodoro-settings-btn`, and the delete-modal styling.
- `static/js/harpr.js` — full rewrite. Now owns toasts, modal management,
  delete-modal, day-tasks modal, chrono-node integration, and reminder
  polling. The keyboard-shortcut handler dropped `L` and `A` and added
  `D` for the dashboard.
- `static/js/calendar.js` — switched to `dayCellDidMount`-based dots,
  added `dateClick` → day-tasks modal.
- `templates/base.html` — new sidebar, new mobile nav, new modals
  (delete, day-tasks, pomodoro settings, shortcuts) and the chrono-node
  CDN script tag.
- `tasks/templates/tasks/dashboard.html` — rewrite (single KPI,
  scrollable Today list, Pomodoro w/ settings, Recently completed).
- `tasks/templates/tasks/timeline.html` — brand-new template for the
  date-grouped task view.
- `tasks/templates/tasks/_task_form_inner.html` — Cancel button now
  routes to `{% url 'timeline' %}`; the Delete button now opens the
  confirmation modal instead of navigating away.
- `tasks/templates/tasks/calendar.html` — added `data-events-url` to
  the calendar div, plus a one-line "click any day to see tasks" hint.
- `tasks/templates/tasks/settings.html` — added the dark-mode toggle,
  the mobile-notifications note, and the corrected permission-button
  script with toast feedback.
- Deleted: `analytics.html`, `task_list.html`, `timelog_form.html`,
  `_timelog_form_inner.html`.

### What I deliberately *didn't* do

- **No new model migrations.** All v1.2 work is at the view / template /
  static-asset layer. The existing schema (Task, TimeLog, UserSettings)
  is unchanged, and no data is destroyed.
- **No service-worker push notifications.** Still listed under Future
  work in the README. The current approach (poll while open) is enough
  for an honest demo, and a service worker is a bigger commitment than
  this sprint warranted.
- **No backend changes to FullCalendar's events endpoint.** The day-modal
  re-uses `Task.objects.filter(...due_date in [day, day+1))` rather than
  any new aggregation logic, so the data the calendar shows and the data
  the day-modal shows are guaranteed to agree.

### What I learned

- **Removing things is harder than adding them.** Every view I deleted had
  three or four references in templates, the sidebar, the keyboard
  shortcuts, the README, and the manual. A search-and-fix pass at the end
  was essential.
- **Toast notifications change the feel of an app dramatically** for very
  little code. The hardest part was making them survive the page reload
  after a modal submit; `sessionStorage` is the right tool for that.
- **Natural-language date parsing is genuinely magical** when it works,
  and chrono-node is small enough to load over CDN. Showing a "Detected:
  …" hint with an undo link removes almost all of the surprise from
  surprise auto-fill.

---

## v1.3 — Final feature pass (April 2026)

This sprint applied a 19-item explicit feature list on top of v1.2. The
shape of the app, the Mono Grid design language, and the dark/light toggle
are unchanged.

### New / changed behaviour

1. **New-task defaults.** Opening the New-task modal pre-fills the due-date
   to *now + 2 hours, rounded to the next 30 minutes*, and the reminder
   to *5 minutes before*. Edit-task does **not** apply defaults.
2. **Regex natural-language date parser.** `chrono-node` is replaced with a
   tiny in-house regex parser that handles `today`, `tomorrow`, `next
   monday`, `in 3 days`, `Apr 30`, `5pm`, `at 17:30`, and combinations.
3. **Someday bucket.** Tasks created without a due date are kept in a new
   *Someday* section on the dashboard. Order is fixed: TODAY → SOMEDAY →
   TOMORROW. The Pending KPI counts *today + someday only*.
4. **Tomorrow section.** A read-only preview of tomorrow's pending tasks
   sits below Someday on the dashboard.
5. **Calendar dots coloured by category.** Each day with at least one
   pending task gets a single dot whose colour is the highest-precedence
   category (Urgent &rsaquo; Work &rsaquo; Study &rsaquo; Personal &rsaquo;
   Health). A legend is shown below the calendar.
6. **Urgent priority.** A new priority above High; renders as a red pill,
   pushes affected rows to the top of every list, and gives them a red
   left border.
7. **Category renaming.** Settings exposes 4 category-label inputs (Work /
   Study / Personal / Health). Colours are fixed; only the label changes.
8. **Timeline order.** Groups are now strictly chronological:
   PAST → TODAY → TOMORROW → FUTURE.
9. **Floating Today button.** When the timeline scrolls away from the
   *Today* group, a fixed-position pill appears in the bottom-right and
   smoothly scrolls back.
10. **Bounded list height.** The dashboard and timeline scroll containers
    are capped at 500 px on desktop and 400 px on mobile, so the rest of
    the page is always reachable.
11. **AJAX task-toggle.** Clicking the checkbox no longer reloads the
    page. The server returns JSON; the row fades out (or just toggles
    its line-through), and the Pending KPI updates in place.
12. **Pomodoro reset confirm.** Resetting a running timer prompts
    *"Reset timer? Your progress will be lost."* before clearing.
13. **Pomodoro sound + notification.** Two short beeps + a browser
    notification fire at the end of a Pomodoro, both gated by independent
    Settings toggles.
14. **Activity log page.** Last 30 actions (created / updated / completed /
    re-opened / deleted / restored) for the current user, with a link to
    the trash for soft-deleted items.
15. **Calendar list view label.** List view headings now read
    *"Monday, Apr 28"*.
16. **Zambian public holidays.** Optional Settings toggle. When on, the
    13 standard public holidays (incl. movable Easter dates 2024–2028)
    render as gray, non-editable events on the calendar.
17. **Exact FullCalendar overrides.** Buttons, day cells, list view, and
    holiday events all match the Mono Grid design tokens.
18. **Quick Actions removed.** The 2×2 grid on the dashboard is gone;
    every action it duplicated already lives in the sidebar or the
    floating *+ New task* button.
19. **Demo data seeder.** `manage.py seed_demo --user=milimo` creates
    35 representative tasks (today, tomorrow, future, urgent, someday,
    completed past). Idempotent — re-running cleans prior demo tasks
    first.

### Schema changes (migration `0003_v13_features`)

- `Task.priority` choices extended: `urgent` (added), high, medium, low.
- `Task.due_date` becomes nullable (Someday tasks have no due date).
- New model `ActivityLog` (capped at 30 rows per user, enforced in
  `ActivityLog.record()`).
- `UserSettings` gains `pomodoro_sound_enabled`,
  `pomodoro_notification_enabled`, `show_public_holidays`, and four
  category-label fields.

### Files added / changed

- **Added**: `tasks/management/commands/seed_demo.py`,
  `tasks/templatetags/harpr_extras.py`,
  `tasks/context_processors.py`,
  `tasks/templates/tasks/activity_log.html`,
  `tasks/templates/tasks/_dashboard_row.html`,
  `tasks/migrations/0003_v13_features.py`.
- **Rewritten**: `tasks/views.py`, `tasks/forms.py`,
  `tasks/templates/tasks/{dashboard,timeline,calendar,settings,_task_form_inner}.html`,
  `templates/base.html`, `static/js/{harpr,calendar}.js`,
  `static/css/cosmos.css` (additive — Mono Grid tokens preserved).

### What I deliberately *didn't* do

- **Touch the Mono Grid design tokens** or the dark/light CSS variables.
- **Add server-sent events / push.** The reminder + Pomodoro hooks
  continue to use the existing in-tab polling and Web Notifications API.
- **Persist Activity-log entries beyond 30.** The cap is enforced in
  `ActivityLog.record()` so the table stays bounded for every user.
