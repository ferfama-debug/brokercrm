from django.urls import path

from . import views

app_name = "login_tracking"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
