"""Template context processors for Harpr."""

from .models import UserSettings

APP_NAME = "Harpr"
APP_TAGLINE = "Task & Activity Planner"


def app_branding(request):
    """Expose brand name + per-user notification setting to templates."""
    notifications_enabled = True
    if request.user.is_authenticated:
        try:
            notifications_enabled = UserSettings.for_user(request.user).notifications_enabled
        except Exception:
            notifications_enabled = True

    return {
        "APP_NAME": APP_NAME,
        "APP_TAGLINE": APP_TAGLINE,
        "notifications_enabled": notifications_enabled,
    }
