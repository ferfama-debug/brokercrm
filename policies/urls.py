from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_polizas, name='lista_polizas'),
    path('nueva/', views.crear_poliza, name='crear_poliza'),

    # 🔥 RENOVAR POLIZA
    path('renovar/<int:poliza_id>/', views.renovar_poliza, name='renovar_poliza'),

    # 🔥 MARCAR PAGO
    path('pago/<int:pago_id>/', views.marcar_pago, name='marcar_pago'),

    # 🔥 ENVIAR EMAIL
    path('enviar/<int:poliza_id>/', views.enviar_poliza, name='enviar_poliza'),
]