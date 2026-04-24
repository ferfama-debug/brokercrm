from datetime import date, datetime
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractMonth
from django.shortcuts import render

from alerts.models import Alert
from alerts.services import generar_todas_las_alertas
from clients.models import Client
from policies.models import Policy, Payment


User = get_user_model()


def _nombre_compania(poliza):
    return poliza.company or "Sin compañía"


def _mensaje_renovacion(poliza):
    return (
        f"Hola {poliza.client.first_name}, te escribo de Fuerza Natural Broker. "
        f"Tu póliza {poliza.policy_number} de {_nombre_compania(poliza)} vence el {poliza.end_date}. "
        f"Si querés podemos renovarla o revisar mejores opciones."
    )


def _mensaje_cobranza_vencida(poliza):
    return (
        f"Hola {poliza.client.first_name}, te escribo de Fuerza Natural Broker. "
        f"Tenés una cuota vencida de la póliza {poliza.policy_number} ({_nombre_compania(poliza)}). "
        f"¿Podés enviarnos el comprobante así la registramos?"
    )


def _mensaje_cobranza_proxima(poliza, pago):
    return (
        f"Hola {poliza.client.first_name}, te recordamos una cuota próxima a vencer "
        f"de tu póliza {poliza.policy_number} ({_nombre_compania(poliza)}). "
        f"Vence el {pago.fecha_vencimiento}."
    )


def _mensaje_cuponera(poliza, proximo_pago):
    return (
        f"Hola {poliza.client.first_name}. "
        f"Te recordamos el pago de la cuponera de tu póliza "
        f"{poliza.policy_number} de {_nombre_compania(poliza)}. "
        f"Vence el {proximo_pago}."
    )


