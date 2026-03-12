from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # LOGIN / LOGOUT DJANGO
    path("accounts/", include("django.contrib.auth.urls")),
    # PANEL PRINCIPAL
    path("", include("panel.urls")),
    # CLIENTES
    path("clientes/", include("clients.urls")),
    # POLIZAS
    path("polizas/", include("policies.urls")),
    # ALERTAS
    path("alertas/", include("alerts.urls")),
]

# SERVIR ARCHIVOS MEDIA (PDF POLIZAS)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
