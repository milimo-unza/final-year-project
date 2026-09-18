# Harpr — Task & Activity Planner

Final-year BSc Computer Science project for the University of Zambia (UNZA).
Author: *Milimo Kasamba Mukkuli*. Supervisor: *Prof. J. Phiri*.

## Stack

- **Backend**: Django 5.2 (sync, no DRF)
- **DB**: SQLite (default) — `db.sqlite3` in the repo root
- **Frontend**: server-rendered Django templates + vanilla JS + a single
  hand-rolled CSS file (`static/css/cosmos.css`, the "Mono Grid" design
  language). FullCalendar 6 is loaded from a CDN for the calendar page.
- **Python venv**: `venv/` (project root); activated by the workflow command.

## Run

The `web` workflow runs:

```
venv/bin/python manage.py migrate --noinput && \
  venv/bin/python manage.py runserver 0.0.0.0:$PORT --insecure
```

The dev port is supplied by Replit via `$PORT`. App is reachable at
`https://${REPLIT_DEV_DOMAIN}` once the workflow is running.

## Demo user

- **Username**: `milimo`
- **Password**: `milimo`
- Demo data: `venv/bin/python manage.py seed_demo --user=milimo`
  (idempotent — re-running cleans prior demo tasks first).

## Project layout

```
timeplanner/        # Django settings + root URLs
tasks/              # Single app — models, views, forms, admin, templatetags
  context_processors.py    # APP_NAME, category_colors/labels, urgent_color
  templatetags/harpr_extras.py   # cat_label, cat_color, get_item filters
  management/commands/seed_demo.py
  migrations/
    0001_initial.py
    0002_*.py
    0003_v13_features.py   # Urgent priority, ActivityLog, expanded settings
templates/base.html        # Shared shell (sidebar, mobile nav, modals)
tasks/templates/tasks/     # Per-page templates (dashboard, timeline, …)
static/css/cosmos.css      # The Mono Grid design system (single file)
static/js/harpr.js         # Modals, toasts, AJAX toggle, regex date parser,
                           # default-value autofill, Pomodoro completion hook
static/js/calendar.js      # FullCalendar wrapper (dots + holiday events)
```

## Releases

- **v1.0** — initial Django scaffolding, basic CRUD.
- **v1.1** — Mono Grid redesign, calendar page.
- **v1.2** — task-only refocus: dashboard KPI + scrollable Today list,
  date-grouped Timeline, calendar dots, chrono-node date parser, toasts.
- **v1.3 (current)** — final feature pass. See `BUILD.md` for the full
  19-item changelog. Highlights: AJAX task-toggle, Someday + Tomorrow
  buckets, Urgent priority, category-coloured calendar dots with legend,
  optional Zambian public holidays, Activity log page, regex
  natural-language date parser (chrono-node removed), Pomodoro reset
  confirm + sound + notification, demo data seeder.

## User preferences

- **Mono Grid design**: do not change. The `static/css/cosmos.css` file
  encodes the design tokens (CSS custom properties) and the dark/light
  toggle. Both are off-limits unless the user asks.
- **No new third-party JS** beyond what's already loaded (FullCalendar
  via CDN). The natural-language date parser is hand-rolled regex —
  do not reintroduce chrono-node.

## Documentation

- `BUILD.md` — sprint-by-sprint engineering log (v1.0 → v1.3).
- `MANUAL.md` — end-user manual.
- `README.md` — public-facing overview + feature table.
