from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.lista_clientes, name="clientes"),
    path("nuevo/", views.crear_cliente, name="crear_cliente"),
    path("ver/<int:cliente_id>/", views.ver_cliente, name="ver_cliente"),
    path("editar/<int:cliente_id>/", views.editar_cliente, name="editar_cliente"),
    path("eliminar/<int:id>/", views.eliminar_cliente, name="eliminar_cliente"),
]