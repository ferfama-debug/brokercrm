from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Client
from .forms import ClienteForm


# 🔹 LISTA DE CLIENTES (ESTA FALTABA)
@login_required
def lista_clientes(request):
    clientes = Client.objects.all()
    return render(request, "clientes/lista_clientes.html", {
        "clientes": clientes
    })


# 🔹 CREAR CLIENTE
@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_clientes")
    else:
        form = ClienteForm()

    return render(request, "clientes/crear_cliente.html", {"form": form})
