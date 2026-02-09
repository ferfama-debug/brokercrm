from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def home(request):
    return HttpResponse("CRM Fuerza Natural Brokers funcionando 🚀")


urlpatterns = [
    path('', include('panel.urls')),
    path('admin/', admin.site.urls),

    # RUTAS DE LOGIN / LOGOUT / PASSWORD
    path('accounts/', include('django.contrib.auth.urls')),

    # HOME TEMPORAL
    path('', home),
]