@login_required
def home(request):
    try:
        generar_todas_las_alertas()
    except Exception as e:
        print("⚠️ No se pudieron generar alertas automáticamente:", e)

    hoy = date.today()
    buscar = request.GET.get("buscar", "").strip()

    if request.user.is_superuser:
        policies = Policy.objects.select_related("client").prefetch_related("pagos")
        pagos_base = Payment.objects.select_related("policy", "policy__client")
    else:
        policies = (
            Policy.objects.filter(client__producer=request.user)
            .select_related("client")
            .prefetch_related("pagos")
        )
        pagos_base = Payment.objects.filter(
            policy__client__producer=request.user
        ).select_related("policy", "policy__client")

    if buscar:
        policies = policies.filter(
            Q(client__first_name__icontains=buscar)
            | Q(client__last_name__icontains=buscar)
        )

    polizas_por_vencer = []
    clientes_llamar = []
    pagos_cuponera = []
    cobranzas_urgentes = []
    cobranzas_proximas = []

    vencen_semana = 0
    vencen_7 = 0
    vencen_15 = 0
    vencen_30 = 0

    for p in policies:
        dias = (p.end_date - hoy).days
        mensaje = _mensaje_renovacion(p)
        telefono = getattr(p.client, "phone", "")

        if dias >= 0:
            polizas_por_vencer.append(
                {
                    "cliente": p.client,
                    "numero": p.policy_number,
                    "compania": _nombre_compania(p),
                    "vencimiento": p.end_date,
                    "dias": dias,
                    "telefono": telefono,
                    "mensaje": mensaje,
                }
            )

            if dias <= 30:
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
                        "telefono": telefono,
                        "numero": p.policy_number,
                        "dias": dias,
                        "mensaje": mensaje,
                    }
                )

        for pago in p.pagos.all():
            dias_pago = (pago.fecha_vencimiento - hoy).days

            if pago.estado == "VENCIDO":
                cobranzas_urgentes.append(
                    {
                        "cliente": p.client,
                        "numero": p.policy_number,
                        "telefono": telefono,
                        "mensaje": _mensaje_cobranza_vencida(p),
                        "dias": dias_pago,
                    }
                )

            elif pago.estado == "PENDIENTE" and 0 <= dias_pago <= 5:
                cobranzas_proximas.append(
                    {
                        "cliente": p.client,
                        "numero": p.policy_number,
                        "telefono": telefono,
                        "mensaje": _mensaje_cobranza_proxima(p, pago),
                        "dias": dias_pago,
                    }
                )

        if p.forma_pago == "CUPONERA" and p.frecuencia_cuponera and p.cuponera_pdf:
            proximo_pago = p.proximo_pago_cuponera

            if proximo_pago:
                dias_pago = (proximo_pago - hoy).days

                if 0 <= dias_pago <= 5:
                    pagos_cuponera.append(
                        {
                            "cliente": p.client,
                            "numero": p.policy_number,
                            "company": _nombre_compania(p),
                            "fecha": proximo_pago,
                            "telefono": telefono,
                            "mensaje": _mensaje_cuponera(p, proximo_pago),
                            "pdf": p.cuponera_pdf,
                        }
                    )

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
        clientes_llamar_agrupados.values(),
        key=lambda x: x["dias"],
    )

    polizas_por_vencer = sorted(polizas_por_vencer, key=lambda x: x["dias"])
    cobranzas_urgentes = sorted(cobranzas_urgentes, key=lambda x: x["dias"])
    cobranzas_proximas = sorted(cobranzas_proximas, key=lambda x: x["dias"])
    pagos_cuponera = sorted(pagos_cuponera, key=lambda x: x["fecha"])

    cobranzas_vencidas = pagos_base.filter(
        fecha_vencimiento__lt=hoy,
        fecha_pago__isnull=True,
    ).count()

    cobranzas_hoy = pagos_base.filter(
        fecha_vencimiento=hoy,
        fecha_pago__isnull=True,
    ).count()

    cobranzas_proximos = pagos_base.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=hoy.replace(day=hoy.day) if False else hoy,
    ).count()

    from datetime import timedelta

    cobranzas_proximos = pagos_base.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=3),
        fecha_pago__isnull=True,
    ).count()

    deuda_total = (
        pagos_base.filter(
            fecha_vencimiento__lt=hoy,
            fecha_pago__isnull=True,
        ).aggregate(total=Sum("monto"))["total"]
        or 0
    )

    if request.user.is_superuser:
        alertas_count = Alert.objects.filter(resolved=False).count()
    else:
        alertas_count = Alert.objects.filter(user=request.user, resolved=False).count()

    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

    if request.user.is_superuser:
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

        clientes_query = Client.objects.annotate(
            total_polizas=Count("policy")
        ).order_by("-total_polizas")[:5]

        total_clientes = Client.objects.count()
        total_polizas = Policy.objects.count()
        total_usuarios = User.objects.count()
    else:
        produccion_mes = Policy.objects.filter(
            client__producer=request.user,
            start_date__month=mes_actual,
            start_date__year=anio_actual,
        ).count()

        renovaciones_mes = Policy.objects.filter(
            client__producer=request.user,
            end_date__month=mes_actual,
            end_date__year=anio_actual,
        ).count()

        produccion_companias = (
            Policy.objects.filter(client__producer=request.user)
            .values("company")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        clientes_query = (
            Client.objects.filter(producer=request.user)
            .annotate(total_polizas=Count("policy"))
            .order_by("-total_polizas")[:5]
        )

        total_clientes = Client.objects.filter(producer=request.user).count()
        total_polizas = Policy.objects.filter(client__producer=request.user).count()
        total_usuarios = 1

    companias = [c["company"] or "Sin compañía" for c in produccion_companias]
    cantidades = [c["total"] for c in produccion_companias]

    if request.user.is_superuser:
        crecimiento = (
            Policy.objects.annotate(mes=ExtractMonth("start_date"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
    else:
        crecimiento = (
            Policy.objects.filter(client__producer=request.user)
            .annotate(mes=ExtractMonth("start_date"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

    meses = [c["mes"] for c in crecimiento]
    totales = [c["total"] for c in crecimiento]

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
        "clientes": total_clientes,
        "polizas": total_polizas,
        "alertas": alertas_count,
        "usuarios": total_usuarios,
        "polizas_por_vencer": polizas_por_vencer,
        "clientes_llamar": clientes_llamar,
        "pagos_cuponera": pagos_cuponera,
        "cobranzas_urgentes": cobranzas_urgentes,
        "cobranzas_proximas": cobranzas_proximas,
        "cobranzas_vencidas": cobranzas_vencidas,
        "cobranzas_hoy": cobranzas_hoy,
        "cobranzas_proximos": cobranzas_proximos,
        "deuda_total": deuda_total,
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
