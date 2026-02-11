from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Client
from .forms import ClientForm


@login_required
def lista_clientes(request):
    clientes = Client.objects.all()
    return render(request, "clientes/lista_clientes.html", {"clientes": clientes})


@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_clientes")
    else:
        form = ClientForm()

    return render(request, "clientes/crear_cliente.html", {"form": form})
from django.shortcuts import get_object_or_404


@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Client, id=cliente_id)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("lista_clientes")
    else:
        form = ClientForm(instance=cliente)

    return render(request, "clientes/editar_cliente.html", {"form": form})
from django.shortcuts import get_object_or_404

@login_required
def eliminar_cliente(request, id):
    cliente = get_object_or_404(Client, id=id)

    if request.method == "POST":
        cliente.delete()
        return redirect("lista_clientes")

    return render(request, "clients/eliminar_cliente.html", {"cliente": cliente})

