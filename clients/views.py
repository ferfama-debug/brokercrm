from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Client


@login_required
def lista_clientes(request):
    clientes = Client.objects.all()
    return render(request, "clients/lista_clientes.html", {"clientes": clientes})
