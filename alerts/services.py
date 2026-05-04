from datetime import date, timedelta
from urllib.parse import quote

from policies.models import Policy, Payment
from clients.models import Client
from .models import Alert

# Si llegas a tener un archivo dedicado solo a emails, lo importarías aquí
# from alerts.emails import enviar_email_cuponera


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


def generate_payment_reminders():
    """
    Detecta cuotas que vencen en 2 días y genera alertas.
    Aquí es donde se integrará el envío de mail automático.
    """
    today = date.today()
    target_date = today + timedelta(days=2)  # Exactamente 2 días antes

    # Buscamos pagos pendientes que vencen en 2 días
    pagos = Payment.objects.filter(
        fecha_pago__isnull=True,
        fecha_vencimiento=target_date,  # Usamos la fecha exacta de la cuota
        recordatorio_enviado=False,
        policy__forma_pago="CUPONERA",
    ).select_related("policy", "policy__client", "policy__client__producer")

    for pago in pagos:
        if not pago.policy or not pago.policy.client:
            continue

        cliente = pago.policy.client
        producer = cliente.producer

        # 1. Crear Alerta interna para el Broker (vos)
        mensaje_interno = f"Recordatorio: {cliente} tiene el vencimiento de la cuota #{pago.numero_cuota} en 2 días."

        Alert.objects.get_or_create(
            user=producer,
            policy=pago.policy,
            tipo="PAGO_PROXIMO",
            resolved=False,
            defaults={"message": mensaje_interno, "level": "ALTA"},
        )

        # 2. Lógica de Envío de Email Automático al Cliente
        # Aquí llamarías a tu función de envío de mail real
        # success = enviar_email_cuponera(pago)
        # if success:
        #     pago.recordatorio_enviado = True
        #     pago.save()


def generate_debt_alerts():
    # Buscamos pagos que ya pasaron su fecha y no están pagados
    pagos_vencidos = Payment.objects.filter(
        fecha_vencimiento__lt=date.today(), fecha_pago__isnull=True
    ).select_related("policy", "policy__client", "policy__client__producer")

    policies_con_deuda = set()

    for pago in pagos_vencidos:
        if not pago.policy or not pago.policy.client:
            continue

        policy = pago.policy
        cliente = policy.client
        policies_con_deuda.add(policy.id)

        mensaje = (
            f"Cuota vencida #{pago.numero_cuota} de la póliza {policy.policy_number}"
        )

        alerta = Alert.objects.filter(
            user=cliente.producer,
            policy=policy,
            tipo="DEUDA",
            resolved=False,
        ).first()

        if not alerta:
            Alert.objects.create(
                user=cliente.producer,
                policy=policy,
                tipo="DEUDA",
                resolved=False,
                message=mensaje,
                level="CRITICA",
            )

    # Resolvemos alertas de deuda si el pago ya se registró
    alertas_activas = Alert.objects.filter(tipo="DEUDA", resolved=False)
    for alerta in alertas_activas:
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
    generate_payment_reminders()
    generate_debt_alerts()
    generate_birthday_alerts()


def generar_link_whatsapp(cliente, mensaje):
    # Intentamos obtener el teléfono de cualquiera de los dos campos posibles
    telefono = getattr(cliente, "phone", "") or getattr(cliente, "telefono", "")
    if not telefono:
        return "#"

    telefono = str(telefono).replace(" ", "").replace("-", "").replace("+", "")
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
