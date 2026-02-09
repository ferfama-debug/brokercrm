from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def home(request):
    return HttpResponse("<h1>CRM Fuerza Natural Brokers funcionando 🚀</h1>")


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),

    # 👇 ESTO CREA EL LOGIN AUTOMÁTICO DE DJANGO
    path("accounts/", include("django.contrib.auth.urls")),
]
