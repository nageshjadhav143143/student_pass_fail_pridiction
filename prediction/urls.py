from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html",
                                                redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),   # POST only (Django 5)
    path("dashboard/", views.dashboard, name="dashboard"),
    path("students/", views.students, name="students"),
    path("students/add/", views.add_student, name="add_student"),
    path("students/<int:pk>/delete/", views.delete_student, name="delete_student"),
    path("predict/", views.predict_view, name="predict"),
    path("result/<int:pk>/", views.prediction_result, name="prediction_result"),
    path("history/", views.prediction_history, name="prediction_history"),
    path("analytics/", views.analytics, name="analytics"),
    path("model/", views.model_info, name="model_info"),
]
