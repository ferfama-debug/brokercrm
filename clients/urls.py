from django.urls import path
from .views import lista_clientes, crear_cliente, editar_cliente

urlpatterns = [
    path("", lista_clientes, name="lista_clientes"),
    path("nuevo/", crear_cliente, name="crear_cliente"),
    path("editar/<int:cliente_id>/", editar_cliente, name="editar_cliente"),
]

