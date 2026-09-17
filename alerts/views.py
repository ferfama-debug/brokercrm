from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from policies.models import Payment, Policy
from .models import Alert

from .services import generar_todas_las_alertas


@login_required
def alertas(request):

    # 🟢 LIMPIEZA AUTOMÁTICA: Marcar como resueltas las alertas de pólizas que ya fueron renovadas
    polizas_renovadas_ids_all = Policy.objects.filter(
        renovacion_de__isnull=False
    ).values_list("renovacion_de", flat=True)
    
    if polizas_renovadas_ids_all.exists():
        Alert.objects.filter(
            policy_id__in=polizas_renovadas_ids_all,
            resolved=False
        ).update(resolved=True)

    generar_todas_las_alertas()

    # 🟢 SOLUCIÓN ESTÁNDAR: Buscamos los IDs de pólizas que SÍ tienen cuotas pagadas (excluyendo anuladas)
    polizas_pagadas = Payment.objects.filter(
        fecha_pago__isnull=False,
        policy__anulada=False
    ).values_list("policy_id", flat=True)

    # 🟢 LIMPIEZA AUTOMÁTICA SEGURA: Resolvemos las alertas de esas pólizas sin romper el SQL
    if polizas_pagadas.exists():
        Alert.objects.filter(
            tipo__in=["PAGO_PROXIMO", "DEUDA"],
            resolved=False,
            policy_id__in=polizas_pagadas,
        ).update(resolved=True)

    nivel = request.GET.get("nivel", "")
    tab = request.GET.get("tab", "alertas")  # 👈 Pestaña activa por defecto

    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False, policy__anulada=False)
    else:
        alertas = Alert.objects.filter(user=request.user, resolved=False, policy__anulada=False)

    if nivel:
        alertas = alertas.filter(level=nivel)

    alertas = alertas.order_by("-created_at")

    hoy = date.today()
    limite_vencimiento = hoy + timedelta(days=30)

    # Filtramos estrictamente por cuotas que NO tengan fecha de pago asentada
    estados_criticos = ["VENCIDO", "HOY", "PROXIMO"]

    # IDs de pólizas que ya tienen una renovación creada para excluirlas
    polizas_renovadas_ids = Policy.objects.filter(
        renovacion_de__isnull=False
    ).values("renovacion_de")

    if request.user.is_superuser:
        polizas_por_vencer = Policy.objects.filter(
            anulada=False,
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        ).exclude(id__in=polizas_renovadas_ids)
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos, 
            fecha_pago__isnull=True,
            policy__anulada=False
        ).select_related("policy__client")
        
        policies_for_cuponera = Policy.objects.filter(anulada=False).exclude(id__in=polizas_renovadas_ids)
    else:
        polizas_por_vencer = Policy.objects.filter(
            client__producer=request.user,
            anulada=False,
            end_date__gte=hoy,
            end_date__lte=limite_vencimiento,
        ).exclude(id__in=polizas_renovadas_ids)
        pagos_vencidos = Payment.objects.filter(
            estado__in=estados_criticos,
            fecha_pago__isnull=True,
            policy__client__producer=request.user,
            policy__anulada=False,
        ).select_related("policy__client")
        
        policies_for_cuponera = Policy.objects.filter(
            client__producer=request.user,
            anulada=False
        ).exclude(id__in=polizas_renovadas_ids)

    clientes_con_deuda = {
        pago.policy.client
        for pago in pagos_vencidos
        if pago.policy and pago.policy.client
    }

    # 🟢 PROCESAMIENTO DE CUPONERAS PRÓXIMAS A VENCER
    pagos_cuponera = []
    for p in policies_for_cuponera:
        if getattr(p, 'forma_pago', None) == "CUPONERA" and getattr(p, 'frecuencia_cuponera', None):
            proximo_pago = getattr(p, 'proximo_pago_cuponera', None)
            if proximo_pago:
                dias_pago = (proximo_pago - hoy).days
                if dias_pago <= 30:
                    telefono = ""
                    if p.client:
                        telefono = getattr(p.client, "phone", "") or getattr(p.client, "telefono", "")
                    
                    nombre_cliente = p.client.nombre_completo() if p.client and hasattr(p.client, "nombre_completo") else (f"{p.client.first_name} {p.client.last_name}" if p.client else "Cliente")
                    
                    pagos_cuponera.append({
                        "cliente": p.client,
                        "numero": p.policy_number,
                        "company": p.company or "Sin compañía",
                        "fecha": proximo_pago,
                        "dias": dias_pago,
                        "telefono": telefono,
                        "mensaje": f"Hola {nombre_cliente}, te recordamos el pago de la cuponera de tu póliza N° {p.policy_number} de {p.company or 'Sin compañía'} que vence el {proximo_pago.strftime('%d/%m/%Y')}." if hasattr(proximo_pago, 'strftime') else f"Vence el {proximo_pago}",
                        "pdf": getattr(p, 'cuponera_pdf', None),
                    })

    pagos_cuponera = sorted(pagos_cuponera, key=lambda x: x["fecha"])

    return render(
        request,
        "alerts/alertas.html",
        {
            "alertas": alertas,
            "nivel": nivel,
            "tab": tab,
            "polizas_por_vencer": polizas_por_vencer,
            "clientes_con_deuda": clientes_con_deuda,
            "pagos_cuponera": pagos_cuponera,
        },
    )
