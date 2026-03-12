from django.urls import path
from . import views

urlpatterns = [
path('', views.lista_polizas, name='lista_polizas'),
path('nueva/', views.crear_poliza, name='crear_poliza'),
]
