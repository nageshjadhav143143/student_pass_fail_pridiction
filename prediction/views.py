from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.db.models import Avg, Count, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import ml_model
from .forms import PredictionForm, StudentForm
from .models import Prediction, Student, StudentPerformance


# ------------------------------------------------------------------ helpers
def students_with_latest():
    """Every student annotated with their most recent prediction + performance."""
    latest_pred = Prediction.objects.filter(student=OuterRef("pk")).order_by(
        "-prediction_date", "-prediction_id")
    latest_perf = StudentPerformance.objects.filter(student=OuterRef("pk")).order_by(
        "-created_at", "-performance_id")
    return Student.objects.annotate(
        last_prediction=Subquery(latest_pred.values("prediction")[:1]),
        last_pass_prob=Subquery(latest_pred.values("pass_probability")[:1]),
        last_risk=Subquery(latest_pred.values("risk_level")[:1]),
        last_pred_date=Subquery(latest_pred.values("prediction_date")[:1]),
        last_pred_id=Subquery(latest_pred.values("prediction_id")[:1]),
        last_attendance=Subquery(latest_perf.values("attendance_percentage")[:1]),
        last_internal=Subquery(latest_perf.values("internal_marks")[:1]),
    )


# ------------------------------------------------------------------ pages
def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    qs = students_with_latest()
    predicted = qs.filter(last_prediction__isnull=False)
    stats = {
        "total": qs.count(),
        "predicted": predicted.count(),
        "passed": predicted.filter(last_prediction="PASS").count(),
        "failed": predicted.filter(last_prediction="FAIL").count(),
        "high_risk": predicted.filter(last_risk="HIGH").count(),
        "avg_attendance": qs.aggregate(a=Avg("last_attendance"))["a"] or 0,
    }
    recent = Prediction.objects.select_related("student")[:6]
    return render(request, "dashboard.html", {"stats": stats, "recent": recent})


@login_required
def add_student(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, f"Student {student.name} added. You can now run a prediction.")
        return redirect(f"/predict/?student={student.pk}")
    return render(request, "add_student.html", {"form": form})


@login_required
def predict_view(request):
    initial = {}
    student_id = request.GET.get("student")
    if student_id and student_id.isdigit():
        student = Student.objects.filter(pk=student_id).first()
        if student:
            initial = {f: getattr(student, f) for f in PredictionForm.STUDENT_FIELDS}

    form = PredictionForm(request.POST or None, initial=initial)
    if request.method == "POST":
        if not form.is_valid():
            messages.error(request, "Please correct the highlighted fields.")
        else:
            data = form.cleaned_data
            try:
                result = ml_model.predict({f: data[f] for f in ml_model.FEATURES})
            except ml_model.ModelUnavailableError as exc:
                messages.error(request, str(exc))
                return render(request, "student_form.html", {"form": form})
            try:
                with transaction.atomic():  # all three rows are saved, or none
                    student, _ = Student.objects.update_or_create(
                        usn=data["usn"],
                        defaults={f: data[f] for f in PredictionForm.STUDENT_FIELDS if f != "usn"})
                    perf = StudentPerformance.objects.create(
                        student=student, **{f: data[f] for f in PredictionForm.PERFORMANCE_FIELDS})
                    pred = Prediction.objects.create(student=student, performance=perf, **result)
            except DatabaseError:
                messages.error(request, "A database error occurred. Nothing was saved - please try again.")
                return render(request, "student_form.html", {"form": form})
            return redirect("prediction_result", pk=pred.pk)
    return render(request, "student_form.html", {"form": form})


@login_required
def prediction_result(request, pk):
    pred = get_object_or_404(Prediction.objects.select_related("student", "performance"), pk=pk)
    perf = pred.performance
    details = [
        ("Attendance", f"{perf.attendance_percentage:g}%"),
        ("Internal Marks", f"{perf.internal_marks:g}"),
        ("Assignment Score", f"{perf.assignment_score:g}"),
        ("Quiz Score", f"{perf.quiz_score:g}"),
        ("Midterm Score", f"{perf.midterm_score:g}"),
        ("Study Hours", f"{perf.study_hours:g}"),
        ("Previous Semester", f"{perf.previous_sem_percentage:g}%"),
        ("Backlogs", perf.backlogs),
    ]
    importance = list(ml_model.get_importance().items())[:5]
    return render(request, "prediction_result.html",
                  {"pred": pred, "perf": perf, "details": details, "importance": importance})


