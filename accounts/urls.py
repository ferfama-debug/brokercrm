from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # 👇 NUEVO (temporal)
    path("crear-admin/", views.crear_admin_rapido, name="crear_admin_rapido"),
    path("health/", views.health),  # 👈 esta línea nueva
]
