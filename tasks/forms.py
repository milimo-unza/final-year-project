from django import forms
from .models import Task, TimeLog, UserSettings


HOUR_CHOICES = [(f"{h:02d}", f"{h:02d}") for h in range(24)]
MINUTE_CHOICES = [(f"{m:02d}", f"{m:02d}") for m in range(0, 60, 5)]


class TaskForm(forms.ModelForm):
    # --- replaced datetime-local widget with two helper dropdowns ---
    due_date_only = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Date",
    )
    due_hour = forms.ChoiceField(
        required=False,
        choices=[("", "--")] + HOUR_CHOICES,
        label="Hour",
    )
    due_minute = forms.ChoiceField(
        required=False,
        choices=[("", "--")] + MINUTE_CHOICES,
        label="Minute",
    )
    remind_minutes_before = forms.TypedChoiceField(
        coerce=int,
        choices=Task.REMIND_CHOICES,
        required=False,
        initial=0,
        label="Reminder",
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "due_date",
            "duration_minutes",
            "category",
            "priority",
            "remind_minutes_before",
        )
        widgets = {
            "title": forms.TextInput(attrs={"autocomplete": "off", "placeholder": "What needs doing?"}),
            "due_date": forms.HiddenInput(),
            "duration_minutes": forms.NumberInput(attrs={"min": 0, "placeholder": "Minutes"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # duration not required
        self.fields["duration_minutes"].required = False
        # Set initial values from the instance's due_date on edit
        if self.instance and self.instance.pk and self.instance.due_date:
            local = self.instance.due_date
            # Django gives aware datetimes; use localtime for display
            from django.utils import timezone
            local = timezone.localtime(local)
            self.fields["due_date_only"].initial = local.date()
            self.fields["due_hour"].initial = f"{local.hour:02d}"
            self.fields["due_minute"].initial = f"{local.minute // 15 * 15:02d}"

    def clean(self):
        cleaned = super().clean()
        date_only = cleaned.get("due_date_only")
        hour = cleaned.get("due_hour")
        minute = cleaned.get("due_minute")

        if date_only and hour and minute:
            from datetime import datetime
            from django.utils import timezone
            naive = datetime(
                date_only.year, date_only.month, date_only.day,
                int(hour), int(minute),
            )
            cleaned["due_date"] = timezone.make_aware(
                naive, timezone.get_current_timezone()
            )
        elif date_only and not hour:
            # Date given, no time: default 17:00
            from datetime import datetime
            from django.utils import timezone
            naive = datetime(date_only.year, date_only.month, date_only.day, 17, 0)
            cleaned["due_date"] = timezone.make_aware(
                naive, timezone.get_current_timezone()
            )
        elif not date_only:
            # No date given: Someday bucket.
            cleaned["due_date"] = None

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if "due_date" in self.cleaned_data:
            instance.due_date = self.cleaned_data["due_date"]
        if commit:
            instance.save()
        return instance


class LogTimeForm(forms.ModelForm):
    """Log time spent on a task. Simple hours/minutes split."""
    hours = forms.IntegerField(min_value=0, max_value=23, required=False, initial=0,
                               widget=forms.NumberInput(attrs={"min": 0, "max": 23}))
    minutes_part = forms.IntegerField(min_value=0, max_value=59, required=False, initial=0,
                                      widget=forms.NumberInput(attrs={"min": 0, "max": 59}))

    class Meta:
        model = TimeLog
        fields = ("note",)
        widgets = {
            "note": forms.TextInput(attrs={"placeholder": "Optional note", "maxlength": 200}),
        }

    def clean(self):
        cleaned = super().clean()
        h = cleaned.get("hours") or 0
        m = cleaned.get("minutes_part") or 0
        total = h * 60 + m
        if total <= 0:
            raise forms.ValidationError("Please enter a duration greater than zero.")
        cleaned["minutes"] = total
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.minutes = self.cleaned_data["minutes"]
        if commit:
            instance.save()
        return instance

class LogTimeForm(forms.ModelForm):
    """Log time spent on a task."""
    hours = forms.IntegerField(min_value=0, max_value=23, required=False, initial=0)
    minutes_part = forms.IntegerField(min_value=0, max_value=59, required=False, initial=0)

    class Meta:
        model = TimeLog
        fields = ("note",)
        widgets = {
            "note": forms.TextInput(attrs={"placeholder": "Optional note", "maxlength": 200}),
        }

    def clean(self):
        cleaned = super().clean()
        h = cleaned.get("hours") or 0
        m = cleaned.get("minutes_part") or 0
        total = h * 60 + m
        if total <= 0:
            raise forms.ValidationError("Please enter a duration greater than zero.")
        cleaned["minutes"] = total
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.minutes = self.cleaned_data["minutes"]
        if commit:
            instance.save()
        return instance


