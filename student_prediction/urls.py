from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("prediction.urls")),
]

handler404 = "prediction.views.error_404"
handler500 = "prediction.views.error_500"
