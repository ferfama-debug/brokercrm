from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Alert

from policies.models import Policy, Payment
from datetime import date, timedelta

from .services import generar_todas_las_alertas


@login_required
def alertas(request):

    generar_todas_las_alertas()

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

    # 🟢 CIRUGÍA QUIRÚRGICA: Ampliamos el filtro de estados para incluir cuotas de HOY y PROXIMO
    estados_criticos = ["VENCIDO", "HOY", "PROXIMO"]

    if request.user.is_superuser:
        polizas_por_vencer = Policy.objects.filter(
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        )
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos
        ).select_related("policy__client")
    else:
        polizas_por_vencer = Policy.objects.filter(
            client__producer=request.user,
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        )
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos,
            policy__client__producer=request.user,
        ).select_related("policy__client")

    clientes_con_deuda = {
        pago.policy.client
        for pago in pagos_vencidos
        if pago.policy and pago.policy.client
    }

    return render(
        request,
        request.user.is_superuser
        and "alerts/alertas.html"
        or "alerts/alertas.html",  # Mantenemos compatibilidad de render
        {
            "alertas": alertas,
            "nivel": nivel,
            "polizas_por_vencer": polizas_por_vencer,
            "clientes_con_deuda": clientes_con_deuda,
        },
    )
