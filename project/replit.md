# Harpr — Task & Activity Planner

Final-year BSc Computer Science project (UNZA). Single-author Django app,
plain HTML/CSS/JS (no React, no build step).

## Stack
- Python 3.11, Django 5.2, SQLite
- WhiteNoise (production static), gunicorn (production server)
- FullCalendar 6 + chrono-node 2.7.5 (CDN)
- Inter + JetBrains Mono via Google Fonts

## Brand
- App name: **Harpr** — Task & Activity Planner
- Accent: emerald (`hsl(161 94% 30%)`)
- Logo: 6-string harp SVG (`static/favicon.svg`)
- Branding strings exposed to all templates via
  `tasks.context_processors.branding` → `{{ APP_NAME }}`, `{{ APP_TAGLINE }}`

## Run
The `web` workflow runs:
```
venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py runserver 0.0.0.0:$PORT --insecure
```

## v1.2 polish pass (current release, on top of v1.1)
1. Background `#f5f5f0`, base font-size 120% (desktop and mobile)
2. Settings: dark-mode toggle + working "Request browser permission" button
   + inline mobile-notification note (Android vs iOS)
3. Calendar: green dot on days with tasks (`dayCellDidMount` + `.has-tasks`),
   day-click modal fed by `/calendar/day/<y>-<m>-<d>/` JSON endpoint
4. Dashboard: single Pending KPI; Today list = pending only, sorted by
   due time, in `.task-scroll` (max-height ≈7 rows desktop / 5 mobile);
   Recently completed card replaces "Next 7 days"
5. Analytics page + time-logging UI removed; `TimeLog` model + table kept
   (no data destroyed). `TimeLogForm` deleted, `analytics.html`,
   `task_list.html`, `timelog_form.html`, `_timelog_form_inner.html` deleted.
6. Timeline rebuilt as the main task view, grouped by due date
   (Today / Tomorrow / weekday labels / Earlier / Someday). Overdue tasks
   stay in their original date group. CSV export = `harpr_tasks.csv`.
7. Pomodoro length adjustable (1–180 min) via ⚙ settings modal, persisted
   in `localStorage`; "1hr 56min" pretty hint; linked-task picker removed
8. Delete confirmation = small modal ("Move *X* to the Trash?") triggered
   by `data-delete-task="…"` on every Delete button
9. Toast notifications via `#toast-container` + `harpr.toast()`; survives
   modal-submit page reloads via `sessionStorage`
10. Natural-language date parser on task title input (chrono-node CDN);
    fills the `datetime-local` Due field, shows "Detected: …" hint
11. Sidebar: Today / Timeline / Calendar / Trash / Settings; mobile nav = 4
    items (Today / Timeline / Calendar / Settings)
12. Keyboard shortcuts now: `N` (new task), `T` (timeline), `C` (calendar),
    `D` (today), `?`, `Esc`. (Removed `L` for log-time and `A` for
    analytics.)

## v1.1 Harpr feature pass (still in the app)
1. Browser notifications + reminders (60-second poll → `views.reminders_due`)
2. Task duration field + `Task.end_time()`
3. Mobile-responsive layout + bottom nav
4. Modal popups for New task (vanilla JS, partial templates)
5. Soft-delete Trash (`Task.is_deleted` + custom `TaskManager`,
   `Task.all_objects` for trash view)
6. Pomodoro timer (dashboard card; WebAudio beep)
7. Keyboard shortcuts; CSV export

## Files of note
- `tasks/models.py` — Task (+ soft delete fields), TimeLog (kept),
  UserSettings
- `tasks/views.py` — `dashboard` (pending-only + recently completed),
  `timeline` (date-grouped task view), `task_list_redirect`,
  `calendar_day_tasks`, `timeline_export_csv` (now exports tasks),
  `trash_*`, `reminders_due`, `settings_view`
- `tasks/urls.py` — `/`, `/timeline/`, `/timeline/export.csv`,
  `/tasks/{new,<pk>/edit,<pk>/delete,<pk>/toggle}/`,
  `/tasks/` → redirect to timeline (kept as `task_list` name),
  `/trash/...`, `/calendar/{events,day/<y>-<m>-<d>}/`,
  `/reminders/due/`, `/settings/`
- `tasks/forms.py` — `TaskForm` (with `data-chrono="1"` on title input);
  `SettingsForm`
- `tasks/migrations/0002_harpr_features.py` — single migration for the v1.1
  data-layer changes (still applied; no v1.2 migration needed)
- `static/js/harpr.js` — toasts, modals (task / delete / day-tasks /
  pomodoro settings / shortcuts), chrono-node integration, reminder polling
- `static/js/calendar.js` — FullCalendar bootstrap + green-dot markers
  + `dateClick` → day modal
- `static/css/cosmos.css` — global styles incl. timeline groups, scroll
  list, calendar dot, toasts, chrono hint, pomodoro settings button,
  delete-modal text, mobile breakpoint adjustments
- `templates/base.html` — sidebar + bottom-nav + all global modals
  (task / delete / day-tasks / pomodoro settings / shortcuts) +
  toast container + chrono-node CDN script tag
- `tasks/templates/tasks/timeline.html` — NEW; the date-grouped task view
- `tasks/templates/tasks/dashboard.html` — single KPI + scrollable Today
  list + Pomodoro w/ settings + Recently completed
- `tasks/templates/tasks/settings.html` — dark mode + notification prefs
  + working permission button

## Future work (deliberately out of scope)
- Service-Worker + VAPID push notifications (current ones only fire while a
  tab is open)
- Recurring tasks (daily/weekly/monthly)
- AI assistant via Gemini
- WhatsApp reminders via Twilio
- Native mobile app
