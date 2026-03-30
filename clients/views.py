from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client
from policies.models import Policy


def _get_cliente_seguro(request, cliente_id):
    if request.user.is_superuser:
        return get_object_or_404(Client, id=cliente_id)
    return get_object_or_404(Client, id=cliente_id, producer=request.user)


def _set_flags_seguimiento(cliente, hoy, limite_seguimiento):
    cliente.whatsapp_url = cliente.whatsapp_link
    cliente.seguimiento_vencido = bool(
        cliente.proximo_seguimiento and cliente.proximo_seguimiento < hoy
    )
    cliente.seguimiento_hoy = bool(
        cliente.proximo_seguimiento and cliente.proximo_seguimiento == hoy
    )
    cliente.seguimiento_proxima_semana = bool(
        cliente.proximo_seguimiento
        and hoy <= cliente.proximo_seguimiento <= limite_seguimiento
    )
    return cliente


@login_required
def lista_clientes(request):
    buscar = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "").strip()

    if request.user.is_superuser:
        clientes = Client.objects.all()
    else:
        clientes = Client.objects.filter(producer=request.user)

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
    limite_seguimiento = hoy + timedelta(days=7)

    if estado == "ACTIVOS":
        clientes = clientes.filter(policy__end_date__gt=hoy).distinct()
    elif estado == "VENCIDOS":
        clientes = clientes.filter(policy__end_date__lt=hoy).distinct()
    elif estado == "POR_VENCER":
        clientes = clientes.filter(policy__end_date__range=(hoy, limite)).distinct()
    elif estado == "SEGUIMIENTO_VENCIDO":
        clientes = clientes.filter(proximo_seguimiento__lt=hoy).distinct()
    elif estado == "SEGUIMIENTO_HOY":
        clientes = clientes.filter(proximo_seguimiento=hoy).distinct()
    elif estado == "SEGUIMIENTO_SEMANA":
        clientes = clientes.filter(
            proximo_seguimiento__range=(hoy, limite_seguimiento)
        ).distinct()

    clientes = clientes.order_by("last_name", "first_name")

    for cliente in clientes:
        _set_flags_seguimiento(cliente, hoy, limite_seguimiento)

    return render(
        request,
        "clientes/lista_clientes.html",
        {
            "clientes": clientes,
            "buscar": buscar,
            "estado": estado,
            "hoy": hoy,
            "limite_seguimiento": limite_seguimiento,
        },
    )


@login_required
def ver_cliente(request, cliente_id):
    cliente = _get_cliente_seguro(request, cliente_id)

    hoy = date.today()
    limite_seguimiento = hoy + timedelta(days=7)

    poliza_id = request.GET.get("poliza")
    polizas_query = Policy.objects.filter(client=cliente)

    if poliza_id:
        polizas_query = polizas_query.filter(id=poliza_id)

    polizas = polizas_query.annotate(
        estado_orden=Case(
            When(end_date__gte=hoy, then=1),
            default=2,
            output_field=IntegerField(),
        )
    ).order_by("estado_orden", "-end_date")

    polizas_activas = 0
    polizas_por_vencer = 0
    polizas_vencidas = 0

    for poliza in polizas_query:
        dias = (poliza.end_date - hoy).days

        if dias < 0:
            polizas_vencidas += 1
        elif dias <= 30:
            polizas_por_vencer += 1
        else:
            polizas_activas += 1

    _set_flags_seguimiento(cliente, hoy, limite_seguimiento)

    return render(
        request,
        "clientes/cliente_detalle.html",
        {
            "cliente": cliente,
            "polizas": polizas,
            "polizas_activas": polizas_activas,
            "polizas_por_vencer": polizas_por_vencer,
            "polizas_vencidas": polizas_vencidas,
            "hoy": hoy,
            "limite_seguimiento": limite_seguimiento,
        },
    )


@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClientForm(request.POST)

        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.producer = request.user
            cliente.save()

            messages.success(request, "✅ Cliente creado correctamente")
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
    cliente = _get_cliente_seguro(request, cliente_id)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            messages.success(request, "✅ Cliente actualizado correctamente")
            return redirect("clients:clientes")

    else:
        form = ClientForm(instance=cliente)

    return render(
        request,
        "clientes/editar_cliente.html",
        {
            "form": form,
            "cliente": cliente,
        },
    )


@login_required
def eliminar_cliente(request, id):
    if not request.user.is_superuser:
        messages.error(request, "❌ No tenés permisos para eliminar clientes")
        return redirect("clients:clientes")

    cliente = get_object_or_404(Client, id=id)

    if request.method == "POST":
        cliente.delete()
        messages.success(request, "🗑️ Cliente eliminado correctamente")
        return redirect("clients:clientes")

    return render(
        request,
        "clientes/eliminar_cliente.html",
        {
            "cliente": cliente,
        },
    )


@login_required
def marcar_contactado(request, cliente_id):
    if request.method != "POST":
        return redirect("clients:ver_cliente", cliente_id=cliente_id)

    cliente = _get_cliente_seguro(request, cliente_id)
    cliente.marcar_contactado(dias_hasta_proximo=7)

    messages.success(
        request,
        "✅ Cliente marcado como contactado. Próximo seguimiento programado en 7 días.",
    )

    return redirect("clients:ver_cliente", cliente_id=cliente.id)