from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static


# Función simple para el Health Check de Render
def health(request):
    return HttpResponse("ok")


urlpatterns = [
    # 1. Health Check (Prioridad para que Render sepa que el sitio está vivo)
    path("health/", health),
    # 2. Administración
    path("admin/", admin.site.urls),
    # 3. Autenticación (Login/Logout)
    path("accounts/", include("accounts.urls")),
    # 4. DASHBOARD (LA RAÍZ DEL SITIO)
    # Al estar vacío "", este es el que muestra a Martínez Herrera apenas entras
    path("", include("dashboard.urls")),
    # 5. ELIMINAMOS LA RUTA VACÍA DE PANEL PARA QUE NO HAYA BUCLE
    # Si necesitas algo de panel, lo llamamos con un prefijo
    path("panel-sistema/", include("panel.urls")),
    # 6. Módulos de gestión
    path("clientes/", include("clients.urls")),
    path("polizas/", include("policies.urls")),
    path("alertas/", include("alerts.urls")),
]

# Configuración para archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
