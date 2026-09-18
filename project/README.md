# Harpr — Task & Activity Planner

A simple task-and-activity planner built in Django. Final-year project for the
**BSc Computer Science** programme at the **University of Zambia (UNZA)** —
*Milimo Kasamba Mukkuli*, supervised by *Prof. J. Phiri*.

> **v1.2 (current release)** focuses the app on tasks: the Timeline is now a
> date-grouped task view, the dashboard is reduced to a single Pending KPI
> with a scrollable Today list, the calendar gets clickable days with green
> dots, and the title field parses natural-language dates as you type. See
> the **What's new in v1.2** section below for the full list.

> **Why "Harpr"?** Like a harp, the planner gives every string of your day a
> place to vibrate — one task at a time, in tune.

---

## What it does

### Core
- Sign up, sign in, sign out (Django built-in auth)
- Create / edit / delete tasks with a category (Work, Study, Personal, Health)
  and a priority (High, Medium, Low)
- Mark tasks complete or pending
- **Today** dashboard with a single Pending KPI, today's pending tasks
  (sorted by due time, scrollable), Pomodoro timer with adjustable length,
  and a Recently completed list
- **Timeline** — every task grouped by due date (Today / Tomorrow / weekday
  labels / Earlier / Someday). Overdue tasks stay on their original date
  group so nothing silently moves on you. CSV export of all tasks.
- **Calendar** — FullCalendar monthly grid, green dot on days that have
  tasks, click any day to see what's scheduled
- **Trash** — soft-deleted tasks, restorable, with "Empty trash" action
- **Settings** — dark-mode toggle, browser-notification preference, browser
  permission button, mobile-notifications note

### v1.2 — what's new in this release
1. Warm light background (`#f5f5f0`) and **120% base font size** across all
   breakpoints
2. Notifications permission button now correctly requests browser permission
   (the click handler was missing); Settings shows an inline note about
   how mobile notifications work on Android vs iOS
3. **Calendar dots** instead of event chips, plus a **day-click modal**
   listing tasks for that day
4. **Dashboard simplified** — only Pending KPI; Today list (pending only,
   sorted by due time, scrollable: 5 rows mobile / 7 rows desktop); Recently
   completed card replaces "Next 7 days"
5. **Analytics page and time-logging UI removed**; the `TimeLog` model and
   table are kept (no data is destroyed)
6. **Timeline redesigned** as the main task view, grouped by date, with a
   CSV export of every task. Overdue tasks remain on their original date
   group.
7. **Pomodoro length is configurable** from 1 to 180 minutes via a small
   ⚙ Settings popup; lengths over an hour show as e.g. "1hr 56min". The
   "Linked task" picker was removed for simplicity.
8. **Delete confirmation as a small modal** ("Move *X* to the Trash?")
   instead of a full-page form
9. **Toast notifications** in the corner for every CRUD operation
10. **Natural-language date parser** on the task-title field (chrono-node
    via CDN). "Submit report tomorrow 5pm" auto-fills the Due date.
