from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


# Página de bienvenida (home)
def home(request):
    return HttpResponse("CRM Fuerza Natural Brokers funcionando 🚀")


urlpatterns = [
    path('admin/', admin.site.urls),

    # Login / usuarios
    path('accounts/', include('accounts.urls')),

    # Página principal del sitio
    path('', home),
]
