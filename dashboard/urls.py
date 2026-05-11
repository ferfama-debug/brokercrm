from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static


# Función de salud simple fuera de bucles
def health(request):
    return HttpResponse("ok")


urlpatterns = [
    path("health/", health),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    # 🔥 LA SOLUCIÓN:
    # Dejamos el DASHBOARD como la página principal real.
    path("", include("dashboard.urls")),
    # Si el logo grande estaba en 'panel', lo movemos a otra ruta para que no choque
    path("inicio/", include("panel.urls")),
    path("clientes/", include("clients.urls")),
    path("polizas/", include("policies.urls")),
    path("alertas/", include("alerts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
