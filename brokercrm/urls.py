from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from django.conf import settings
from django.conf.urls.static import static


def health(request):
    return HttpResponse("ok")


urlpatterns = [
    # HEALTH CHECK (RAÍZ)
    path("health/", health),
    # ADMIN DJANGO
    path("admin/", admin.site.urls),
    # LOGIN / LOGOUT / HEALTH / CREAR ADMIN
    path("accounts/", include("accounts.urls")),
    # PANEL PRINCIPAL
    path("", include("dashboard.urls")),
    # CLIENTES
    path("clientes/", include("clients.urls")),
    # POLIZAS
    path("polizas/", include("policies.urls")),
    # ALERTAS
    path("alertas/", include("alerts.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
