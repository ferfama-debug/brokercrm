from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clients.models import Client
from policies.models import Policy, Payment
from accounts.models import User
from datetime import date, timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


@login_required
def home(request):

    hoy = date.today()
    en_3_dias = hoy + timedelta(days=3)

    # 🔥 CONTADORES GENERALES - VISIBILIDAD TOTAL SIN FILTROS
    if request.user.is_superuser:
        clientes_qs = Client.objects.all()
        policies_qs = Policy.objects.select_related("client").all()
        pagos_qs = Payment.objects.select_related("policy", "policy__client")
        usuarios = User.objects.count()
    else:
        clientes_qs = Client.objects.all()
        policies_qs = Policy.objects.all().select_related("client")
        pagos_qs = Payment.objects.all().select_related("policy", "policy__client")
        usuarios = 1

    # CIRUGÍA QUIRÚRGICA: Conteo de pólizas activas vs anuladas
    # Las activas son las que NO están anuladas
    polizas_activas_count = policies_qs.filter(anulada=False).count()
    polizas_anuladas_count = policies_qs.filter(anulada=True).count()

    clientes = clientes_qs.count()
    polizas = polizas_activas_count  # Usamos las activas para el contador principal

    # Sincronización con base.html
    ultimas_alertas = []
    clientes_llamar_lista = []

    vencidas = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    # Filtramos para que el CRM de renovaciones no muestre pólizas que ya fueron anuladas
    policies_para_alertas = policies_qs.filter(anulada=False)

    for p in policies_para_alertas:
        dias = (p.end_date - hoy).days

        if dias < 0:
            vencidas += 1
            continue

        if dias <= 30:
            lvl = "info"
            if dias <= 7:
                lvl = "danger"
            elif dias <= 15:
                lvl = "warning"

            p_message = (
                p.client.nombre_completo() if p.client else "Cliente desconocido"
            )
            ultimas_alertas.append(
                {
                    "message": f"{p_message} - Vence en {dias} días",
                    "level": lvl,
                }
            )

            telefono = ""
            if p.client:
                telefono = getattr(p.client, "phone", "") or getattr(
                    p.client, "telefono", ""
                )

            if dias <= 7:
                vencen_7 += 1
                prioridad = "URGENTE"
                orden = 1
            elif dias <= 15:
                vencen_15 += 1
                prioridad = "ALTA"
                orden = 2
            else:
                vencen_30 += 1
                prioridad = "MEDIA"
                orden = 3

            nombre_completo_texto = (
                p.client.nombre_completo() if p.client else "Cliente"
            )
            mensaje = (
                f"Hola {nombre_completo_texto}, te escribo de Fuerza Natural Broker. "
                f"Tu póliza N° {p.policy_number} de {p.company} vence el {p.end_date.strftime('%d/%m/%Y')}."
            )

            clientes_llamar_lista.append(
                {
                    "cliente": p.client,
                    "cliente_id": p.client.id if p.client else None,
                    "numero": p.policy_number,
                    "compania_texto": str(p.company),
                    "telefono": telefono,
                    "dias": dias,
                    "mensaje": mensaje,
                    "prioridad": prioridad,
                    "orden": orden,
                }
            )

    # Agrupamos por cliente para la tabla
    clientes_agrupados = {}
    for c in clientes_llamar_lista:
        cid = c["cliente_id"]
        if not cid:
            continue
        if cid not in clientes_agrupados:
            clientes_agrupados[cid] = {
                "cliente": c["cliente"],
                "cliente_id": cid,
                "telefono": c["telefono"],
                "mensaje": c["mensaje"],
                "dias": c["dias"],
                "prioridad": c["prioridad"],
                "cantidad": 1,
                "compania": c["compania_texto"],
                "n_poliza": c["numero"],
            }
        else:
            clientes_agrupados[cid]["cantidad"] += 1
            if c["dias"] < clientes_agrupados[cid]["dias"]:
                clientes_agrupados[cid]["dias"] = c["dias"]
                clientes_agrupados[cid]["mensaje"] = c["mensaje"]
                clientes_agrupados[cid]["prioridad"] = c["prioridad"]
                clientes_agrupados[cid]["compania"] = c["compania_texto"]
                clientes_agrupados[cid]["n_poliza"] = c["numero"]

    clientes_llamar = sorted(clientes_agrupados.values(), key=lambda x: x["dias"])
    clientes_hoy = len(clientes_llamar)

    # 🔥 COBRANZAS (Intacto)
    cobranzas_vencidas = pagos_qs.filter(
        fecha_vencimiento__lt=hoy, fecha_pago__isnull=True
    ).count()
    cobranzas_hoy = pagos_qs.filter(
        fecha_vencimiento=hoy, fecha_pago__isnull=True
    ).count()
    cobranzas_proximos = pagos_qs.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=3),
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

    # ⭐ SCORE (Intacto)
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
            {"cliente": c, "polizas": c.total_polizas, "score": score}
        )

    # 🏢 PRODUCCIÓN (Intacto)
    produccion_companias_db = (
        policies_qs.values("company")
        .annotate(total=Count("id"))
        .order_by("-total", "company")
    )
    produccion_companias = []
    companias = []
    cantidades = []

    for item in produccion_companias_db:
        company = (item.get("company") or "Sin compañía").strip()
        total = item.get("total", 0)
        produccion_companias.append({"company": company, "total": total})
        companias.append(company)
        cantidades.append(total)

    # 📈 CRECIMIENTO (Intacto)
    crecimiento_db = (
        policies_qs.annotate(mes_p=TruncMonth("start_date"))
        .values("mes_p")
        .annotate(total=Count("id"))
        .order_by("mes_p")
    )
    meses = []
    crecimiento_totales = []
    for item in crecimiento_db:
        if item["mes_p"]:
            meses.append(item["mes_p"].strftime("%b %Y"))
            crecimiento_totales.append(item["total"])

    alert_color = "media"
    if vencen_7 > 0:
        alert_color = "critica"
    elif vencen_15 > 0:
        alert_color = "alta"

    context = {
        "clientes": clientes,
        "polizas": polizas,
        "polizas_anuladas_count": polizas_anuladas_count,
        "usuarios": usuarios,
        "alert_count": len(ultimas_alertas),
        "ultimas_alertas": ultimas_alertas,
        "alert_color": alert_color,
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
        "clientes_score": clientes_score,
        "clientes_llamar": clientes_llamar,
        "companias": companias,
        "cantidades": cantidades,
        "meses": meses,
        "crecimiento_totales": crecimiento_totales,
        "produccion_companias": produccion_companias,
    }

    return render(request, "dashboard/dashboard.html", context)
