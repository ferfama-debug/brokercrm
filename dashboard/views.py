from django.shortcuts import render
from clients.models import Client
from policies.models import Policy, Payment
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


def home(request):

    hoy = date.today()

    # 🔥 CONTADORES GENERALES
    clientes = Client.objects.count()
    polizas = Policy.objects.count()
    usuarios = User.objects.count()

    policies_db = Policy.objects.select_related("client").all()

    polizas_por_vencer = []
    clientes_llamar = []

    vencidas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies_db:

        dias = (p.end_date - hoy).days

        if dias < 0:
            vencidas += 1
            continue

        polizas_por_vencer.append({
            "cliente": p.client,
            "numero": p.policy_number,
            "compania": p.company,
            "vencimiento": p.end_date,
            "dias": dias,
        })

        telefono = getattr(p.client, "phone", "")

        # 🔴 URGENTE
        if dias <= 7:
            vencen_7 += 1

            mensaje = (
                f"Hola {p.client.nombre_completo()}, te escribo de Fuerza Natural Broker. "
                f"Tu póliza N° {p.policy_number} de {p.company} vence el {p.end_date.strftime('%d/%m/%Y')}. "
                f"Podemos renovarla hoy mismo para que no pierdas cobertura. ¿Avanzamos?"
            )

            clientes_llamar.append({
                "cliente": p.client,
                "numero": p.policy_number,
                "telefono": telefono,
                "dias": dias,
                "mensaje": mensaje,
                "prioridad": "URGENTE",
                "orden": 1
            })

        # 🟠 ALTA
        elif dias <= 15:
            vencen_15 += 1

            mensaje = (
                f"Hola {p.client.nombre_completo()}, ¿cómo estás? "
                f"Tu póliza N° {p.policy_number} de {p.company} vence el {p.end_date.strftime('%d/%m/%Y')}. "
                f"Podemos ir avanzando con la renovación."
            )

            clientes_llamar.append({
                "cliente": p.client,
                "numero": p.policy_number,
                "telefono": telefono,
                "dias": dias,
                "mensaje": mensaje,
                "prioridad": "ALTA",
                "orden": 2
            })

        # 🟡 MEDIA
        elif dias <= 30:
            vencen_30 += 1

            mensaje = (
                f"Hola {p.client.nombre_completo()}, te contacto de Fuerza Natural Broker. "
                f"Tu póliza N° {p.policy_number} de {p.company} vence el {p.end_date.strftime('%d/%m/%Y')}. "
                f"Cuando quieras vemos la renovación."
            )

            clientes_llamar.append({
                "cliente": p.client,
                "numero": p.policy_number,
                "telefono": telefono,
                "dias": dias,
                "mensaje": mensaje,
                "prioridad": "MEDIA",
                "orden": 3
            })

    # 🔥 ORDEN AUTOMÁTICO (CLAVE NIVEL 3)
    clientes_llamar = sorted(clientes_llamar, key=lambda x: (x["orden"], x["dias"]))

    # 🔥 FILTRO INTELIGENTE (SOLO URGENTES SI EXISTEN)
    urgentes = [c for c in clientes_llamar if c["prioridad"] == "URGENTE"]

    if urgentes:
        clientes_llamar = urgentes

    # 🔥 CONTADOR DEL DÍA
    clientes_hoy = len(clientes_llamar)

    # 💰 COBRANZA
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

    # ⭐ SCORE
    clientes_score_db = Client.objects.annotate(
        total_polizas=Count("policy")
    ).order_by("-total_polizas")

    clientes_score = []

    for c in clientes_score_db:

        if c.total_polizas >= 4:
            score = "⭐⭐⭐ Cliente Premium"
        elif c.total_polizas >= 2:
            score = "⭐⭐ Buen Cliente"
        else:
            score = "⭐ Cliente Básico"

        clientes_score.append({
            "cliente": c,
            "polizas": c.total_polizas,
            "score": score,
        })

    # 🏢 PRODUCCIÓN
    produccion_companias = (
        Policy.objects.values("company")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    companias = [c["company"] for c in produccion_companias]
    cantidades = [c["total"] for c in produccion_companias]

    # 📈 CRECIMIENTO
    crecimiento = (
        Policy.objects.annotate(mes=TruncMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = [c["mes"].strftime("%b %Y") for c in crecimiento]
    crecimiento_totales = [c["total"] for c in crecimiento]

    context = {
        "clientes": clientes,
        "polizas": polizas,
        "usuarios": usuarios,
        "alertas": len(polizas_por_vencer),

        "clientes_hoy": clientes_hoy,  # 🔥 NUEVO

        # 💰
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

        "companias": companias,
        "cantidades": cantidades,
        "meses": meses,
        "crecimiento_totales": crecimiento_totales,
        "produccion_companias": produccion_companias,
    }

    return render(request, "panel/dashboard.html", context)