11. **Dark-mode toggle in Settings** (mirrors the sidebar's ☀ / ☾ button)
12. **Sidebar slimmed** to Today / Timeline / Calendar / Trash / Settings;
    mobile bottom nav reduced to four items

The look-and-feel is still the "Mono Grid" theme: hairline borders,
monospace numbers (JetBrains Mono), and a single emerald accent. The
light/dark toggle is remembered in `localStorage`.

### v1.1 — earlier rebrand sprint (still in the app)
1. Browser notifications for task reminders (5 / 15 / 30 / 60 min before due)
2. Task duration field, used to compute end times
3. Mobile-responsive layout with a bottom navigation bar on small screens
4. Modal popups for "New task" — no full page reload
5. Soft-delete trash — deleted tasks land in `/trash/`, restorable for life
6. Pomodoro timer on the dashboard
7. Keyboard shortcuts — `N`, `T`, `C`, `D`, `?`, `Esc`
8. CSV export from the Timeline page

---

## Tech stack

| Concern              | Choice                                    |
| -------------------- | ----------------------------------------- |
| Language             | Python 3.11                               |
| Framework            | Django 5.2                                |
| Database (dev)       | SQLite                                    |
| HTML / CSS / JS      | Plain — no build step                     |
| Calendar             | FullCalendar 6 (CDN)                      |
| Date NLP             | chrono-node 2.7.5 (CDN)                   |
| Fonts                | Inter + JetBrains Mono (Google Fonts)     |
| Notifications        | Web Notifications API + 60-second polling |
| Static file serving  | WhiteNoise (production)                   |
| Auth                 | `django.contrib.auth` (no third party)    |

No React, no TypeScript, no monorepo, no codegen, no separate API server.

---

## Project layout

```
artifacts/cosmos-planner/        (folder name kept from v1.0; brand is "Harpr")
├── manage.py
├── requirements.txt
├── README.md, BUILD.md, MANUAL.md
├── timeplanner/                 # Django project package
│   ├── settings.py, urls.py, wsgi.py, asgi.py
├── accounts/                    # Auth app (login / register / logout)
│   ├── views.py, urls.py, forms.py
│   └── templates/accounts/
│       ├── login.html
│       └── register.html
├── tasks/                       # Main app
│   ├── models.py                # Task, TimeLog, UserSettings
│   ├── views.py, urls.py, forms.py, admin.py
│   ├── context_processors.py    # APP_NAME / APP_TAGLINE globals
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_harpr_features.py
│   └── templates/tasks/
│       ├── dashboard.html       # Today list + Pomodoro + Recently completed
│       ├── timeline.html        # NEW — date-grouped task view (replaces task_list)
│       ├── task_form.html       # full-page form (also embedded in modal)
│       ├── _task_form_inner.html # reusable form fragment
│       ├── task_confirm_delete.html  # fallback (modal is preferred)
│       ├── trash.html           # restore / purge
│       ├── calendar.html        # FullCalendar w/ green-dot day markers
│       └── settings.html        # dark-mode + notification prefs
├── templates/
│   └── base.html                # Sidebar + theme toggle + modals + mobile nav
└── static/
    ├── favicon.svg              # NEW — emerald harp
    ├── css/cosmos.css           # All visual styling lives here
    └── js/
        ├── calendar.js          # FullCalendar bootstrap
        └── harpr.js             # NEW — modals, shortcuts, reminder polling
```

---

## Run it locally

```bash
# 1. Install dependencies (Python 3.11 recommended)
pip install -r requirements.txt

# 2. Apply migrations (creates db.sqlite3)
python manage.py migrate

# 3. (Optional) Create a superuser for /admin/
python manage.py createsuperuser

# 4. Start the dev server
python manage.py runserver
```

Then open <http://127.0.0.1:8000>.

On Replit the app starts automatically. The first request triggers `migrate`,
so there is nothing to set up by hand.

### Environment variables

| Var              | Purpose                                  | Default              |
| ---------------- | ---------------------------------------- | -------------------- |
| `SESSION_SECRET` | Django `SECRET_KEY` (set in production)  | dev placeholder      |
| `DJANGO_DEBUG`   | `1` for dev, `0` for production          | `1`                  |
| `PORT`           | Bind port for the dev / WSGI server      | `8000` (dev)         |

---

## Documentation

- **`BUILD.md`** — first-person, week-by-week build story (now includes the
  Harpr v1.1 rebrand sprint)
- **`MANUAL.md`** — end-user guide for every feature

---

## Future work (out of scope for v1.1)

- True **push notifications** when the browser tab is closed (Service Worker
  + `webpush` / VAPID). Right now reminders only fire while Harpr is open.
- AI assistant powered by Gemini (chat-driven planning)
- WhatsApp reminders via Twilio
- Multi-device sync, native mobile app
- Recurring tasks (daily / weekly / monthly)
