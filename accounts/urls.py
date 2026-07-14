from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Ruta inteligente conectada a la vista Custom
    path("password-change/", 
         views.CustomPasswordChangeView.as_view(), 
         name="password_change"),
         
    path("password-change/done/", 
         auth_views.PasswordChangeDoneView.as_view(
             template_name="accounts/password_change_done.html"
         ), 
         name="password_change_done"),

    # 👇 NUEVO (temporal)
    path("crear-admin/", views.crear_admin_rapido, name="crear_admin_rapido"),
    path("health/", views.health),  
]