@login_required
def students(request):
    qs = students_with_latest()
    q = request.GET.get("q", "").strip()
    dept = request.GET.get("department", "")
    sem = request.GET.get("semester", "")
    result = request.GET.get("result", "")
    risk = request.GET.get("risk", "")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(usn__icontains=q))
    if dept:
        qs = qs.filter(department=dept)
    if sem.isdigit():
        qs = qs.filter(semester=int(sem))
    if result in ("PASS", "FAIL"):
        qs = qs.filter(last_prediction=result)
    if risk in ("LOW", "MEDIUM", "HIGH"):
        qs = qs.filter(last_risk=risk)
    ctx = {
        "students": qs.order_by("name"),
        "departments": Student.objects.order_by("department").values_list(
            "department", flat=True).distinct(),
        "semesters": Student.objects.order_by("semester").values_list(
            "semester", flat=True).distinct(),
        "f": {"q": q, "department": dept, "semester": sem, "result": result, "risk": risk},
    }
    return render(request, "students.html", ctx)


@login_required
@require_POST
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.delete()  # cascades to performance + predictions
    messages.success(request, "Student and related records deleted.")
    return redirect("students")


@login_required
def prediction_history(request):
    qs = Prediction.objects.select_related("student")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(student__name__icontains=q) | Q(student__usn__icontains=q))
    return render(request, "prediction_history.html", {"predictions": qs[:500], "q": q})


@login_required
def analytics(request):
    predicted = students_with_latest().filter(last_prediction__isnull=False)
    passed, failed = Q(last_prediction="PASS"), Q(last_prediction="FAIL")
    avg = predicted.aggregate(
        att_pass=Avg("last_attendance", filter=passed), att_fail=Avg("last_attendance", filter=failed),
        int_pass=Avg("last_internal", filter=passed), int_fail=Avg("last_internal", filter=failed))
    risk = predicted.aggregate(
        low=Count("pk", filter=Q(last_risk="LOW")), medium=Count("pk", filter=Q(last_risk="MEDIUM")),
        high=Count("pk", filter=Q(last_risk="HIGH")))
    dept = predicted.values("department").annotate(
        passed=Count("pk", filter=passed), failed=Count("pk", filter=failed)).order_by("department")
    scatter = [{"x": round(a, 1), "y": round(p, 1), "result": r}
               for a, p, r in predicted.values_list("last_attendance", "last_pass_prob", "last_prediction")]
    data = {
        "pass_fail": [predicted.filter(passed).count(), predicted.filter(failed).count()],
        "attendance": [round(avg["att_pass"] or 0, 1), round(avg["att_fail"] or 0, 1)],
        "internal": [round(avg["int_pass"] or 0, 1), round(avg["int_fail"] or 0, 1)],
        "risk": [risk["low"], risk["medium"], risk["high"]],
        "departments": [d["department"] for d in dept],
        "dept_pass": [d["passed"] for d in dept],
        "dept_fail": [d["failed"] for d in dept],
        "scatter": scatter,
        "importance": ml_model.get_importance(),
    }
    return render(request, "analytics.html", {"data": data, "has_data": bool(scatter)})


@login_required
def model_info(request):
    return render(request, "model_info.html", {
        "metrics": ml_model.get_metrics(), "importance": ml_model.get_importance()})


# ------------------------------------------------------------------ errors
def error_404(request, exception=None):
    return render(request, "error.html", {"code": 404, "message": "That page could not be found."}, status=404)


def error_500(request):
    return render(request, "error.html",
                  {"code": 500, "message": "Something went wrong on our side. Please try again."}, status=500)
