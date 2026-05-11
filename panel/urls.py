from django.urls import path
from . import views

urlpatterns = [
    # Le cambiamos la ruta vacía por "bienvenida" para que no choque con el Dashboard
    path("bienvenida/", views.home, name="bienvenida"),
]
