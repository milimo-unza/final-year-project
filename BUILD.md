# Build Log — Harpr

**Author:** Milimo Kasamba Mukkuli (2021515567)
**Programme:** BSc Computer Science, University of Zambia
**Supervisor:** Prof. J. Phiri
**Period:** April 2026 – September 2026

This is a record of how I built Harpr, week by week. Most of it was
written during the build, from notes I kept as I went. The last two
sections were tidied up after the project was done, so they read a bit
more carefully than the earlier ones.

---

## Week 1 — Setting up Django and accounts

I installed Python 3.13 and started a Django project. I picked Django
because the auth system, admin, ORM, and migrations come built in — for
a one-person project I didn't want to spend time evaluating libraries.

```bash
django-admin startproject timeplanner .
python manage.py startapp accounts
python manage.py startapp tasks
```

For accounts I used Django's built-in `LoginView` and `LogoutView`, and
wrote one small `register` view that wraps `UserCreationForm` and adds an
email field.

Things that went wrong:

- Project name typo (`timeplanner` vs `timeplanner`) — fixed with `sed`.
- Forgot to activate the venv the first time. Learned to always run
`source .venv/bin/activate` first.
- `__str__` vs `_str__` in the model — Python didn't complain until I
tried to print a task.

---

## Week 2 — The Task model and CRUD

One model to start: `Task`. Title, description, due date, category,
priority, completed flag, user foreign key.

```
class Task(models.Model):
    CATEGORY_CHOICES = [
        ("work", "Work"), ("study", "Study"),
        ("personal", "Personal"), ("health", "Health"),
    ]
    PRIORITY_CHOICES = [
        ("high", "High"), ("medium", "Medium"), ("low", "Low"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="work")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    completed = models.BooleanField(default=False)
```

I used function-based views, not class-based. They read top-to-bottom,
which is easier when explaining the code to someone else.

Every view starts with a query scoped to `request.user`:

```
Task.objects.filter(user=request.user)
```

No path returns another user's data. This was the first thing I checked
before adding anything else.

---

## Week 3 — Calendar

I used FullCalendar 6 from a CDN. One Django view returns JSON:
holidays plus a per-day task map. On the client, instead of letting
FullCalendar render its own event chips, I inject my own chips inside
each day cell using `dayCellDidMount`. That gives me control over the
colour-by-category look.

The first version double-rendered chips on month change because
`datesSet` and `eventsSet` both fire and both were calling `injectChips`.
Fix: wrap the injection in `setTimeout(..., 0)` so it runs after the
DOM settles, and check for an existing chip stack before adding a new one.

Clicking a day opens a modal with that day's tasks. Same AJAX toggle
used on the dashboard and timeline — one function, three places.

---

## Week 4 — Time tracking

`TimeLog` stores a single integer `minutes` value. The form exposes two
number inputs — hours and minutes — and combines them in `clean()`:

```
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

The form dropdown for the `task` field initially showed every task in the
database, not just the current user's. Fixed by overriding the form's
`__init__` to take a `user` argument and filter.

---

## Week 5 — Charts

Three charts on the dashboard, drawn with Chart.js 4. Aggregations happen
server-side in the view and are handed to the template as JSON:

```
cat_totals = (
    TimeLog.objects
    .filter(user=user)
    .values("task__category")
    .annotate(total=Sum("minutes"))
)
```

Keeping the aggregation server-side means the client only draws — no raw
log data leaves the server.

First version of the daily line chart showed the wrong order because I was
sorting stringified dates. Fixed by building the labels from the same
`datetime` objects used in the query.

---

## Week 6 — Design

All the CSS lives in one file. Colours are CSS custom properties on
`:root`, and dark mode overrides them under `[data-theme="dark"]`:

```
:root {
  --bg:         #eceae3;
  --fg:         #2b2823;
  --card:       #fbf9f4;
  --border:     #d9d4c6;
  --accent:     #b5623e;
}

