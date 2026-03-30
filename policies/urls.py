from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_polizas, name='lista_polizas'),

    path('cobranzas/', views.panel_cobranzas, name='panel_cobranzas'),

    path('nueva/', views.crear_poliza, name='crear_poliza'),

    path('renovar/<int:poliza_id>/', views.renovar_poliza, name='renovar_poliza'),

    path('pago/<int:pago_id>/', views.marcar_pago, name='marcar_pago'),

    path('enviar/<int:poliza_id>/', views.enviar_poliza, name='enviar_poliza'),

    # 🔥 NUEVA
    path('<int:poliza_id>/', views.detalle_poliza, name='detalle_poliza'),
]