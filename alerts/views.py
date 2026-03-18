from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Alert

from policies.models import Policy, Payment
from datetime import date

# 🔥 IMPORTANTE: motor automático
from .services import generar_todas_las_alertas


@login_required
def alertas(request):

    # 🔥 GENERAR ALERTAS AUTOMÁTICAMENTE
    generar_todas_las_alertas()

    nivel = request.GET.get("nivel", "")

    # 🔹 ALERTAS MANUALES + AUTOMÁTICAS (DB)
    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)
    else:
        alertas = Alert.objects.filter(
            user=request.user,
            resolved=False
        )

    if nivel:
        alertas = alertas.filter(level=nivel)

    alertas = alertas.order_by("-created_at")

    # 🔥 CONTEXTO VISUAL (NO ROMPE TU TEMPLATE)

    hoy = date.today()

    # 🟠 PÓLIZAS POR VENCER (30 días)
    polizas_por_vencer = Policy.objects.filter(
        end_date__gte=hoy,
        end_date__lte=hoy.replace(day=hoy.day)
    )

    # 🔴 CLIENTES CON DEUDA
    pagos_vencidos = Payment.objects.filter(
        estado="VENCIDO"
    ).select_related("policy__client")

    clientes_con_deuda = set(
        pago.policy.client for pago in pagos_vencidos
    )

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