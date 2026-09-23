# Harpr - User Manual

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
sidebar (desktop) or from the **Settings** screen (mobile).

---

## 2. Today (the dashboard)

The Today page is deliberately focused on what you need right now. From
top to bottom:

- **Quick add bar** - type a title and press Enter to create a task.
  Natural language works: "Pay rent tomorrow", "Meeting Friday 3pm". If
  a date is detected, it goes on the task automatically.
- **Overdue** - tasks that were due before today and aren't done yet.
  Each has a small arrow button to push it to today. This section only
  appears if there's something overdue.
- **Today** - pending tasks due today, sorted by time.
- **Tomorrow** - a preview of what's due tomorrow.
- **Someday** - tasks with no due date. They sit here until you give them one.

On the right column:

- **Pending count** - open tasks in total.
- **Insights** - three charts with tabs to switch between them. Time per
  category, activity over the last week, and completed vs pending tasks
  per category. Harpr remembers which chart you looked at last.
- **Recently completed** - the last five tasks you finished.

Click any task title to open the edit modal.

---

## 3. Adding and editing tasks

Click **New task** (top-right of most pages) or use the quick add bar
on the Today page.

Fields:

- **Title** (required)
- **When** - date picker, plus hour and minute dropdowns in 24-hour
  format. Minute steps are 5 minutes. Leave the date empty to send the
  task to Someday.
- **Duration (minutes)** - optional, used to compute an end time.
- **Category** - Work, Study, Personal, or Health.
- **Priority** - High, Medium, or Low.
- **Reminder** - currently unused. Will be removed.

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

- **Complete** - click the circle on the left of any task row. On the
  dashboard, the row disappears because completed tasks aren't pending.
- **Edit** - click the task title. The edit modal opens.
- **Delete** - from inside the edit modal, click Delete. A confirmation
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

**Scroll-to-today button** - the circular icon in the page header scrolls
back to today when you've scrolled away.

**Export CSV** - downloads `harpr_tasks.csv` with every task in a
spreadsheet format.

---

## 5. Calendar

The **Calendar** page has three views, switchable with the buttons in
the toolbar:

- **Month** - a grid. Each day shows coloured chips for its tasks, up to
  three per day. Days with more than three show a "+N more" link.
- **Week** - seven columns, one per day, with all tasks listed. Sunday
  to Saturday.
- **List** - a chronological list of upcoming days and their tasks.

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

- **Pie** - time logged per category
- **Activity** - minutes logged per day, last seven days
- **Tasks** - completed vs pending per category

Switching tabs is instant. The choice persists across sessions.

---

## 8. Activity log

Every action you take on a task - created, edited, completed, re-opened,
deleted - is recorded. The last 30 are visible from the Activity link in
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

- Use the quick add bar for anything you think of in the moment - you
  can always edit details later.
- Set a duration on tasks you actually want to track. Tasks without a
  duration can still have time logged against them, but you won't see an
  end time.
- The Timeline's CSV export is useful for putting together a report or
  reviewing what you've done over a period.
- If something looks wrong after an edit, reload the page. Every list
  reflects the database on page load.
