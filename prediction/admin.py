from django.contrib import admin

from .models import Prediction, Student, StudentPerformance

admin.site.site_header = "Student Prediction Admin"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "usn", "department", "semester", "section", "created_at")
    list_filter = ("department", "semester")
    search_fields = ("name", "usn")


@admin.register(StudentPerformance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("student", "attendance_percentage", "internal_marks", "backlogs", "created_at")
    search_fields = ("student__name", "student__usn")


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("student", "prediction", "pass_probability", "risk_level", "prediction_date")
    list_filter = ("prediction", "risk_level")
    search_fields = ("student__name", "student__usn")
