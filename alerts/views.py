from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from policies.models import Payment, Policy
from .models import Alert

from .services import generar_todas_las_alertas


@login_required
def alertas(request):

    generar_todas_las_alertas()

    # 🟢 SOLUCIÓN ESTÁNDAR: Buscamos los IDs de pólizas que SÍ tienen cuotas pagadas
    polizas_pagadas = Payment.objects.filter(
        fecha_pago__isnull=False
    ).values_list("policy_id", flat=True)

    # 🟢 LIMPIEZA AUTOMÁTICA SEGURA: Resolvemos las alertas de esas pólizas sin romper el SQL
    if polizas_pagadas.exists():
        Alert.objects.filter(
            tipo__in=["PAGO_PROXIMO", "DEUDA"],
            resolved=False,
            policy_id__in=polizas_pagadas,
        ).update(resolved=True)

    nivel = request.GET.get("nivel", "")

    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)
    else:
        alertas = Alert.objects.filter(user=request.user, resolved=False)

    if nivel:
        alertas = alertas.filter(level=nivel)

    alertas = alertas.order_by("-created_at")

    hoy = date.today()
    limite_vencimiento = hoy + timedelta(days=30)

    # Filtramos estrictamente por cuotas que NO tengan fecha de pago asentada
    estados_criticos = ["VENCIDO", "HOY", "PROXIMO"]

    # IDs de pólizas que ya tienen una renovación creada para excluirlas
    polizas_renovadas_ids = Policy.objects.filter(
        renovacion_de__isnull=False
    ).values("renovacion_de")

    if request.user.is_superuser:
        polizas_por_vencer = Policy.objects.filter(
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        ).exclude(id__in=polizas_renovadas_ids)
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos, fecha_pago__isnull=True
        ).select_related("policy__client")
    else:
        polizas_por_vencer = Policy.objects.filter(
            client__producer=request.user,
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        ).exclude(id__in=polizas_renovadas_ids)
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos,
            fecha_pago__isnull=True,
            policy__client__producer=request.user,
        ).select_related("policy__client")

    clientes_con_deuda = {
        pago.policy.client
        for pago in pagos_vencidos
        if pago.policy and pago.policy.client
    }

    return render(
        request,
        "alerts/alertas.html",
        {
            "alertas": alertas,
            "nivel": nivel,
            "polizas_por_vencer": polizas_por_vencer,
            "clientes_con_deuda": clientes_con_deuda,
        },
    )
