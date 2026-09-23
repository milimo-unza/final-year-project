"""
Seed realistic demo data for Harpr.

Idempotent: safe to run multiple times. Removes any prior demo tasks for the
target user and re-creates a spread covering August to December 2026.

Usage:
    python manage.py seed_demo --user=milimo
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
    tz = timezone.get_current_timezone()
    if timezone.is_aware(local_dt):
        return local_dt
    return timezone.make_aware(local_dt, tz)

# ---------------------------------------------------------------------------
# Task pools. Each tuple: (title, category, priority, duration, remind)
# Study tasks dominate (final year), Health is sparse (realistic).
# ---------------------------------------------------------------------------

STUDY_TASKS: List[Tuple[str, str, str, int, int]] = [
    ("Revise database normalisation",       "study", "high",   60, 15),
    ("Read CSC 3712 lecture notes",         "study", "medium", 45, 10),
    ("Solve algorithm practice set",        "study", "high",   50, 15),
    ("Watch networking tutorial",           "study", "low",    30,  5),
    ("Write up lab report 4",               "study", "high",   90, 30),
    ("Group project meeting",               "study", "medium", 60, 15),
    ("Revise operating systems concepts",   "study", "high",   60, 15),
    ("Prepare for programming quiz",        "study", "medium", 40, 10),
    ("Read chapter on software testing",    "study", "medium", 30,  5),
    ("Revise UML diagrams",                 "study", "low",    25,  5),
    ("Work on dissertation draft",          "study", "high",  120, 30),
    ("Review lecture slides",               "study", "low",    20,  0),
    ("Practise SQL queries",                "study", "medium", 45, 10),
    ("Prepare presentation slides",         "study", "high",   60, 20),
    ("Study for Advanced Databases test",   "study", "high",   90, 30),
    ("Read research paper on ML",           "study", "medium", 45, 10),
    ("Revise data structures",              "study", "high",   60, 15),
    ("Complete assignment 3",               "study", "high",   90, 30),
    ("Watch recorded lecture",              "study", "low",    45,  5),
    ("Revise compiler design basics",       "study", "medium", 50, 10),
    ("Prepare for group presentation",      "study", "high",   60, 15),
    ("Read chapter on cryptography",        "study", "medium", 40,  5),
    ("Practise Python exercises",           "study", "low",    30,  5),
    ("Revise computer architecture",        "study", "medium", 45, 10),
    ("Draft literature review section",     "study", "high",   90, 30),
    ("Review past exam papers",             "study", "medium", 60, 15),
    ("Study session at library",            "study", "medium", 120, 15),
    ("Attend extra tutorial",               "study", "medium", 60, 10),
    ("Write weekly reflection",             "study", "low",    20,  0),
    ("Revise maths for computing",          "study", "high",   50, 15),
]

WORK_TASKS: List[Tuple[str, str, str, int, int]] = [
    ("Part-time shift",                     "work", "medium", 240, 60),
    ("Email supervisor",                    "work", "high",   15,  5),
    ("Update CV",                           "work", "medium", 30, 10),
    ("Attend team stand-up",                "work", "medium", 30, 10),
    ("Write weekly report",                 "work", "medium", 45, 15),
    ("Review pull request",                 "work", "low",    30,  5),
    ("Fix bug in project code",             "work", "high",   60, 15),
    ("Client call",                         "work", "high",   30, 15),
    ("Prepare invoices",                    "work", "medium", 40, 10),
    ("Read technical article",              "work", "low",    20,  0),
    ("Attend coding meetup",                "work", "low",   120, 30),
    ("Follow up on application",            "work", "medium", 15,  5),
    ("Review job posting",                  "work", "low",    20,  0),
    ("Practise interview questions",        "work", "medium", 45, 10),
    ("Networking event",                    "work", "low",   120, 30),
]

PERSONAL_TASKS: List[Tuple[str, str, str, int, int]] = [
    ("Call mum",                            "personal", "low",    15,  0),
    ("Buy groceries",                       "personal", "medium", 45, 10),
    ("Pay electricity bill",                "personal", "high",   10,  5),
    ("Do laundry",                          "personal", "low",    60,  0),
    ("Clean room",                          "personal", "low",    40,  0),
    ("Top up phone credit",                 "personal", "low",     5,  0),
    ("Return library books",                "personal", "medium", 30, 10),
    ("Get haircut",                         "personal", "low",    45,  0),
    ("Visit grandparents",                  "personal", "medium", 180, 60),
    ("Buy birthday gift for Chanda",        "personal", "high",   30, 15),
    ("Meet a friend for coffee",            "personal", "low",    60, 15),
    ("Pick up parcel from post office",     "personal", "medium", 30,  5),
    ("Fix broken charger",                  "personal", "low",    30,  0),
    ("Buy new shoes",                       "personal", "low",    90,  0),
    ("Sort out bank account",               "personal", "medium", 45, 10),
    ("Renew student ID",                    "personal", "high",   60, 30),
    ("Attend church service",               "personal", "low",   120, 15),
    ("Movie night with friends",            "personal", "low",   180,  0),
    ("Call dad",                            "personal", "low",    20,  0),
    ("Cook dinner for flatmates",           "personal", "medium", 90, 15),
    ("B's wedding",                         "personal", "high",  360, 60),
    ("Buy wedding outfit",                  "personal", "high",   90, 30),
    ("Plan weekend trip",                   "personal", "low",    60,  0),
]

HEALTH_TASKS: List[Tuple[str, str, str, int, int]] = [
    ("Morning run",                         "health", "medium", 40, 10),
    ("Go to gym",                           "health", "medium", 60, 15),
    ("Yoga session",                        "health", "low",    30,  5),
    ("Drink 2L water",                      "health", "low",     5,  0),
    ("Early night",                         "health", "medium",  5,  0),
    ("Walk to campus",                      "health", "low",    30,  0),
    ("Doctor's appointment",                "health", "high",   45, 60),
    ("Buy vitamins",                        "health", "low",    20,  0),
    ("Stretch for 10 minutes",              "health", "low",    10,  0),
    ("Meal prep for the week",              "health", "medium", 90, 15),
]

URGENT_ITEMS: List[Tuple[str, str]] = [
    ("Submit CSC 3712 presentation", "study"),
    ("Hand in assignment 3",         "study"),
    ("Pay rent",                     "personal"),
    ("Renew passport",               "personal"),
    ("Submit final dissertation",    "study"),
]

SOMEDAY_ITEMS: List[Tuple[str, str]] = [
    ("Learn basic Spanish",                  "study"),
    ("Re-organise photo library",            "personal"),
    ("Build a personal portfolio site",      "work"),
    ("Try a new recipe each week",           "health"),
    ("Read a non-course book",               "personal"),
    ("Plan a trip to Livingstone",           "personal"),
    ("Learn to play a song on guitar",       "personal"),
    ("Start a blog",                         "personal"),
    ("Learn Figma basics",                   "work"),
    ("Volunteer somewhere",                  "personal"),
]

# Named events pinned to specific dates
FIXED_EVENTS: List[Tuple[str, str, str, str, int]] = [
    # (ISO date, title, category, priority, duration)
    ("2026-10-12", "CSC 3712 Advanced Databases presentation", "study", "high", 60),
    ("2026-10-31", "B's wedding", "personal", "high", 360),
]

class Command(BaseCommand):
    help = "Seed realistic demo data for Harpr. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--user", default="milimo",
                            help="Username to seed (default: milimo)")
        parser.add_argument("--clean", action="store_true",
                            help="Only remove prior demo tasks.")

    def handle(self, *args, **opts):
        username = opts["user"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist.")

        prior = Task.objects.filter(user=user, description__contains=DEMO_TAG)
        prior_count = prior.count()
        prior.delete()
        ActivityLog.objects.filter(user=user, task_title__endswith=" (demo)").delete()
        self.stdout.write(self.style.WARNING(
            f"Removed {prior_count} prior demo task(s)."
        ))

        if opts["clean"]:
            return

        UserSettings.for_user(user)
        random.seed(2026)

        today = timezone.localdate()
        start = dt.date(2026, 8, 1)
        end = dt.date(2026, 12, 31)

        created = 0
        completed_count = 0

        def make(title, category, priority, due, duration, remind,
                 completed=False):
            nonlocal created, completed_count
            t = Task.objects.create(
                user=user,
                title=title,
                description=f"{DEMO_TAG} seeded",
                category=category,
                priority=priority,
                due_date=due,
                duration_minutes=duration,
                remind_minutes_before=remind,
                completed=completed,
                completed_at=due + dt.timedelta(hours=1) if completed and due else None,
            )
            ActivityLog.record(user, "created", t)
            if completed:
                ActivityLog.record(user, "completed", t)
                completed_count += 1
            created += 1

        # --- 1. Daily-generated tasks across Aug-Dec ---
        current = start
        while current <= end:
            # Weekday picks: study mostly, work on specific days, health rare
            weekday = current.weekday()  # 0=Mon

            # Skip most Sundays - light day
            if weekday == 6 and random.random() < 0.7:
                current += dt.timedelta(days=1)
                continue

            num_tasks = random.randint(2, 4)

            for _ in range(num_tasks):
                # Category mix: study 50%, work 20%, personal 22%, health 8%
                r = random.random()
                if r < 0.50:
                    pool = STUDY_TASKS
                elif r < 0.70:
                    pool = WORK_TASKS
                elif r < 0.92:
                    pool = PERSONAL_TASKS
                else:
                    pool = HEALTH_TASKS

                title, cat, prio, dur, rem = random.choice(pool)
                hour = random.choice([8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20])
                minute = random.choice([0, 15, 30, 45])
                due_local = dt.datetime.combine(current, dt.time(hour, minute))

                # Older tasks completed, newer pending
                if current < today - dt.timedelta(days=14):
                    completed = random.random() < 0.90
                elif current < today - dt.timedelta(days=3):
                    completed = random.random() < 0.65
                elif current < today:
                    completed = random.random() < 0.45
                else:
                    completed = False

                # Add a small offset per task on the same day
                due_local += dt.timedelta(minutes=random.randint(0, 45))
                make(title, cat, prio, _aware(due_local), dur, rem,
                     completed=completed)

            current += dt.timedelta(days=1)

        # --- 2. Fixed named events ---
        for iso, title, cat, prio, dur in FIXED_EVENTS:
            d = dt.date.fromisoformat(iso)
            due = _aware(dt.datetime.combine(d, dt.time(9, 0)))
            completed = d < today
            make(title, cat, prio, due, dur, 30, completed=completed)

        # --- 3. A handful of overdue items (some not completed) ---
        overdue_items = [
            ("Chase up missing assignment marks",  "study",    "high",   30),
            ("Email lecturer about project topic", "study",    "high",   15),
            ("Return borrowed notes to Chanda",    "personal", "medium", 20),
            ("Pay outstanding internet bill",      "personal", "high",   15),
        ]
        for i, (title, cat, prio, dur) in enumerate(overdue_items):
            d = today - dt.timedelta(days=2 + i * 3)
            due = _aware(dt.datetime.combine(d, dt.time(10, 0)))
            make(title, cat, prio, due, dur, 15, completed=False)

        # --- 4. Upcoming urgent items (next 3 weeks) ---
        for i, (title, cat) in enumerate(URGENT_ITEMS):
            d = today + dt.timedelta(days=2 + i * 4)
            due = _aware(dt.datetime.combine(d, dt.time(9, 0)))
            make(title, cat, "high", due, 60, 30, completed=False)

        # --- 5. Someday bucket (no due dates) ---
        for title, cat in SOMEDAY_ITEMS:
            t = Task.objects.create(
                user=user,
                title=title,
                description=f"{DEMO_TAG} seeded",
                category=cat,
                priority="low",
                due_date=None,
            )
            ActivityLog.record(user, "created", t)
            created += 1

        # --- 6. A few future completions (unrealistic but demonstrates the feature) ---
        # Skip these - no need to fabricate.

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} task(s) ({completed_count} completed) for {username}."
        ))
