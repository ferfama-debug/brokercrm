from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # LOGIN / LOGOUT DJANGO
    path('accounts/', include('django.contrib.auth.urls')),

    # PANEL PRINCIPAL (HOME REAL)
    path('', include('panel.urls')),
    path('clientes/', include('clients.urls')),
]
