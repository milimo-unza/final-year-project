"""Template context processors for Harpr."""

from .models import UserSettings

APP_NAME = "Harpr"
APP_TAGLINE = "Time & Activity Planner"

# Single source of truth for category dot colours (not user-editable per spec).
CATEGORY_COLORS = {
    "work":     "#3B82F6",   # blue
    "study":    "#8B5CF6",   # purple
    "personal": "#10B981",   # green
    "health":   "#14B8A6",   # teal
}
URGENT_COLOR = "#EF4444"     # red — overrides category colour


def app_branding(request):
    """Expose brand strings, per-user settings, and category labels to templates."""
    notifications_enabled = True
    pomodoro_sound_enabled = True
    pomodoro_notification_enabled = True
    show_public_holidays = True
    category_labels = {"work": "Work", "study": "Study", "personal": "Personal", "health": "Health"}

    if request.user.is_authenticated:
        try:
            s = UserSettings.for_user(request.user)
            notifications_enabled = s.notifications_enabled
            pomodoro_sound_enabled = s.pomodoro_sound_enabled
            pomodoro_notification_enabled = s.pomodoro_notification_enabled
            show_public_holidays = s.show_public_holidays
            category_labels = s.category_labels()
        except Exception:
            pass

    return {
        "APP_NAME": APP_NAME,
        "APP_TAGLINE": APP_TAGLINE,
        "notifications_enabled": notifications_enabled,
        "pomodoro_sound_enabled": pomodoro_sound_enabled,
        "pomodoro_notification_enabled": pomodoro_notification_enabled,
        "show_public_holidays": show_public_holidays,
        "category_labels": category_labels,
        "category_colors": CATEGORY_COLORS,
        "urgent_color": URGENT_COLOR,
    }
