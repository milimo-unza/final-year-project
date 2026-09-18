from django import forms
from .models import Task, UserSettings


class TaskForm(forms.ModelForm):
    remind_minutes_before = forms.TypedChoiceField(
        coerce=int,
        choices=Task.REMIND_CHOICES,
        required=False,
        initial=0,
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


class SettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ("notifications_enabled",)
        labels = {
            "notifications_enabled": "Enable browser notifications",
        }
