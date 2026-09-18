from django import forms
from .models import Task, UserSettings


class TaskForm(forms.ModelForm):
    remind_minutes_before = forms.TypedChoiceField(
        coerce=int,
        choices=Task.REMIND_CHOICES,
        required=False,
        initial=5,
        label="Remind me",
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "due_date",
            "duration_minutes",
            "category",
            "priority",
            "remind_minutes_before",
        )
        widgets = {
            "due_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
            "duration_minutes": forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 60"}),
            "title": forms.TextInput(attrs={"data-chrono": "1", "autocomplete": "off"}),
        }
        labels = {
            "duration_minutes": "Duration (minutes)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["due_date"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["duration_minutes"].required = False
        self.fields["due_date"].required = False  # tasks can be "Someday"


class SettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = (
            "notifications_enabled",
            "pomodoro_sound_enabled",
            "pomodoro_notification_enabled",
            "show_public_holidays",
            "category_work_label",
            "category_study_label",
            "category_personal_label",
            "category_health_label",
        )
        labels = {
            "notifications_enabled": "Enable browser notifications",
            "pomodoro_sound_enabled": "Play a sound when the Pomodoro finishes",
            "pomodoro_notification_enabled": "Show a browser notification when the Pomodoro finishes",
            "show_public_holidays": "Show Zambian public holidays on the calendar",
            "category_work_label": "Work label",
            "category_study_label": "Study label",
            "category_personal_label": "Personal label",
            "category_health_label": "Health label",
        }
