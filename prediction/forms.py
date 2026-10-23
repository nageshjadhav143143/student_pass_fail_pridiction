"""Forms with strict numeric validation (server-side; HTML min/max is only a convenience)."""
from django import forms

from .models import Student

PERCENT = {"min_value": 0, "max_value": 100}


class StudentForm(forms.ModelForm):
    """Add a student only (no prediction)."""

    class Meta:
        model = Student
        fields = ["name", "usn", "email", "department", "semester", "section"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_usn(self):
        return self.cleaned_data["usn"].strip().upper()


class PredictionForm(forms.Form):
    # --- student details
    name = forms.CharField(max_length=100, label="Student name")
    usn = forms.CharField(max_length=20, label="USN")
    email = forms.EmailField()
    department = forms.CharField(max_length=50)
    semester = forms.IntegerField(min_value=1, max_value=12)
    section = forms.CharField(max_length=5)
    # --- academic performance
    attendance_percentage = forms.FloatField(label="Attendance (%)", **PERCENT)
    internal_marks = forms.FloatField(label="Internal marks (0-100)", **PERCENT)
    assignment_score = forms.FloatField(label="Assignment score (0-100)", **PERCENT)
    quiz_score = forms.FloatField(label="Quiz score (0-100)", **PERCENT)
    midterm_score = forms.FloatField(label="Midterm score (0-100)", **PERCENT)
    study_hours = forms.FloatField(label="Study hours per day (0-24)", min_value=0, max_value=24)
    previous_sem_percentage = forms.FloatField(label="Previous semester (%)", **PERCENT)
    backlogs = forms.IntegerField(label="Number of backlogs", min_value=0, max_value=50)

    STUDENT_FIELDS = ["name", "usn", "email", "department", "semester", "section"]
    PERFORMANCE_FIELDS = ["attendance_percentage", "internal_marks", "assignment_score",
                          "quiz_score", "midterm_score", "study_hours",
                          "previous_sem_percentage", "backlogs"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
            if isinstance(field, (forms.FloatField, forms.IntegerField)):
                field.widget.attrs.update({"min": field.min_value, "max": field.max_value,
                                           "step": "any" if isinstance(field, forms.FloatField) else "1"})

    def clean_usn(self):
        return self.cleaned_data["usn"].strip().upper()

    def clean_name(self):
        return self.cleaned_data["name"].strip()
