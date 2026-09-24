# Harpr — Time & Activity Planner

A web-based planner built with Django. Final-year project for the BSc
Computer Science programme at the University of Zambia.

**Author:** Milimo Kasamba Mukkuli (2021515567)
**Supervisor:** Prof. J. Phiri
**Live demo:** https://milimo.pythonanywhere.com
**Source:** https://github.com/milimo-unza/final-year-project

---

## What it does

Harpr is a task planner. You add tasks, give them a date, a category and a
priority, and mark them done when you finish them. There's a calendar view,
a timeline view, and a small amount of time tracking.

The idea is to be simpler than a project-management tool and more useful
than a plain to-do list.

### Features

- **Accounts** — sign up, sign in, sign out. Django's built-in auth.
- **Tasks** — create, edit, complete, delete. Each has a title, due date,
  category, priority, and optional duration.
- **Quick add** — a one-line input on the Today page. Type "Pay rent
  tomorrow" and it fills in the date. Works with "tomorrow", "next friday",
  "in 3 days", "Apr 30", "5pm", and combinations.
- **Today dashboard** — overdue tasks, today's tasks, a preview of
  tomorrow, and anything with no due date (the "Someday" bucket).
- **Timeline** — every task grouped by due date, chronologically. Past →
  Today → Tomorrow → Future → Someday.
- **Calendar** — three views: month (with dots on days that have tasks),
  week (columns, all tasks listed), and list. Click any day to see its tasks.
- **Time logging** — from a task's edit modal, log minutes spent on it.
  Total logged time shows on the task row.
- **Insights** — three charts on the Today page: minutes per category,
  minutes logged per day, and completed vs pending per category. All three
  use the last 7 days.
- **CSV export** — download every task as a spreadsheet.
- **Activity log** — the last 30 actions on your tasks.
- **Dark mode** — a toggle in the sidebar footer.

---

## Tech stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.13 |
| Framework | Django 6.0 |
| Database | SQLite |
| Frontend | Server-rendered Django templates |
| Styling | Hand-written CSS, one file |
| JavaScript | Vanilla, no framework, no build step |
| Calendar | FullCalendar 6, from CDN |
| Charts | Chart.js 4, from CDN |
| Fonts | Lora, Source Sans 3, JetBrains Mono |
| Static files | WhiteNoise |
| Hosting | PythonAnywhere |

No React, no TypeScript, no bundler, no separate API server.

---

## Running it locally

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo --user=YOUR_USERNAME   # optional demo data
python manage.py runserver
```

Open http://127.0.0.1:8000 in a browser.

---

## Project layout

```
final-year-project/
├── manage.py
├── requirements.txt
├── README.md, MANUAL.md, BUILD.md
├── timeplanner/            Django project package (settings, urls)
├── accounts/               Authentication app
│   ├── forms.py
│   ├── urls.py, views.py
│   └── templates/accounts/ login.html, register.html
├── tasks/                  Main app
│   ├── models.py           Task, TimeLog, UserSettings, ActivityLog
│   ├── views.py            All views and JSON endpoints
│   ├── forms.py            TaskForm, LogTimeForm
│   ├── urls.py
│   ├── context_processors.py
│   ├── templatetags/       Template filters
│   ├── management/commands/seed_demo.py
│   ├── migrations/
│   └── templates/tasks/    Per-page templates
├── templates/
│   └── base.html           Shared shell (sidebar, mobile nav, modals)
└── static/
    ├── favicon.svg
    ├── css/cosmos.css      The design system
    └── js/
        ├── harpr.js        Modals, toasts, date parser, quick add
        └── calendar.js     FullCalendar setup and dot injection
```

---

## How users are separated

Every view that touches tasks is decorated with `@login_required` and
starts from a query scoped to `request.user`. There is no code path that
returns another user's data.

---

## Limitations

- Reminders aren't wired up. The `Task.remind_minutes_before` column exists
in the model but nothing reads it. Browser notifications when the tab is
closed would need a service worker and a push server.
- No recurring tasks.
- No trash / undelete UI. The `Task.is_deleted` column exists but no view
uses it.
- SQLite, not Postgres. Fine for a single-user demo, not for concurrent
traffic.
- No password reset. That needs an SMTP server.

---

## Documentation

- **MANUAL.md** — end-user guide for every feature
- **BUILD.md** — week-by-week account of how the project was built

---

## Acknowledgements

Thanks to Prof. J. Phiri for supervision, and to the maintainers of Django,
FullCalendar, and Chart.js.

</BDS:create_file>

<BDS:create_file fileName="MANUAL.md">

```markdown
# Harpr — User Manual

A guide to using Harpr. Every screen is covered, in the order you'll
encounter it.

---

## 1. Creating an account

1. Open the app. You land on the **Sign in** page.
2. Click **Create one** at the bottom of the card.
3. Fill in a username, email, and password (twice). The password must be
   at least 6 characters and not entirely numeric.
4. Submit. You're signed in and taken to the **Today** page.

Already have an account? Sign in with your username and password.

