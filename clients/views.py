from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, IntegerField
from datetime import date, timedelta

from .models import Client
from .forms import ClientForm
from policies.models import Policy


@login_required
def lista_clientes(request):

    buscar = request.GET.get("buscar", "")
    estado = request.GET.get("estado", "")

    # 🔴 MULTIUSUARIO
    if request.user.is_superuser:
        clientes = Client.objects.all()
    else:
        clientes = Client.objects.filter(producer=request.user)

    # 🔍 BUSCADOR
    if buscar:
        clientes = clientes.filter(
            Q(first_name__icontains=buscar)
            | Q(last_name__icontains=buscar)
            | Q(dni__icontains=buscar)
            | Q(phone__icontains=buscar)
            | Q(email__icontains=buscar)
        )

    hoy = date.today()
    limite = hoy + timedelta(days=30)

    # 🔥 FILTROS POR ESTADO
    if estado == "ACTIVOS":
        clientes = clientes.filter(policy__end_date__gt=hoy).distinct()

    elif estado == "VENCIDOS":
        clientes = clientes.filter(policy__end_date__lt=hoy).distinct()

    elif estado == "POR_VENCER":
        clientes = clientes.filter(
            policy__end_date__range=(hoy, limite)
        ).distinct()

    clientes = clientes.order_by("last_name", "first_name")

    return render(
        request,
        "clientes/lista_clientes.html",
        {
            "clientes": clientes,
            "buscar": buscar,
            "estado": estado,
        },
    )


@login_required
def ver_cliente(request, cliente_id):

    # 🔴 SEGURIDAD MULTIUSUARIO
    if request.user.is_superuser:
        cliente = get_object_or_404(Client, id=cliente_id)
    else:
        cliente = get_object_or_404(Client, id=cliente_id, producer=request.user)

    hoy = date.today()

    poliza_id = request.GET.get("poliza")

    polizas_query = Policy.objects.filter(client=cliente)

    if poliza_id:
        polizas_query = polizas_query.filter(id=poliza_id)

    polizas = (
        polizas_query.annotate(
            estado_orden=Case(
                When(end_date__gte=hoy, then=1),
                default=2,
                output_field=IntegerField(),
            )
        ).order_by("estado_orden", "-end_date")
    )

    polizas_activas = 0
    polizas_por_vencer = 0
    polizas_vencidas = 0

    for p in polizas_query:

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
            cliente = form.save(commit=False)

            # 🔴 ASIGNAR PRODUCTOR AUTOMÁTICO
            cliente.producer = request.user

            cliente.save()
            return redirect("clients:clientes")

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

    if request.user.is_superuser:
        cliente = get_object_or_404(Client, id=cliente_id)
    else:
        cliente = get_object_or_404(Client, id=cliente_id, producer=request.user)

    if request.method == "POST":

        form = ClientForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            return redirect("clients:clientes")

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

    # 🔴 SOLO ADMIN PUEDE ELIMINAR
    if not request.user.is_superuser:
        return redirect("clients:clientes")

    cliente = get_object_or_404(Client, id=id)

    if request.method == "POST":
        cliente.delete()
        return redirect("clients:clientes")

    return render(
        request,
        "clientes/eliminar_cliente.html",
        {
            "cliente": cliente,
        },
    )