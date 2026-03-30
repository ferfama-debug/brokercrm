from django.shortcuts import render
from clients.models import Client
from policies.models import Policy, Payment
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


def home(request):

    hoy = date.today()
    en_3_dias = hoy + timedelta(days=3)

    # 🔥 CONTADORES GENERALES (RESPETA PERMISOS)
    if request.user.is_superuser:
        clientes_qs = Client.objects.all()
        policies_qs = Policy.objects.select_related("client").all()
        pagos_qs = Payment.objects.select_related("policy", "policy__client")
    else:
        clientes_qs = Client.objects.filter(producer=request.user)
        policies_qs = Policy.objects.filter(
            client__producer=request.user
        ).select_related("client")
        pagos_qs = Payment.objects.filter(
            policy__client__producer=request.user
        ).select_related("policy", "policy__client")

    clientes = clientes_qs.count()
    polizas = policies_qs.count()
    usuarios = User.objects.count()

    polizas_por_vencer = []
    clientes_llamar = []

    vencidas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies_qs:

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

        telefono = getattr(p.client, "phone", "") or getattr(p.client, "telefono", "")

        if dias <= 7:
            vencen_7 += 1
            prioridad = "URGENTE"
            orden = 1

        elif dias <= 15:
            vencen_15 += 1
            prioridad = "ALTA"
            orden = 2

        elif dias <= 30:
            vencen_30 += 1
            prioridad = "MEDIA"
            orden = 3
        else:
            continue

        mensaje = (
            f"Hola {p.client.nombre_completo()}, te escribo de Fuerza Natural Broker. "
            f"Tu póliza N° {p.policy_number} de {p.company} vence el {p.end_date.strftime('%d/%m/%Y')}."
        )

        clientes_llamar.append(
            {
                "cliente": p.client,
                "cliente_id": p.client.id,
                "numero": p.policy_number,
                "telefono": telefono,
                "dias": dias,
                "mensaje": mensaje,
                "prioridad": prioridad,
                "orden": orden,
            }
        )

    clientes_llamar = sorted(clientes_llamar, key=lambda x: (x["orden"], x["dias"]))

    urgentes = [c for c in clientes_llamar if c["prioridad"] == "URGENTE"]
    if urgentes:
        clientes_llamar = urgentes

    clientes_agrupados = {}

    for c in clientes_llamar:
        cid = c["cliente_id"]

        if cid not in clientes_agrupados:
            clientes_agrupados[cid] = {
                "cliente": c["cliente"],
                "cliente_id": cid,
                "telefono": c["telefono"],
                "mensaje": c["mensaje"],
                "dias": c["dias"],
                "cantidad": 1,
            }
        else:
            clientes_agrupados[cid]["cantidad"] += 1

            if c["dias"] < clientes_agrupados[cid]["dias"]:
                clientes_agrupados[cid]["dias"] = c["dias"]
                clientes_agrupados[cid]["mensaje"] = c["mensaje"]

    clientes_llamar = sorted(clientes_agrupados.values(), key=lambda x: x["dias"])
    clientes_hoy = len(clientes_llamar)

    # 🔥 COBRANZAS
    cobranzas_vencidas = pagos_qs.filter(
        fecha_vencimiento__lt=hoy, fecha_pago__isnull=True
    ).count()

    cobranzas_hoy = pagos_qs.filter(
        fecha_vencimiento=hoy, fecha_pago__isnull=True
    ).count()

    cobranzas_proximos = pagos_qs.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=en_3_dias,
        fecha_pago__isnull=True,
    ).count()

    deuda_total = (
        pagos_qs.filter(estado="VENCIDO").aggregate(total=Sum("monto"))["total"] or 0
    )

    cuotas_vencidas = pagos_qs.filter(estado="VENCIDO").count()

    proximos_pagos = (
        pagos_qs.filter(estado="PENDIENTE", fecha_vencimiento__gte=hoy).aggregate(
            total=Sum("monto")
        )["total"]
        or 0
    )

    cuotas_pendientes = pagos_qs.filter(
        estado="PENDIENTE", fecha_vencimiento__gte=hoy
    ).count()

    cobranzas_urgentes = pagos_qs.filter(
        fecha_vencimiento__lte=hoy, fecha_pago__isnull=True
    )

    # ⭐ SCORE (RESPETA PERMISOS)
    clientes_score_db = clientes_qs.annotate(total_polizas=Count("policy")).order_by(
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

    # 🏢 PRODUCCIÓN
    produccion_companias_db = (
        policies_qs.values("company")
        .annotate(total=Count("id"))
        .order_by("-total", "company")
    )

    produccion_companias = []
    companias = []
    cantidades = []

    for item in produccion_companias_db:
        company = (item.get("company") or "").strip()
        total = item.get("total", 0)

        if not company:
            company = "Sin compañía"

        produccion_companias.append(
            {
                "company": company,
                "total": total,
            }
        )
        companias.append(company)
        cantidades.append(total)

    # 📈 CRECIMIENTO
    crecimiento_db = (
        policies_qs.annotate(mes=TruncMonth("start_date"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    meses = []
    crecimiento_totales = []

    for item in crecimiento_db:
        if item["mes"]:
            meses.append(item["mes"].strftime("%b %Y"))
            crecimiento_totales.append(item["total"])

    context = {
        "clientes": clientes,
        "polizas": polizas,
        "usuarios": usuarios,
        "alertas": len(polizas_por_vencer),
        "clientes_hoy": clientes_hoy,
        "cobranzas_vencidas": cobranzas_vencidas,
        "cobranzas_hoy": cobranzas_hoy,
        "cobranzas_proximos": cobranzas_proximos,
        "cobranzas_urgentes": cobranzas_urgentes,
        "deuda_total": deuda_total,
        "cuotas_vencidas": cuotas_vencidas,
        "proximos_pagos": proximos_pagos,
        "cuotas_pendientes": cuotas_pendientes,
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