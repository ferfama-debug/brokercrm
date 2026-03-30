from datetime import date
from django.core.mail import send_mail
from django.conf import settings
from urllib.parse import quote

from policies.models import Policy, Payment
from .models import Alert


def generate_expiration_alerts():

    today = date.today()

    # 🔥 SOLO PÓLIZAS DENTRO DE 30 DÍAS
    policies = Policy.objects.filter(
        end_date__gte=today,
        end_date__lte=today.replace(day=today.day),
    ).select_related(
        "client",
        "client__producer"
    )

    # 🔥 FIX rango real de 30 días
    policies = [
        policy for policy in policies
        if 0 <= (policy.end_date - today).days <= 30
    ]

    for policy in policies:

        days = (policy.end_date - today).days

        if days <= 7:
            level = "CRITICA"
        elif days <= 15:
            level = "ALTA"
        elif days <= 30:
            level = "MEDIA"
        else:
            continue

        mensaje = (
            f"La póliza {policy.policy_number} del cliente {policy.client} "
            f"vence en {days} días"
        )

        alerta = Alert.objects.filter(
            user=policy.client.producer,
            policy=policy,
            tipo="VENCIMIENTO",
            resolved=False,
        ).first()

        if alerta:
            cambios = False

            if alerta.message != mensaje:
                alerta.message = mensaje
                cambios = True

            if alerta.level != level:
                alerta.level = level
                cambios = True

            if cambios:
                alerta.save()
        else:
            alerta = Alert.objects.create(
                user=policy.client.producer,
                policy=policy,
                tipo="VENCIMIENTO",
                resolved=False,
                message=mensaje,
                level=level,
            )

            if days == 7 and policy.client.producer.email:

                subject = "⚠ Póliza por vencer en 7 días"

                message = f"""
Cliente: {policy.client}

Compañía: {policy.company}
Número de póliza: {policy.policy_number}

La póliza vence el {policy.end_date}.

Se recomienda contactar al cliente para gestionar la renovación.
"""

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [policy.client.producer.email],
                    fail_silently=True,
                )

    # 🔥 AUTO-RESOLVER ALERTAS DE VENCIMIENTO QUE YA NO APLICAN
    alertas_vencimiento = Alert.objects.filter(
        tipo="VENCIMIENTO",
        resolved=False,
    ).select_related("policy")

    for alerta in alertas_vencimiento:
        if not alerta.policy:
            continue

        dias = (alerta.policy.end_date - today).days
        if dias < 0 or dias > 30:
            alerta.resolved = True
            alerta.save()


def generate_debt_alerts():

    pagos_vencidos = Payment.objects.filter(estado="VENCIDO").select_related(
        "policy",
        "policy__client",
        "policy__client__producer"
    )

    policies_con_deuda = set()

    for pago in pagos_vencidos:

        policy = pago.policy
        cliente = policy.client
        policies_con_deuda.add(policy.id)

        mensaje = f"Cliente con deuda en cuota #{pago.numero_cuota}"

        alerta = Alert.objects.filter(
            user=cliente.producer,
            policy=policy,
            tipo="DEUDA",
            resolved=False,
        ).first()

        if alerta:
            if alerta.message != mensaje or alerta.level != "CRITICA":
                alerta.message = mensaje
                alerta.level = "CRITICA"
                alerta.save()
        else:
            Alert.objects.create(
                user=cliente.producer,
                policy=policy,
                tipo="DEUDA",
                resolved=False,
                message=mensaje,
                level="CRITICA",
            )

    # 🔥 AUTO-RESOLVER ALERTAS DE DEUDA SI YA NO HAY PAGOS VENCIDOS
    alertas_deuda = Alert.objects.filter(
        tipo="DEUDA",
        resolved=False,
    ).select_related("policy")

    for alerta in alertas_deuda:
        if alerta.policy_id not in policies_con_deuda:
            alerta.resolved = True
            alerta.save()


def generar_todas_las_alertas():

    generate_expiration_alerts()
    generate_debt_alerts()


def generar_link_whatsapp(cliente, mensaje):

    telefono = (
        getattr(cliente, "phone", "") or getattr(cliente, "telefono", "")
    )

    telefono = telefono.replace(" ", "").replace("-", "")

    texto = quote(mensaje)

    return f"https://wa.me/{telefono}?text={texto}"


def whatsapp_deuda(pago):

    cliente = pago.policy.client

    mensaje = (
        f"Hola {cliente.first_name}, te escribo por tu póliza N° {pago.policy.policy_number}. "
        f"Tenés una cuota vencida (#{pago.numero_cuota}). "
        "¿Querés que te ayude a regularizarla?"
    )

    return generar_link_whatsapp(cliente, mensaje)


def whatsapp_vencimiento(policy):

    cliente = policy.client

    mensaje = (
        f"Hola {cliente.first_name}, tu póliza N° {policy.policy_number} "
        f"vence el {policy.end_date}. "
        "¿Querés que avancemos con la renovación?"
    )

    return generar_link_whatsapp(cliente, mensaje)