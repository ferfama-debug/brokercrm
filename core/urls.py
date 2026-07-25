from django.contrib import admin
from django.urls import path, include  # 👈 1. Importamos 'include'
from .views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home),
    
    # 🟢 2. Agregamos esta línea para conectar la app de pólizas
    path("polizas/", include("policies.urls")),
]
