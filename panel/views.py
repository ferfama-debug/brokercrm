from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
import json

from clients.models import Client
from policies.models import Policy
from django.contrib.auth import get_user_model
from alerts.services import generate_expiration_alerts


User = get_user_model()


@login_required
def home(request):

    generate_expiration_alerts()

    hoy = date.today()
    buscar = request.GET.get("buscar", "")

    policies = Policy.objects.select_related("client")

    if buscar:
        policies = policies.filter(
            Q(client__first_name__icontains=buscar)
            | Q(client__last_name__icontains=buscar)
        )

    polizas_por_vencer = []
    clientes_llamar = []
    pagos_cuponera = []

    vencen_semana = 0
    alertas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies:

        dias = (p.end_date - hoy).days

        if dias >= 0:

            mensaje = (
                f"Hola {p.client.first_name}, te escribo de Fuerza Natural Brokers. "
                f"Tu póliza {p.policy_number} de {p.company} vence el {p.end_date}. "
                f"Si querés podemos renovarla o revisar mejores opciones."
            )

            polizas_por_vencer.append(
                {
                    "cliente": p.client,
                    "numero": p.policy_number,
                    "compania": p.company,
                    "vencimiento": p.end_date,
                    "dias": dias,
                    "telefono": getattr(p.client, "phone", ""),
                    "mensaje": mensaje,
                }
            )

            if dias <= 30:
                alertas += 1
                vencen_30 += 1

            if dias <= 15:
                vencen_15 += 1

            if dias <= 7:
                vencen_7 += 1
                vencen_semana += 1

                clientes_llamar.append(
                    {
                        "cliente": p.client,
                        "telefono": getattr(p.client, "phone", ""),
                        "numero": p.policy_number,
                        "dias": dias,
                        "mensaje": mensaje,
                    }
                )

        # =========================
        # PAGOS DE CUPONERA
        # =========================

        if (
            p.forma_pago == "CUPONERA"
            and p.frecuencia_cuponera
            and p.cuponera_pdf
        ):

            proximo_pago = p.proximo_pago_cuponera

            if proximo_pago:

                dias_pago = (proximo_pago - hoy).days

                if 0 <= dias_pago <= 5:

                    mensaje_pago = (
                        f"Hola {p.client.first_name}. "
                        f"Te recordamos el pago de la cuponera de tu póliza "
                        f"{p.policy_number} de {p.company}. "
                        f"Vence el {proximo_pago}."
                    )

                    pagos_cuponera.append(
                        {
                            "cliente": p.client,
                            "numero": p.policy_number,
                            "company": p.company,
                            "fecha": proximo_pago,
                            "telefono": getattr(p.client, "phone", ""),
                            "mensaje": mensaje_pago,
                            "pdf": p.cuponera_pdf.url,
                        }
                    )

    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

    produccion_mes = Policy.objects.filter(
        start_date__month=mes_actual,
        start_date__year=anio_actual,
    ).count()

    renovaciones_mes = Policy.objects.filter(
        end_date__month=mes_actual,
        end_date__year=anio_actual,
    ).count()

    produccion_companias = (
        Policy.objects.values("company")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    companias = [c["company"] for c in produccion_companias]
    cantidades = [c["total"] for c in produccion_companias]

    companias_json = json.dumps(companias)
    cantidades_json = json.dumps(cantidades)

    crecimiento = (
        Policy.objects.annotate(mes=ExtractMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = [c["mes"] for c in crecimiento]
    totales = [c["total"] for c in crecimiento]

    meses_json = json.dumps(meses)
    totales_json = json.dumps(totales)

    ranking_companias = (
        Policy.objects.values("company")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    clientes_query = (
        Client.objects.annotate(total_polizas=Count("policy"))
        .order_by("-total_polizas")[:5]
    )

    clientes_score = []

    for c in clientes_query:

        if c.total_polizas >= 4:
            score = "⭐⭐⭐"
        elif c.total_polizas >= 2:
            score = "⭐⭐"
        else:
            score = "⭐"

        clientes_score.append(
            {
                "cliente": f"{c.first_name} {c.last_name}",
                "polizas": c.total_polizas,
                "score": score,
            }
        )

    context = {
        "clientes": Client.objects.count(),
        "polizas": Policy.objects.count(),
        "alertas": alertas,
        "usuarios": User.objects.count(),
        "polizas_por_vencer": polizas_por_vencer,
        "clientes_llamar": clientes_llamar,
        "pagos_cuponera": pagos_cuponera,
        "vencen_semana": vencen_semana,
        "vencen_7": vencen_7,
        "vencen_15": vencen_15,
        "vencen_30": vencen_30,
        "produccion_mes": produccion_mes,
        "renovaciones_mes": renovaciones_mes,
        "produccion_companias": produccion_companias,
        "companias": companias_json,
        "cantidades": cantidades_json,
        "meses": meses_json,
        "crecimiento_totales": totales_json,
        "clientes_score": clientes_score,
        "ranking_companias": ranking_companias,
        "oportunidades": [],
        "ventas_cruzadas": [],
        "no_renovaron": [],
        "buscar": buscar,
    }

    return render(request, "panel/dashboard.html", context)
