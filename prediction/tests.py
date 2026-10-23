"""Run with:  python manage.py test"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from . import ml_model
from .models import Prediction, Student, StudentPerformance

GOOD = {"name": "Rahul Kumar", "usn": "1xx23cs001", "email": "rahul@example.com",
        "department": "CSE", "semester": 5, "section": "A",
        "attendance_percentage": 85, "internal_marks": 78, "assignment_score": 80,
        "quiz_score": 75, "midterm_score": 72, "study_hours": 4.5,
        "previous_sem_percentage": 74, "backlogs": 0}
WEAK = dict(GOOD, usn="1XX23CS002", name="Weak Student", attendance_percentage=45,
            internal_marks=22, assignment_score=30, quiz_score=20, midterm_score=18,
            study_hours=0.5, previous_sem_percentage=35, backlogs=4)


class RiskLevelTests(TestCase):
    def test_thresholds(self):
        self.assertEqual(ml_model.risk_level(0.90), "LOW")
        self.assertEqual(ml_model.risk_level(0.75), "LOW")
        self.assertEqual(ml_model.risk_level(0.60), "MEDIUM")
        self.assertEqual(ml_model.risk_level(0.50), "MEDIUM")
        self.assertEqual(ml_model.risk_level(0.49), "HIGH")


class ModelTests(TestCase):
    def test_probabilities_sum_to_100(self):
        r = ml_model.predict({k: GOOD[k] for k in ml_model.FEATURES})
        self.assertAlmostEqual(r["pass_probability"] + r["fail_probability"], 100, delta=0.05)
        self.assertIn(r["prediction"], ("PASS", "FAIL"))

    def test_strong_beats_weak(self):
        strong = ml_model.predict({k: GOOD[k] for k in ml_model.FEATURES})
        weak = ml_model.predict({k: WEAK[k] for k in ml_model.FEATURES})
        self.assertGreater(strong["pass_probability"], weak["pass_probability"])

    def test_metrics_files_exist(self):
        self.assertIsNotNone(ml_model.get_metrics())
        self.assertTrue(ml_model.get_importance())


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_user("teacher", password="pass12345!")

    def login(self):
        self.client.login(username="teacher", password="pass12345!")

    def test_public_pages(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_login_required(self):
        for name in ["dashboard", "students", "predict", "prediction_history", "analytics", "model_info"]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn("/login/", r["Location"])

    def test_all_pages_render_when_logged_in(self):
        self.login()
        for name in ["dashboard", "students", "add_student", "predict", "prediction_history",
                     "analytics", "model_info"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_prediction_flow_saves_everything(self):
        self.login()
        r = self.client.post(reverse("predict"), GOOD)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentPerformance.objects.count(), 1)
        pred = Prediction.objects.get()
        self.assertEqual(Student.objects.get().usn, "1XX23CS001")  # normalised to upper-case
        page = self.client.get(reverse("prediction_result", args=[pred.pk]))
        self.assertContains(page, "Rahul Kumar")

    def test_same_usn_reuses_student(self):
        self.login()
        self.client.post(reverse("predict"), GOOD)
        self.client.post(reverse("predict"), GOOD)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Prediction.objects.count(), 2)

    def test_high_risk_shows_warning(self):
        self.login()
        self.client.post(reverse("predict"), WEAK)
        pred = Prediction.objects.get()
        page = self.client.get(reverse("prediction_result", args=[pred.pk]))
        if pred.risk_level == "HIGH":
            self.assertContains(page, "high risk of failing")

    def test_invalid_values_rejected(self):
        self.login()
        for field, bad in [("attendance_percentage", 120), ("internal_marks", -5),
                           ("study_hours", 30), ("backlogs", -1), ("quiz_score", "abc")]:
            r = self.client.post(reverse("predict"), dict(GOOD, **{field: bad}))
            self.assertEqual(r.status_code, 200, field)
            self.assertEqual(Student.objects.count(), 0, field)

    def test_empty_form_rejected(self):
        self.login()
        r = self.client.post(reverse("predict"), {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_filters(self):
        self.login()
        self.client.post(reverse("predict"), GOOD)
        self.client.post(reverse("predict"), WEAK)
        r = self.client.get(reverse("students"), {"q": "Weak"})
        self.assertContains(r, "Weak Student")
        self.assertNotContains(r, "Rahul Kumar")
        self.assertEqual(self.client.get(reverse("students"), {"result": "PASS", "risk": "LOW",
                                                               "department": "CSE", "semester": "5"}).status_code, 200)

    def test_delete_requires_post(self):
        self.login()
        self.client.post(reverse("predict"), GOOD)
        s = Student.objects.get()
        self.assertEqual(self.client.get(reverse("delete_student", args=[s.pk])).status_code, 405)
        self.client.post(reverse("delete_student", args=[s.pk]))
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Prediction.objects.count(), 0)  # cascade

    def test_missing_model_shows_friendly_error(self):
        self.login()
        ml_model.load_model.cache_clear()
        with override_settings(MODEL_PATH=self_missing_path()):
            r = self.client.post(reverse("predict"), GOOD)
        ml_model.load_model.cache_clear()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "trained model file was not found")
        self.assertEqual(Student.objects.count(), 0)


def self_missing_path():
    from pathlib import Path
    return Path("/nonexistent/model.pkl")
