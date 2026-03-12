from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.db.models import Count
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
    buscar = request.GET.get("buscar")

    if buscar:
        policies = Policy.objects.filter(
            client__first_name__icontains=buscar
        ) | Policy.objects.filter(client__last_name__icontains=buscar)
    else:
        policies = Policy.objects.all()

    polizas_por_vencer = []
    clientes_llamar = []

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
        Policy.objects.values("company").annotate(total=Count("id")).order_by("-total")
    )

    companias = []
    cantidades = []

    for c in produccion_companias:
        companias.append(c["company"])
        cantidades.append(c["total"])

    companias_json = json.dumps(companias)
    cantidades_json = json.dumps(cantidades)

    # CRECIMIENTO POR MES
    crecimiento = (
        Policy.objects.annotate(mes=ExtractMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = []
    totales = []

    for c in crecimiento:
        meses.append(c["mes"])
        totales.append(c["total"])

    meses_json = json.dumps(meses)
    totales_json = json.dumps(totales)

    ranking_companias = (
        Policy.objects.values("company")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    clientes_query = Client.objects.annotate(total_polizas=Count("policy")).order_by(
        "-total_polizas"
    )[:5]

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
        "totales": totales_json,
        "clientes_score": clientes_score,
        "ranking_companias": ranking_companias,
        "oportunidades": [],
        "ventas_cruzadas": [],
        "no_renovaron": [],
        "buscar": buscar,
    }

    return render(request, "panel/dashboard.html", context)
