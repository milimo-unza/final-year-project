"""
Seed demo data for Harpr.

Idempotent: safe to run multiple times. Removes any prior demo tasks for the
target user (those tagged in their description with ``[demo]``) and re-creates
a fresh, realistic spread covering the current and next month.

Usage:
    venv/bin/python manage.py seed_demo --user=milimo
"""

from __future__ import annotations

import datetime as dt
import random
from typing import List, Tuple

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tasks.models import Task, ActivityLog, UserSettings


DEMO_TAG = "[demo]"

User = get_user_model()


def _aware(local_dt: dt.datetime) -> dt.datetime:
    """Convert a naive datetime in the project's TZ into an aware datetime."""
    tz = timezone.get_current_timezone()
    if timezone.is_aware(local_dt):
        return local_dt
    return timezone.make_aware(local_dt, tz)


# ---------------------------------------------------------------------------
# Demo task templates
# ---------------------------------------------------------------------------

# (title, category, priority, duration_minutes, remind_minutes_before)
SCATTERED: List[Tuple[str, str, str, int, int]] = [
    # work
    ("Finalise quarterly report",       "work",     "high",   90, 15),
    ("Email the supervisor",            "work",     "medium", 15,  5),
    ("Team stand-up",                   "work",     "medium", 30,  5),
    ("Review pull requests",            "work",     "medium", 45, 10),
    ("Prepare slides for stakeholders", "work",     "high",   60, 30),
    ("Sprint planning meeting",         "work",     "high",   60, 15),
    # study
    ("Revise database normalisation",   "study",    "high",   60, 10),
    ("Solve algorithm practice set",    "study",    "medium", 45,  5),
    ("Read Chapter 4 — networking",     "study",    "medium", 40,  5),
    ("Watch FullCalendar tutorial",     "study",    "low",    25,  5),
    # personal
    ("Pay electricity bill",            "personal", "high",   10,  5),
    ("Call mum",                        "personal", "low",    15,  5),
    ("Buy groceries",                   "personal", "medium", 30,  5),
    ("Pick up parcel",                  "personal", "low",    20,  5),
    # health
    ("Morning run (5 km)",              "health",   "medium", 40, 10),
    ("Yoga session",                    "health",   "low",    30,  5),
    ("Drink 2L water",                  "health",   "low",     5,  0),
    ("Bedtime by 10:30pm",              "health",   "medium",  5,  0),
]

URGENT_ITEMS: List[Tuple[str, str]] = [
    ("Submit final project paperwork", "study"),
    ("Renew passport before travel",   "personal"),
]

SOMEDAY_ITEMS: List[Tuple[str, str]] = [
    ("Plan a weekend trip to Livingstone",       "personal"),
    ("Learn basic Spanish",                       "study"),
    ("Re-organise photo library",                "personal"),
    ("Build a personal portfolio site",          "work"),
    ("Try a new healthy recipe each week",       "health"),
]

PAST_COMPLETED: List[Tuple[str, str, int]] = [
    # (title, category, days_ago)
    ("Submit assignment 3", "study",    2),
    ("Doctor's appointment", "health",  3),
    ("Buy birthday gift",    "personal", 5),
    ("File expense report",  "work",     6),
    ("Workout — chest day",  "health",   1),
    ("Weekly groceries",     "personal", 7),
]


def _round_to_30(d: dt.datetime) -> dt.datetime:
    minute = 0 if d.minute < 30 else 30
    return d.replace(minute=minute, second=0, microsecond=0)


