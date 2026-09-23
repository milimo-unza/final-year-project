# Harpr - Time & Activity Planner

A web-based planner built with Django. Final-year project for the BSc
Computer Science programme at the University of Zambia.

**Author:** Milimo Kasamba Mukkuli (2021515567)
**Supervisor:** Prof. J. Phiri
**Live demo:** https://milimo.pythonanywhere.com
**Source:** https://github.com/milimo-unza/final-year-project

---

## What it does

Harpr is a planner that helps you organise tasks and see how you actually
spend your time. Every task gets a title, a due date, a category, a
priority, and an optional duration. You can mark tasks complete, log time
against them, and see charts of how your week has gone.

The idea is to be simpler than project management suites and more useful
than a plain to-do list.

### Features

- **Accounts** - sign up, sign in, sign out. Django's built-in auth.
- **Tasks** - create, edit, complete, delete. Each has a title, due date, category, priority, and optional duration.
- **Quick add** - one-line input on the Today page. Type "Pay rent tomorrow" and it fills in the date.
- **Today dashboard** - overdue tasks, today's tasks, a preview of tomorrow, and anything parked under Someday.
- **Timeline** - every task grouped by due date, chronologically, with a scroll-to-today button in the header.
- **Calendar** - month, week, and list views. Month view shows chips of each task inside the day cell. Click any day to see what's scheduled.
- **Time logging** - record how long you spent on a task. Total logged time shows on the task row.
- **Insights** - three charts on the Today page: time per category, activity over the last week, and completed vs pending tasks per category. Switchable tabs, remembers your last choice.
- **CSV export** - download every task as a spreadsheet.
- **Activity log** - the last 30 actions you've taken, viewable from the sidebar.
- **Dark mode** - a toggle in the sidebar footer. Follows your system preference on first visit.

---

## Tech stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.13 |
| Framework | Django 6.1 |
| Database | SQLite |
| Frontend | Server-rendered Django templates |
| Styling | Hand-written CSS, one file |
| JavaScript | Vanilla, no framework, no build step |
| Calendar | FullCalendar 6, loaded from CDN |
| Charts | Chart.js 4, loaded from CDN |
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
python manage.py seed_demo --user=YOUR_USERNAME   # optional
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
    ├── css/cosmos.css      The entire design system
    └── js/
        ├── harpr.js        Modals, toasts, date parser, quick add
        └── calendar.js     FullCalendar setup and chip injection
```

---

## How users are separated

Every view that touches tasks is decorated with `@login_required` and
starts from a query scoped to `request.user`. There is no code path that
returns another user's data.

---

## Limitations

- Reminders were removed during development. Push notifications when the
browser tab is closed would need a service worker and a push server.
- No recurring tasks. Each task happens once.
- SQLite, not Postgres. Fine for a single-user demo, not for concurrent traffic.
- No password reset. That would require an SMTP server, which free hosting
doesn't provide.

---

## Documentation

- **MANUAL.md** - end-user guide for every feature
- **BUILD.md** - week-by-week account of how the project was built

---

## Acknowledgements

Thanks to Prof. J. Phiri for supervision, and to the maintainers of Django,
FullCalendar, and Chart.js.

</BDS:create_file>

Download that, then in your terminal:

```bash
mv ~/Downloads/README.md /mnt/c/Users/Pluto/Downloads/Old/Work/Projects/final-year-project/README.md

Or move it via Windows Explorer — same result.

**Verify:**

```
cd /mnt/c/Users/Pluto/Downloads/Old/Work/Projects/final-year-project && wc -l README.md
```

Should show around 120 lines.

**Read it once.** If anything's wrong — Python version, the URL, a feature I described incorrectly — tell me and I'll give you a corrected file. If it's good, say **"next"** and I'll send MANUAL.md the same way: as a downloadable file, not a heredoc. No more truncation.
