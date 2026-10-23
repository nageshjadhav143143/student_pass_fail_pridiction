"""
Database design:  Student (1) --- (N) StudentPerformance (1) --- (N) Prediction
A Student also has a direct FK from Prediction so history can be queried easily.
All tables are created through the Django ORM (no raw SQL).
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def percent_field(label):
    return models.FloatField(label, validators=[MinValueValidator(0), MaxValueValidator(100)])


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    usn = models.CharField("USN", max_length=20, unique=True)
    email = models.EmailField()
    department = models.CharField(max_length=50)
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)])
    section = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.usn})"


class StudentPerformance(models.Model):
    performance_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="performances")
    attendance_percentage = percent_field("Attendance %")
    internal_marks = percent_field("Internal marks")
    assignment_score = percent_field("Assignment score")
    quiz_score = percent_field("Quiz score")
    midterm_score = percent_field("Midterm score")
    study_hours = models.FloatField(
        "Study hours / day", validators=[MinValueValidator(0), MaxValueValidator(24)])
    previous_sem_percentage = percent_field("Previous semester %")
    backlogs = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(50)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Performance #{self.performance_id} - {self.student.usn}"


class Prediction(models.Model):
    PASS, FAIL = "PASS", "FAIL"
    RESULT_CHOICES = [(PASS, "Pass"), (FAIL, "Fail")]
    RISK_CHOICES = [("LOW", "Low risk"), ("MEDIUM", "Medium risk"), ("HIGH", "High risk")]

    prediction_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="predictions")
    performance = models.ForeignKey(StudentPerformance, on_delete=models.CASCADE,
                                    related_name="predictions")
    prediction = models.CharField(max_length=4, choices=RESULT_CHOICES)
    pass_probability = models.FloatField()   # stored as 0-100
    fail_probability = models.FloatField()   # stored as 0-100
    risk_level = models.CharField(max_length=6, choices=RISK_CHOICES)
    prediction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-prediction_date", "-prediction_id"]

    def __str__(self):
        return f"{self.student.usn}: {self.prediction} ({self.pass_probability:.0f}%)"