You can sign out at any time using the **⏻** icon at the bottom of the
sidebar.

---

## 2. Today (the dashboard)

The Today page is deliberately focused on what you need right now. From
top to bottom:

- **Quick add bar** — type a title and press Enter to create a task.
  Natural language works: "Pay rent tomorrow", "Meeting Friday 3pm". If
  a date is detected, it goes on the task automatically.
- **Overdue** — tasks that were due before today and aren't done yet.
  Each has a small arrow button to push it to today. This section only
  appears if there's something overdue.
- **Today** — pending tasks due today, sorted by time.
- **Tomorrow** — a preview of what's due tomorrow.
- **Someday** — tasks with no due date. They sit here until you give them one.

On the right column:

- **Pending count** — open tasks in total.
- **Insights** — three charts with tabs to switch between them. Time per
  category, activity over the last week, and completed vs pending tasks
  per category. Harpr remembers which chart you looked at last.
- **Recently completed** — the last five tasks you finished.

Click any task title to open the edit modal.

---

## 3. Adding and editing tasks

Click **New task** (top-right of most pages) or use the quick add bar
on the Today page.

Fields:

- **Title** (required)
- **When** — date picker, plus hour and minute dropdowns in 24-hour
  format. Minute steps are 5 minutes. Leave the date empty to send the
  task to Someday.
- **Duration (minutes)** — optional, used to compute an end time.
- **Category** — Work, Study, Personal, or Health.
- **Priority** — High, Medium, or Low.
- **Reminder** — currently unused. Will be removed.

Click **Add task** (or **Save** when editing). A small toast appears in
the corner confirming the action.

### Natural language in the title

As you type in the title field, Harpr looks for a date phrase. When it
finds one, the date field fills in and a green hint appears under the
title. Examples it understands:

- "Submit report **tomorrow at 5pm**"
- "Call mum **next Friday 9am**"
- "Gym **today 18:30**"

You can always override the date manually afterwards.

### Complete, edit, delete

- **Complete** — click the circle on the left of any task row. On the
  dashboard, the row disappears because completed tasks aren't pending.
- **Edit** — click the task title. The edit modal opens.
- **Delete** — from inside the edit modal, click Delete. A confirmation
  appears. Once confirmed the task is gone.

---

## 4. Timeline

**Timeline** shows every task you have, grouped by due date. The order is:

1. Overdue dates (oldest first)
2. Today
3. Tomorrow
4. Future dates in chronological order
5. Someday (tasks with no date)

Each task shows its time, duration if set, and priority dot. Click a task
to open the edit modal.

**Scroll-to-today button** — the circular icon in the page header scrolls
back to today when you've scrolled away.

**Export CSV** — downloads `harpr_tasks.csv` with every task in a
spreadsheet format.

---

## 5. Calendar

The **Calendar** page has three views, switchable with the buttons in
the toolbar:

- **Month** — a grid. Each day shows coloured chips for its tasks, up to
  three per day. Days with more than three show a "+N more" link.
- **Week** — seven columns, one per day, with all tasks listed. Sunday
  to Saturday.
- **List** — a chronological list of upcoming days and their tasks.

Navigate with the **‹**, **·**, and **›** buttons. Click any day to open
a modal with that day's full task list.

Category colours (all muted, muted palette):

- Work: soft blue
- Study: soft purple
- Personal: soft green
- Health: soft teal

---

## 6. Time logging

From any task you can log how long you spent on it.

1. Open the task (click its title).
2. Click **Log time** in the modal.
3. Enter hours and minutes. Add an optional note.
4. Save.

Logged time appears on the task row as "45m logged". The Insights chart
on the Today page uses this data.

---

## 7. Insights

The Insights card sits in the right column of the Today page. It has
three tabs:

- **Pie** — time logged per category
- **Activity** — minutes logged per day, last seven days
- **Tasks** — completed vs pending per category

Switching tabs is instant. The choice persists across sessions.

---

## 8. Activity log

Every action you take on a task — created, edited, completed, re-opened,
deleted — is recorded. The last 30 are visible from the Activity link in
the sidebar.

---

## 9. Toast notifications

Every save, edit, or delete triggers a small toast in the bottom-right
corner. Toasts fade after three seconds. On mobile they appear above the
bottom navigation bar.

---

## 10. Dark mode

The **☀ / ☾** button in the sidebar footer toggles between light and
dark mode. On your very first visit Harpr follows your operating system
preference. After that your choice is remembered in this browser.

---

## 11. Mobile

On phones the sidebar is replaced by a bottom navigation bar. The task
list, calendar, and modals all adapt to narrow screens. Cards stack into
a single column. Text is sized for the viewport.

---

## 12. Tips

- Use the quick add bar for anything you think of in the moment — you
  can always edit details later.
- Set a duration on tasks you actually want to track. Tasks without a
  duration can still have time logged against them, but you won't see an
  end time.
- The Timeline's CSV export is useful for putting together a report or
  reviewing what you've done over a period.
- If something looks wrong after an edit, reload the page. Every list
  reflects the database on page load.

