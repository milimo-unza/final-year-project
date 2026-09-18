# User Manual — Harpr

**Harpr — Task & Activity Planner**

Welcome! This guide walks you through every screen of Harpr. The app is small
on purpose — five real pages, a sidebar (or bottom bar on mobile), and a
handful of keyboard shortcuts.

---

## 1. Create an account

1. Open the app. You'll land on the **Sign in** screen.
2. Click **"Create one"** at the bottom of the card.
3. Fill in a **username**, **email**, and **password** (twice). The password
   must be at least 6 characters and not entirely numeric.
4. Submit. You're signed in and dropped on the **Today** page.

Already have an account? Use **Sign in** with your username and password.

You can sign out at any time using the **⏻** icon at the bottom of the
sidebar (desktop) or the **Settings** screen (mobile).

---

## 2. Today (the dashboard)

The dashboard is deliberately stripped down to **what you need today, right
now**. From top to bottom:

- **Pending KPI** — a single big number showing how many tasks you still owe
  yourself (across all dates).
- **Today list** — every pending task whose due date is today, sorted by due
  time. Click the circle on the left to mark a task done; it disappears from
  this list (it's no longer pending). On desktop the list shows up to about
  seven rows before scrolling; on mobile, about five.
- **Pomodoro timer** — a focus countdown. The default is 25 minutes; click
  the small **⚙ Settings** button next to "Pomodoro" to set any length from
  **1 to 180 minutes**. Lengths over an hour show as e.g. `1hr 56min` so
  you always know what you're committing to. Your choice is remembered in
  your browser.
- **Quick actions** — one-click links to add a task, jump to Timeline /
  Calendar, or download your tasks as CSV.
- **Recently completed** — your last five completed tasks, with the time
  you finished. A tiny win-list, basically.

The big **+ New task** button at the top right is reachable from every page
and opens as a **modal popup**, so you don't lose your place.

---

## 3. Adding & managing tasks

From any page, click **+ New task** (or press **N**).

1. Fill in:
   - **Title** (required)
   - **Description** (optional)
   - **Due date / time** — use the date picker
   - **Duration (minutes)** — optional; used to compute the task's end time
   - **Category** — Work, Study, Personal, or Health
   - **Priority** — High, Medium, or Low
   - **Remind me** — None, 5, 15, 30, or 60 minutes before
2. Click **Create task**. You'll see a small **toast** in the corner
   confirming the save.

### Type the date into the title

The title field has a **natural-language date parser** built in (powered by
chrono-node). As you type, Harpr looks for date phrases like:

- "Submit report **tomorrow at 5pm**"
- "Call mum **next Friday 9am**"
- "Gym **today 18:30**"

When it finds one, the **Due date** field fills in for you and a small green
hint appears under the title (`Detected: tomorrow at 5pm → 26/4/2026, 17:00`).
You can ignore it, edit the date manually, or click **clear** in the hint.

### Edit, complete, delete

- **Edit** — click the task title or the **Edit** button on its row. The form
  opens in a modal.
- **Complete / re-open** — click the circle on the left of any row.
- **Delete** — click **Delete** on the row (or from inside the edit modal).
  A small **confirmation pops up** ("Move *Task title* to the Trash?"). Click
  **Move to Trash** to confirm or **Cancel** to back out.

> **Trash, not gone.** Delete sends a task to the **Trash**. From there you
> can **Restore** or **Delete permanently** — a mis-click is never fatal.

---

## 4. Timeline (your main task view)

**Timeline** is where every task in your account lives, **grouped by due
date**. The order is:

1. **Today** (highlighted in green)
2. **Tomorrow**
3. The next few days, by weekday
4. Future dates further out, by full date
5. **Earlier** — overdue dates, most recent first. **Overdue tasks stay on
   their original date group** — Harpr never silently moves them, so you can
   tell at a glance what slipped.
6. **Someday** — tasks with no due date

Each row has the same controls as the dashboard list (toggle, edit, delete).
Click **↓ Export CSV** to download every task as `harpr_tasks.csv` for use
in spreadsheets or your project report.

---

## 5. Calendar

The **Calendar** page shows a monthly grid (powered by FullCalendar).

- Days that have at least one task get a small **green dot** under the date.
- **Click any day** to open a side modal listing every task scheduled for
  that day, with quick toggle buttons and a link to edit each one.
- Use the **prev / next / today** buttons (top-left) to navigate months,
  or switch to the **week / list view** (top-right).
- On mobile the calendar opens as a list view automatically.

---

## 6. Reminders & notifications

Pick a "Remind me" value when creating or editing a task. While Harpr is
open in your browser, it polls every 60 seconds and shows a **browser
notification** when a reminder is due.

The first time, your browser asks you to grant Notification permission. If
you missed the prompt, open **Settings** in the sidebar and click **Request
browser permission** — the page now correctly wires that button to your
browser's permission API and shows a toast confirming the result. You can
also disable reminders entirely from Settings.

> **On mobile**: browser notifications work best on **Android (Chrome /
> Firefox)**. On **iOS** they only appear if Harpr has been added to the
> Home Screen as a web app. Settings shows this note inline so you don't
> miss it.

> Reminders only fire while Harpr is open in a tab. True push notifications
> when the page is closed are listed under **Future work** in the README.

---

## 7. Trash

Deleted tasks live in **Trash** until you remove them permanently. From
this page you can:

- **Restore** a single task back to the active list.
- **Delete permanently** (this also removes any associated time logs).
- **Empty trash** to wipe every soft-deleted task in one click.

---

## 8. Settings

The **Settings** page lets you:

- Toggle **dark mode** (also available from the sidebar's ☀ / ☾ button).
- Toggle reminders on or off.
- Request browser notification permission and see its current status.
- Read the mobile-notifications note (Android vs iOS).

---

## 9. Toast notifications

Every save, edit, completion, deletion, or restore now triggers a small
**toast** in the bottom-right corner (bottom-centre on mobile). Toasts
auto-dismiss after about three seconds. You don't need to do anything with
them — they're just confirmation that the action landed.

---

## 10. Light and dark mode

The **☀ / ☾** button in the bottom-left of the sidebar toggles the theme.
On the very first visit Harpr follows your operating system preference.
After that, your choice is remembered in your browser. Settings has a
matching toggle that does the same thing.

---

## 11. Keyboard shortcuts

| Key   | Action                          |
| ----- | ------------------------------- |
| `N`   | Open the **New task** modal     |
| `T`   | Go to **Timeline**              |
| `C`   | Go to **Calendar**              |
| `D`   | Go to **Today** (dashboard)     |
| `?`   | Show the shortcuts cheat-sheet  |
| `Esc` | Close the topmost modal         |

Shortcuts are disabled while you're typing in a text field.

---

## 12. Mobile

On phones and small tablets:

- The sidebar is replaced by a **bottom navigation bar** with the four
  most-used links (Today, Timeline, Calendar, Settings).
- Cards stack into a single column; the Today list shows about five rows
  before scrolling.
- The base font size is **120%** so text stays readable without zooming.
- Toasts appear from the bottom-centre, above the nav bar.

---

## 13. Tips

- Keep titles short — they're easier to scan in lists.
- Try the natural-language date parser: "**Pay rent on the 1st**" or
  "**Coffee with Mary tomorrow 10am**" fills the date field for you.
- Set a due date and a reminder on every important task; Harpr will pop
  a notification before it's due.
- The **Timeline** export gives you a clean CSV of every task — handy for
  spreadsheets or your project report.
- Don't be afraid to delete: anything you remove sits in **Trash** until you
  empty it.

---

Need help? Check `README.md` for setup details and `BUILD.md` for the
development story.