[data-theme="dark"] {
  --bg:         #1c1a17;
  --fg:         #ebe7dd;
  --accent:     #d17a55;
}
```

Dark mode is a `data-theme` attribute on `<html>`, saved in `localStorage`,
and read by an inline script in `<head>` before the page paints — so there's
no flash of light theme on a dark refresh.

The first dashboard used a `<table>` and looked fine on my laptop but
cramped on my phone. I rewrote the layout with CSS Grid and a few media
queries.

---

## Week 7 — Bug fixing and a smoke test

Wrote a small test that logs in and GETs every URL:

```
c = Client()
c.login(username="milimo", password="milimo")
for u in ["/", "/timeline/", "/calendar/", "/calendar/events/", "/activity-log/"]:
    assert c.get(u).status_code == 200
```

Bugs found:

1. `due_date` didn't prepopulate when editing. The widget format didn't
match what HTML5's `datetime-local` expects. Fixed by splitting the
field into three form fields (date, hour, minute) and recombining them
in `clean()`.
2. CSRF blocked POST from the Replit preview iframe. Added `*.replit.dev`
to `CSRF_TRUSTED_ORIGINS`.
3. `X-Frame-Options: DENY` blocked the preview entirely. I removed
`XFrameOptionsMiddleware`. That's fine for development; a production
deploy would need to add it back with a targeted exception.

---

## Weeks 8–10 — Feature sprint and rebrand

The app was originally called "Cosmos AI Planner". That name promised an
AI it didn't have, so I renamed it. **Harpr** is a deliberate misspelling
of *harp* — each task is a string in your day's chord.

The rebrand touched every template. I added a context processor so
`APP_NAME` and `APP_TAGLINE` are available everywhere instead of hard-coding
"Harpr" in every file.

Two features landed in this sprint that are still in the app:

**Modals for task create/edit.** A click on a button with
`data-modal="task-new"` or `data-modal="task-edit"` is intercepted by
JavaScript. The URL is fetched, the form is lifted out of the response,
and it's injected into a modal. Submitting is also intercepted, POSTed
via `fetch`, and on success the page reloads with a small toast queued.

**Toasts.** Small notifications in the bottom-right corner on save, edit,
delete, complete, restore.

Several other features were started in this sprint and later cut. See
the "Scope cuts" section at the end.

---

## Weeks 11–14 — Refocus on tasks

Feedback after the mid-project review was that the app was trying to do
too much. Two concepts were competing — Tasks and Time Logs — and most
screens showed both.

I made these decisions:

- **Keep the `TimeLog` table in the database.** Remove most of its UI. No
data is destroyed, and if I want to bring time-logging back the model
is still there.
- **Keep the design language.** The point of this sprint was for the app
to get quieter, not louder.
- **Increase the base font size** so desktop and mobile reading are
consistent.

What changed:

- Sidebar slimmed down.
- Dashboard rebuilt: single Pending KPI, scrollable Today list, Recently
completed panel.
- Timeline became the main task view, grouped by due date.
- Calendar moved from event chips to single colour-coded dots per day.
- Toasts, delete-confirmation modal, natural-language date parser
(hand-written regex, no library).

Removing things turned out to be harder than adding them. Every deleted
view had three or four references elsewhere — in templates, the sidebar,
the keyboard shortcuts, the README. A final search-and-fix pass was
necessary.

---

## Weeks 15–16 — Final feature pass and polish

The last two weeks before submission were mostly bug fixing and cleanup,
with a few small additions:

- **Someday bucket.** Tasks with no due date sit in their own section on
the dashboard. The Pending count includes them.
- **AJAX toggle.** Clicking a checkbox updates the row and the Pending
count without a full page reload. On the dashboard, the row fades out
because completed tasks don't belong in a pending list.
- **Activity log page.** The last 30 actions per user.
- **Category renaming.** The Settings page exposes four inputs so the
category labels can be changed. Colours are fixed.
- **Demo data seeder.** `manage.py seed_demo --user=X` creates a few
hundred realistic tasks, so screenshots don't show empty states.

Bugs fixed in this sprint:

**The log-time modal was rendering two copies of its form.** The modal
fetches a URL and pulls a form out of the response. But the URL was
returning the whole page — sidebar, mobile nav, other modal shells — and
the JS then did `querySelector('form.form-grid') || querySelector('form')`.
The fallback selector was sometimes matching the wrong form. Fix:

1. Add `?embed=1` support to the `log_time` view so it returns only the
form fragment when asked.
2. Extract the form into a shared template, included by both the full
page and the modal. One source of truth.
3. Tighten the JS selector to a specific class, never a bare `form`
fallback.

This also fixed a subtler bug: the modal was silently submitting the wrong
form, so `TimeLog.objects.count()` stayed at zero no matter how many times
you saved.

**The Insights card had three different timeframes.** The pie chart was
all-time, the line was last 7 days, the bar was all-time. Fixed by
threading one `week_start_dt` through all three aggregations.

**Mobile layout for Calendar and Activity.** The calendar toolbar's grid
collapsed badly under 640px. The activity list squeezed four columns into
phone width. Both got media-query overrides using `grid-template-areas`.

---

## Scope cuts

Several features were started and then removed or left incomplete. What
was cut, and why:

- **Browser notifications and reminders.** I built polling for due
reminders and a browser-notification permission flow. Then I realised
the whole thing only works while a tab is open, which makes the feature
nearly useless for the use case (remembering a task an hour from now,
when you're not looking at the app). A real implementation needs a
service worker and a push server, which was out of scope. The
`Task.remind_minutes_before` column stays in the database; the UI was
removed.
- **Pomodoro timer.** Built it, and then realised it didn't fit the
project. The proposal is about planning and tracking, not about
running a stopwatch. Cut.
- **Soft-delete trash bin.** Added `is_deleted` / `deleted_at` columns
and an `AllTaskManager`. Then I realised a two-week-old project with a
trash bin was over-engineered for a single user. The columns stay; the
view was never wired up.
- **Public holidays on the calendar.** I added a `show_public_holidays`
setting and started listing Zambian public holidays. The dataset was
always going to be incomplete (movable feasts vary year to year), and
the toggle was one more thing to explain in the viva. Cut.
- **Time logging UI, then partial return.** The v1.2 sprint removed the
standalone "Log time" page and its sidebar entry. Time logging came
back in v1.3 as a small button inside the task edit modal. The model
and the form were never removed, so restoring the button was a
template change, not a migration.

The cuts are visible in the code as columns and context-processor keys
that nothing reads. Cleaning those up properly would be a migration, and
it isn't worth doing for a project of this size.

---

## What I'd do differently

**Decide the data model early.** I spent one sprint building a
two-concept app (Tasks + Time Logs), one sprint tearing the second
concept out, and then brought part of it back. That's two sprints of
work that a week-one decision would have avoided.

**Don't fetch full pages into modals.** The `?embed=1` pattern should
have been in from day one. Building the modal as an afterthought meant
every modal request was rendering the entire page (sidebar, mobile nav,
four other modal shells) just so the client could pull out a twelve-line
form.

**Freeze features earlier.** The last two weeks added a lot of small
things that didn't need to be added. The right call would have been to
freeze the feature set two weeks before submission and spend that time
on documentation, testing, and rehearsal.

**Write the manual as I went.** The user manual was written at the end
in a single pass, which meant reconstructing a lot from memory. Writing
each section as I finished the feature would have taken ten minutes a
week and been more accurate.

---

## Future work

- Recurring tasks (daily, weekly, monthly).
- A trash / undelete view using the existing `is_deleted` column.
- True push notifications via service worker.
- Postgres instead of SQLite for deployment.
- Password reset (needs SMTP).

---

## Acknowledgements

Thanks to Prof. J. Phiri for weekly check-ins, the Department of Computer
Science at UNZA, and the maintainers of Django, Chart.js, and FullCalendar.