class Command(BaseCommand):
    help = "Seed demo Harpr data for a user. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            default="milimo",
            help="Username to seed data for (default: milimo).",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Only remove existing demo tasks; do not re-seed.",
        )

    def handle(self, *args, **opts):
        username = opts["user"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f"User '{username}' does not exist. Create it first "
                f"(e.g. via `manage.py createsuperuser`)."
            )

        # 1. Clean prior demo tasks (hard-delete so they don't litter the trash)
        prior = Task.objects.filter(user=user, description__contains=DEMO_TAG)
        prior_count = prior.count()
        prior.delete()
        # Also wipe related activity-log noise
        ActivityLog.objects.filter(user=user, task_title__endswith=" (demo)").delete()
        self.stdout.write(self.style.WARNING(
            f"Removed {prior_count} prior demo task(s) for {username}."
        ))

        if opts["clean"]:
            return

        # 2. Ensure user settings exist
        UserSettings.for_user(user)

        # Anchor times
        now = timezone.localtime()
        today_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
        random.seed(42)  # deterministic spread

        created = 0

        def make(
            title: str,
            category: str,
            priority: str,
            due: dt.datetime | None,
            duration: int,
            remind: int,
            completed: bool = False,
            completed_at: dt.datetime | None = None,
        ) -> None:
            nonlocal created
            t = Task.objects.create(
                user=user,
                title=title,
                description=f"{DEMO_TAG} demo task seeded by management command.",
                category=category,
                priority=priority,
                due_date=due,
                duration_minutes=duration,
                remind_minutes_before=remind,
                completed=completed,
                completed_at=completed_at,
            )
            ActivityLog.record(user, "created", t)
            if completed:
                ActivityLog.record(user, "completed", t)
            created += 1

        # ---------- TODAY: a handful spread across the day ----------
        today_slots = [9, 10, 11, 12, 14, 15, 16, 17, 19]
        random.shuffle(today_slots)
        today_picks = SCATTERED[:6]
        for i, (title, cat, prio, dur, rem) in enumerate(today_picks):
            hour = today_slots[i % len(today_slots)]
            due = today_local.replace(hour=hour, minute=random.choice([0, 30]))
            make(title, cat, prio, _aware(due), dur, rem)

        # ---------- TOMORROW: a few items ----------
        tomorrow = today_local + dt.timedelta(days=1)
        for (title, cat, prio, dur, rem) in SCATTERED[6:10]:
            due = tomorrow.replace(hour=random.choice([9, 11, 14, 16]),
                                   minute=random.choice([0, 30]))
            make(title, cat, prio, _aware(due), dur, rem)

        # ---------- URGENT (spread across this + next week) ----------
        for i, (title, cat) in enumerate(URGENT_ITEMS):
            offset_days = 1 + i * 3
            due = today_local + dt.timedelta(days=offset_days)
            due = due.replace(hour=10, minute=0)
            make(title, cat, "urgent", _aware(due), 30, 30)

        # ---------- FUTURE: spread across the next 30 days ----------
        for i, (title, cat, prio, dur, rem) in enumerate(SCATTERED[10:]):
            offset_days = 2 + (i * 2) % 28  # 2–29 days out
            base = today_local + dt.timedelta(days=offset_days)
            hour = random.choice([8, 9, 11, 13, 15, 17, 18, 20])
            due = base.replace(hour=hour, minute=random.choice([0, 30]))
            make(title, cat, prio, _aware(due), dur, rem)

        # ---------- NEXT MONTH (a handful into next month) ----------
        next_month_anchor = today_local + dt.timedelta(days=20)
        next_month_items = [
            ("Conference: dev community meetup", "work",     "medium", 120, 60),
            ("Dentist check-up",                 "health",   "high",    45, 60),
            ("Mid-term exam: algorithms",        "study",    "urgent",  90, 60),
            ("Family gathering",                 "personal", "medium", 180, 30),
        ]
        for i, (title, cat, prio, dur, rem) in enumerate(next_month_items):
            due = next_month_anchor + dt.timedelta(days=i * 4)
            due = due.replace(hour=random.choice([10, 14, 18]), minute=0)
            make(title, cat, prio, _aware(due), dur, rem)

        # ---------- SOMEDAY (no due date) ----------
        for (title, cat) in SOMEDAY_ITEMS:
            make(title, cat, "low", None, 0, 0)

        # ---------- PAST COMPLETED ----------
        for (title, cat, days_ago) in PAST_COMPLETED:
            past = today_local - dt.timedelta(days=days_ago)
            past = past.replace(hour=random.choice([9, 12, 15, 18]),
                                minute=random.choice([0, 30]))
            make(
                title, cat, "medium", _aware(past), 30, 5,
                completed=True, completed_at=_aware(past + dt.timedelta(hours=1)),
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} demo task(s) for {username}."
        ))
