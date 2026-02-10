from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ClientForm

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
