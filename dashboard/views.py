from django.shortcuts import render
from clients.models import Client
from policies.models import Policy, Payment
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


def home(request):

    clientes = Client.objects.count()
    polizas = Policy.objects.count()
    usuarios = User.objects.count()

    hoy = date.today()

    policies_db = Policy.objects.all()

    polizas_por_vencer = []
    clientes_llamar = []

    # 🔴 RADAR
    vencidas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies_db:

        dias = (p.end_date - hoy).days

        if dias < 0:
            vencidas += 1
            continue

        polizas_por_vencer.append(
            {
                "cliente": p.client,
                "numero": p.policy_number,
                "compania": p.company,
                "vencimiento": p.end_date,
                "dias": dias,
            }
        )

        if dias <= 7:
            vencen_7 += 1

            fecha = p.end_date.strftime("%d/%m/%Y")

            mensaje = (
                f"Hola {p.client.full_name}, "
                f"tu póliza N° {p.policy_number} de {p.company} "
                f"vence el {fecha}. "
                f"¿Querés que avancemos con la renovación?"
            )

            clientes_llamar.append(
                {
                    "cliente": p.client,
                    "numero": p.policy_number,
                    "telefono": getattr(p.client, "phone", ""),
                    "dias": dias,
                    "mensaje": mensaje,
                }
            )

        elif dias <= 15:
            vencen_15 += 1

        elif dias <= 30:
            vencen_30 += 1

    # 🔥 💰 DEUDA Y COBRANZA (NUEVO PRO)

    pagos = Payment.objects.all()

    deuda_total = pagos.filter(
        estado="VENCIDO"
    ).aggregate(total=Sum("monto"))["total"] or 0

    cuotas_vencidas = pagos.filter(estado="VENCIDO").count()

    proximos_pagos = pagos.filter(
        estado="PENDIENTE",
        fecha_vencimiento__gte=hoy
    ).aggregate(total=Sum("monto"))["total"] or 0

    cuotas_pendientes = pagos.filter(
        estado="PENDIENTE",
        fecha_vencimiento__gte=hoy
    ).count()

    # ⭐ SCORE CLIENTES

    clientes_score_db = Client.objects.annotate(total_polizas=Count("policy")).order_by(
        "-total_polizas"
    )

    clientes_score = []

    for c in clientes_score_db:

        if c.total_polizas >= 4:
            score = "⭐⭐⭐ Cliente Premium"
        elif c.total_polizas >= 2:
            score = "⭐⭐ Buen Cliente"
        else:
            score = "⭐ Cliente Básico"

        clientes_score.append(
            {
                "cliente": c,
                "polizas": c.total_polizas,
                "score": score,
            }
        )

    # 🏢 PRODUCCIÓN POR COMPAÑÍA

    produccion_companias = (
        Policy.objects.values("company").annotate(total=Count("id")).order_by("-total")
    )

    companias = []
    cantidades = []

    for c in produccion_companias:
        companias.append(c["company"])
        cantidades.append(c["total"])

    # 📈 CRECIMIENTO

    crecimiento = (
        Policy.objects.annotate(mes=TruncMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = []
    crecimiento_totales = []

    for c in crecimiento:
        meses.append(c["mes"].strftime("%b %Y"))
        crecimiento_totales.append(c["total"])

    context = {
        "clientes": clientes,
        "polizas": polizas,
        "usuarios": usuarios,
        "alertas": len(polizas_por_vencer),

        # 🔥 💰 NUEVO
        "deuda_total": deuda_total,
        "cuotas_vencidas": cuotas_vencidas,
        "proximos_pagos": proximos_pagos,
        "cuotas_pendientes": cuotas_pendientes,

        # RADAR
        "vencidas": vencidas,
        "vencen_7": vencen_7,
        "vencen_15": vencen_15,
        "vencen_30": vencen_30,

        "polizas_por_vencer": polizas_por_vencer,
        "clientes_score": clientes_score,
        "clientes_llamar": clientes_llamar,
        "produccion_companias": produccion_companias,
        "companias": companias,
        "cantidades": cantidades,
        "meses": meses,
        "crecimiento_totales": crecimiento_totales,
    }

    return render(request, "panel/dashboard.html", context)