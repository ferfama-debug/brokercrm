from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, IntegerField
from datetime import date

from .models import Client
from .forms import ClientForm
from policies.models import Policy


@login_required
def lista_clientes(request):

    buscar = request.GET.get("buscar")

    if buscar:
        clientes = Client.objects.filter(
            Q(first_name__icontains=buscar)
            | Q(last_name__icontains=buscar)
            | Q(dni__icontains=buscar)
            | Q(phone__icontains=buscar)
            | Q(email__icontains=buscar)
        )
    else:
        clientes = Client.objects.all()

    return render(
        request,
        "clientes/lista_clientes.html",
        {
            "clientes": clientes,
            "buscar": buscar,
        },
    )


@login_required
def ver_cliente(request, cliente_id):

    cliente = get_object_or_404(Client, id=cliente_id)

    hoy = date.today()

    # POLIZA QUE VIENE DESDE ALERTA
    poliza_id = request.GET.get("poliza")

    if poliza_id:
        polizas = (
            Policy.objects.filter(id=poliza_id, client=cliente)
            .annotate(
                estado_orden=Case(
                    When(end_date__gte=hoy, then=1),
                    default=2,
                    output_field=IntegerField(),
                )
            )
            .order_by("estado_orden", "-end_date")
        )
    else:
        polizas = (
            Policy.objects.filter(client=cliente)
            .annotate(
                estado_orden=Case(
                    When(end_date__gte=hoy, then=1),
                    default=2,
                    output_field=IntegerField(),
                )
            )
            .order_by("estado_orden", "-end_date")
        )

    # RESUMEN DEL CLIENTE
    polizas_activas = 0
    polizas_por_vencer = 0
    polizas_vencidas = 0

    for p in Policy.objects.filter(client=cliente):

        dias = (p.end_date - hoy).days

        if dias < 0:
            polizas_vencidas += 1

        elif dias <= 30:
            polizas_por_vencer += 1

        else:
            polizas_activas += 1

    return render(
        request,
        "clientes/cliente_detalle.html",
        {
            "cliente": cliente,
            "polizas": polizas,
            "polizas_activas": polizas_activas,
            "polizas_por_vencer": polizas_por_vencer,
            "polizas_vencidas": polizas_vencidas,
        },
    )


@login_required
def crear_cliente(request):

    if request.method == "POST":

        form = ClientForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("clientes")

    else:

        form = ClientForm()

    return render(
        request,
        "clientes/crear_cliente.html",
        {
            "form": form,
        },
    )


@login_required
def editar_cliente(request, cliente_id):

    cliente = get_object_or_404(Client, id=cliente_id)

    if request.method == "POST":

        form = ClientForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            return redirect("clientes")

    else:

        form = ClientForm(instance=cliente)

    return render(
        request,
        "clientes/editar_cliente.html",
        {
            "form": form,
        },
    )


@login_required
def eliminar_cliente(request, id):

    cliente = get_object_or_404(Client, id=id)

    if request.method == "POST":
        cliente.delete()
        return redirect("clientes")

    return render(
        request,
        "clientes/eliminar_cliente.html",
        {
            "cliente": cliente,
        },
    )
