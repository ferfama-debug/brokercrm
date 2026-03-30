from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
import json

from clients.models import Client
from policies.models import Policy, Payment
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

    # 🔥 NUEVO: COBRANZA INTELIGENTE
    cobranzas_urgentes = []
    cobranzas_proximas = []

    vencen_semana = 0
    alertas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies:

        dias = (p.end_date - hoy).days

        if dias >= 0:

            mensaje = (
                f"Hola {p.client.first_name}, te escribo de Fuerza Natural Broker. "
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
                        "cliente_id": p.client.id,
                        "telefono": getattr(p.client, "phone", ""),
                        "numero": p.policy_number,
                        "dias": dias,
                        "mensaje": mensaje,
                    }
                )

        # =========================
        # 🔥 COBRANZA REAL (NUEVO)
        # =========================

        for pago in p.pagos.all():

            telefono = getattr(p.client, "phone", "")
            dias_pago = (pago.fecha_vencimiento - hoy).days

            # 🔴 VENCIDOS
            if pago.estado == "VENCIDO":

                mensaje = (
                    f"Hola {p.client.first_name}, te escribo de Fuerza Natural Broker. "
                    f"Tenés una cuota vencida de la póliza {p.policy_number} ({p.company}). "
                    f"¿Podés enviarnos el comprobante así la registramos?"
                )

                cobranzas_urgentes.append(
                    {
                        "cliente": p.client,
                        "numero": p.policy_number,
                        "telefono": telefono,
                        "mensaje": mensaje,
                        "dias": dias_pago,
                    }
                )

            # 🟠 POR VENCER (5 días)
            elif pago.estado == "PENDIENTE" and 0 <= dias_pago <= 5:

                mensaje = (
                    f"Hola {p.client.first_name}, te recordamos una cuota próxima a vencer "
                    f"de tu póliza {p.policy_number} ({p.company}). "
                    f"Vence el {pago.fecha_vencimiento}."
                )

                cobranzas_proximas.append(
                    {
                        "cliente": p.client,
                        "numero": p.policy_number,
                        "telefono": telefono,
                        "mensaje": mensaje,
                        "dias": dias_pago,
                    }
                )

        # =========================
        # PAGOS DE CUPONERA
        # =========================

        if p.forma_pago == "CUPONERA" and p.frecuencia_cuponera and p.cuponera_pdf:

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
                            "pdf": p.cuponera_pdf,
                        }
                    )

    # 🔥 AGRUPAR CRM DE VENTAS (1 FILA POR CLIENTE)
    clientes_llamar_agrupados = {}

    for c in clientes_llamar:
        cid = c["cliente_id"]

        if cid not in clientes_llamar_agrupados:
            clientes_llamar_agrupados[cid] = {
                "cliente": c["cliente"],
                "cliente_id": c["cliente_id"],
                "telefono": c["telefono"],
                "dias": c["dias"],
                "mensaje": c["mensaje"],
                "cantidad": 1,
            }
        else:
            clientes_llamar_agrupados[cid]["cantidad"] += 1

            if c["dias"] < clientes_llamar_agrupados[cid]["dias"]:
                clientes_llamar_agrupados[cid]["dias"] = c["dias"]
                clientes_llamar_agrupados[cid]["mensaje"] = c["mensaje"]

    clientes_llamar = sorted(
        clientes_llamar_agrupados.values(), key=lambda x: x["dias"]
    )

    # =========================
    # RESTO (NO SE TOCA)
    # =========================

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

    companias = [c["company"] for c in produccion_companias]
    cantidades = [c["total"] for c in produccion_companias]

    crecimiento = (
        Policy.objects.annotate(mes=ExtractMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = [c["mes"] for c in crecimiento]
    totales = [c["total"] for c in crecimiento]

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
        "pagos_cuponera": pagos_cuponera,
        # 🔥 NUEVO
        "cobranzas_urgentes": cobranzas_urgentes,
        "cobranzas_proximas": cobranzas_proximas,
        "vencen_semana": vencen_semana,
        "vencen_7": vencen_7,
        "vencen_15": vencen_15,
        "vencen_30": vencen_30,
        "produccion_mes": produccion_mes,
        "renovaciones_mes": renovaciones_mes,
        "produccion_companias": produccion_companias,
        "companias": json.dumps(companias),
        "cantidades": json.dumps(cantidades),
        "meses": json.dumps(meses),
        "crecimiento_totales": json.dumps(totales),
        "clientes_score": clientes_score,
        "buscar": buscar,
    }

    return render(request, "panel/dashboard.html", context)
