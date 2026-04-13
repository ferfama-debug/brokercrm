from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from urllib.parse import quote

from policies.models import Policy, Payment
from clients.models import Client
from .models import Alert


def generate_expiration_alerts():

    today = date.today()
    limite = today + timedelta(days=30)

    policies = Policy.objects.filter(
        end_date__gte=today,
        end_date__lte=limite,
    ).select_related("client", "client__producer")

    for policy in policies:

        if not policy.client or not policy.client.producer:
            continue

        days = (policy.end_date - today).days

        if days <= 7:
            level = "CRITICA"
        elif days <= 15:
            level = "ALTA"
        else:
            level = "MEDIA"

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
            if alerta.message != mensaje or alerta.level != level:
                alerta.message = mensaje
                alerta.level = level
                alerta.save()
        else:
            Alert.objects.create(
                user=policy.client.producer,
                policy=policy,
                tipo="VENCIMIENTO",
                resolved=False,
                message=mensaje,
                level=level,
            )

        if days == 7 and policy.client.producer.email:
            send_mail(
                "⚠ Póliza por vencer en 7 días",
                f"La póliza {policy.policy_number} vence el {policy.end_date}",
                settings.DEFAULT_FROM_EMAIL,
                [policy.client.producer.email],
                fail_silently=True,
            )

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
        "policy", "policy__client", "policy__client__producer"
    )

    policies_con_deuda = set()

    for pago in pagos_vencidos:

        if not pago.policy or not pago.policy.client:
            continue

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

    alertas_deuda = Alert.objects.filter(
        tipo="DEUDA",
        resolved=False,
    ).select_related("policy")

    for alerta in alertas_deuda:
        if alerta.policy_id not in policies_con_deuda:
            alerta.resolved = True
            alerta.save()


def generate_birthday_alerts():

    today = date.today()

    clientes = Client.objects.filter(
        fecha_nacimiento__day=today.day,
        fecha_nacimiento__month=today.month,
    ).select_related("producer")

    for cliente in clientes:

        if not cliente.producer:
            continue

        mensaje = f"Hoy es el cumpleaños de {cliente.first_name} {cliente.last_name}"

        alerta = Alert.objects.filter(
            user=cliente.producer,
            tipo="CUMPLEANIOS",
            message=mensaje,
            resolved=False,
        ).first()

        if not alerta:
            Alert.objects.create(
                user=cliente.producer,
                tipo="CUMPLEANIOS",
                resolved=False,
                message=mensaje,
                level="MEDIA",
            )


def generar_todas_las_alertas():
    generate_expiration_alerts()
    generate_debt_alerts()
    generate_birthday_alerts()


def generar_link_whatsapp(cliente, mensaje):
    telefono = getattr(cliente, "phone", "") or getattr(cliente, "telefono", "")
    telefono = telefono.replace(" ", "").replace("-", "")
    texto = quote(mensaje)
    return f"https://wa.me/{telefono}?text={texto}"


def whatsapp_deuda(pago):
    if not pago.policy or not pago.policy.client:
        return "#"

    cliente = pago.policy.client

    mensaje = (
        f"Hola {cliente.first_name}, te escribo por tu póliza N° {pago.policy.policy_number}. "
        f"Tenés una cuota vencida (#{pago.numero_cuota}). "
        "¿Querés que te ayude a regularizarla?"
    )

    return generar_link_whatsapp(cliente, mensaje)


def whatsapp_vencimiento(policy):
    if not policy.client:
        return "#"

    cliente = policy.client

    mensaje = (
        f"Hola {cliente.first_name}, tu póliza N° {policy.policy_number} "
        f"vence el {policy.end_date}. "
        "¿Querés que avancemos con la renovación?"
    )

    return generar_link_whatsapp(cliente, mensaje)
