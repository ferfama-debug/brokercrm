from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from urllib.parse import quote

from policies.models import Policy, Payment
from .models import Alert


def generate_expiration_alerts():

    today = date.today()

    policies = Policy.objects.filter(
        end_date__gte=today
    ).select_related(
        "client",
        "client__producer"
    )

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

        alert, created = Alert.objects.get_or_create(
            user=policy.client.producer,
            policy=policy,
            tipo="VENCIMIENTO",
            resolved=False,
            defaults={
                "message": f"La póliza {policy.policy_number} del cliente {policy.client} vence en {days} días",
                "level": level,
            },
        )

        if days == 7 and created and policy.client.producer.email:

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


# 🔥 ALERTAS DE DEUDA
def generate_debt_alerts():

    pagos_vencidos = Payment.objects.filter(estado="VENCIDO").select_related(
        "policy",
        "policy__client",
        "policy__client__producer"
    )

    for pago in pagos_vencidos:

        policy = pago.policy
        cliente = policy.client

        Alert.objects.get_or_create(
            user=cliente.producer,
            policy=policy,
            tipo="DEUDA",
            resolved=False,
            defaults={
                "message": f"Cliente con deuda en cuota #{pago.numero_cuota}",
                "level": "CRITICA",
            },
        )


# 🔥 FUNCIÓN CENTRAL
def generar_todas_las_alertas():

    generate_expiration_alerts()
    generate_debt_alerts()


# =========================
# 🔥 WHATSAPP (NUEVO)
# =========================

def generar_link_whatsapp(cliente, mensaje):

    telefono = cliente.phone.replace(" ", "").replace("-", "")

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