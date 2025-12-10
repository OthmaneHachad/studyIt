from django import forms
from django.utils import timezone
from .models import StudySession


class StudySessionForm(forms.ModelForm):
    """Form for TA/session hosts to create study sessions."""

    class Meta:
        model = StudySession
        fields = ["title", "course", "description", "location", "room_number", "start_time", "end_time", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., CS2340 Exam Review"}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Topics, expectations, what students should bring...",
                    "rows": 4,
                }
            ),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Library 3rd Floor"}),
            "room_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 304"}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        if start and start < timezone.now():
            raise forms.ValidationError("Start time must be in the future.")
        return cleaned

