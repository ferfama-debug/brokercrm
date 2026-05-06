from datetime import date, timedelta
from urllib.parse import quote
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from policies.models import Policy, Payment, EmailLog
from clients.models import Client
from .models import Alert


def generate_expiration_alerts():
    """
    Genera alertas internas y envía emails de vencimiento a los 30 y 15 días.
    """
    today = date.today()
    dias_aviso = [30, 15]
    limite = today + timedelta(days=30)

    policies = Policy.objects.filter(
        end_date__gte=today,
        end_date__lte=limite,
    ).select_related("client", "client__producer")

    for policy in policies:
        if not policy.client or not policy.client.producer:
            continue

        days = (policy.end_date - today).days

        # 1. Lógica de niveles para el dashboard interno
        if days <= 7:
            level = "CRITICA"
        elif days <= 15:
            level = "ALTA"
        else:
            level = "MEDIA"

        mensaje_interno = (
            f"La póliza {policy.policy_number} de {policy.client} vence en {days} días"
        )

        # Actualizar o crear alerta interna en el sistema
        Alert.objects.update_or_create(
            user=policy.client.producer,
            policy=policy,
            tipo="VENCIMIENTO",
            resolved=False,
            defaults={"message": mensaje_interno, "level": level},
        )

        # 2. Envío de Email Automático al Cliente (Solo a los 30 y 15 días)
        if days in dias_aviso and policy.client.email:
            enviar_mail_vencimiento_poliza(policy, days)

    # Limpieza: Resolver alertas si la póliza ya venció hace más de 30 días
    Alert.objects.filter(
        tipo="VENCIMIENTO",
        resolved=False,
        policy__end_date__lt=today - timedelta(days=30),
    ).update(resolved=True)


def enviar_mail_vencimiento_poliza(policy, dias):
    """
    Configuración estética del mail de vencimiento (Naranja).
    Anota la fecha de envío en la póliza para control.
    """
    cliente = policy.client

    html_content = f"""
    <div style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
        <div style="max-width:520px; margin:auto; background:white; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb;">
            <div style="background:#0f172a; padding:30px 20px; text-align:center;">
                <img src="https://crm.fuerzanaturalbroker.com/static/images/img/logo.png" style="width:160px; height:auto; display:block; margin:auto;" />
            </div>
            <div style="padding:28px 24px; color:#1f2937;">
                <h2 style="margin-top:0; text-align:center; color:#ed6c02;">¡Tu póliza vence pronto! ⏳</h2>
                <p style="font-size:16px; line-height:1.5; text-align:center;">Hola {cliente.first_name}, te informamos que tu cobertura finalizará en <strong>{dias} días</strong>:</p>
                
                <div style="background:#fff7ed; padding:16px; border-left:4px solid #ed6c02; margin:20px 0; font-size:15px;">
                    <strong>Póliza N°:</strong> {policy.policy_number}<br>
                    <strong>Vence el:</strong> {policy.end_date.strftime('%d/%m/%Y')}
                </div>

                <p style="font-size:15px; line-height:1.5; color:#4b5563; text-align:center;">
                    Es fundamental renovarla a tiempo para mantener tu protección activa. 
                    Si querés avanzar con la renovación o ver nuevas opciones, respondé este correo.
                </p>
                
                <hr style="border:0; border-top:1px solid #e5e7eb; margin:25px 0;">
                
                <p style="line-height:1.5; font-size:14px; text-align:center; color:#6b7280;">
                    Saludos,<br>
                    <strong>Fuerza Natural Broker de Seguros</strong>
                </p>
            </div>
        </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=f"⚠️ Aviso de Vencimiento: Póliza {policy.policy_number}",
            body=f"Hola {cliente.first_name}, tu póliza vence en {dias} días.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cliente.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        # Registro de éxito en la póliza y en logs
        policy.ultimo_envio_vencimiento = date.today()
        policy.save(update_fields=["ultimo_envio_vencimiento"])

        EmailLog.objects.create(
            policy=policy,
            client=cliente,
            tipo="VENCIMIENTO_POLIZA",
            estado="ENVIADO",
            destinatario=cliente.email,
            asunto=f"Aviso de Vencimiento: Póliza {policy.policy_number}",
        )

    except Exception as e:
        print(f"Error enviando mail de vencimiento: {e}")
        EmailLog.objects.create(
            policy=policy,
            client=cliente,
            tipo="VENCIMIENTO_POLIZA",
            estado="ERROR",
            destinatario=cliente.email,
            error=str(e),
        )


def generate_payment_reminders():
    """
    Detecta cuotas que vencen en 2 días y genera alertas internas.
    """
    today = date.today()
    target_date = today + timedelta(days=2)

    pagos = Payment.objects.filter(
        fecha_pago__isnull=True,
        fecha_vencimiento=target_date,
        recordatorio_enviado=False,
        policy__forma_pago="CUPONERA",
    ).select_related("policy", "policy__client", "policy__client__producer")

    for pago in pagos:
        if not pago.policy or not pago.policy.client:
            continue

        Alert.objects.get_or_create(
            user=pago.policy.client.producer,
            policy=pago.policy,
            tipo="PAGO_PROXIMO",
            resolved=False,
            defaults={
                "message": f"Recordatorio: {pago.policy.client} tiene el vencimiento de la cuota #{pago.numero_cuota} en 2 días.",
                "level": "ALTA",
            },
        )


def generate_debt_alerts():
    pagos_vencidos = Payment.objects.filter(
        fecha_vencimiento__lt=date.today(), fecha_pago__isnull=True
    ).select_related("policy", "policy__client", "policy__client__producer")

    policies_con_deuda = set()

    for pago in pagos_vencidos:
        if not pago.policy or not pago.policy.client:
            continue

        policy = pago.policy
        policies_con_deuda.add(policy.id)

        Alert.objects.get_or_create(
            user=policy.client.producer,
            policy=policy,
            tipo="DEUDA",
            resolved=False,
            defaults={
                "message": f"Cuota vencida #{pago.numero_cuota} de la póliza {policy.policy_number}",
                "level": "CRITICA",
            },
        )

    Alert.objects.filter(tipo="DEUDA", resolved=False).exclude(
        policy_id__in=policies_con_deuda
    ).update(resolved=True)


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

        Alert.objects.get_or_create(
            user=cliente.producer,
            tipo="CUMPLEANIOS",
            resolved=False,
            defaults={"message": mensaje, "level": "MEDIA"},
        )


def generar_todas_las_alertas():
    generate_expiration_alerts()
    generate_payment_reminders()
    generate_debt_alerts()
    generate_birthday_alerts()


def generar_link_whatsapp(cliente, mensaje):
    telefono = getattr(cliente, "phone", "") or getattr(cliente, "telefono", "")
    if not telefono:
        return "#"

    telefono = str(telefono).replace(" ", "").replace("-", "").replace("+", "")
    texto = quote(mensaje)
    return f"https://wa.me/{telefono}?text={texto}"


def whatsapp_deuda(pago):
    if not pago.policy or not pago.policy.client:
        return "#"
    mensaje = f"Hola {pago.policy.client.first_name}, te escribo por tu póliza N° {pago.policy.policy_number}. Tenés una cuota vencida (#{pago.numero_cuota}). ¿Querés que te ayude a regularizarla?"
    return generar_link_whatsapp(pago.policy.client, mensaje)


def whatsapp_vencimiento(policy):
    if not policy.client:
        return "#"
    mensaje = f"Hola {policy.client.first_name}, tu póliza N° {policy.policy_number} vence el {policy.end_date}. ¿Querés que avancemos con la renovación?"
    return generar_link_whatsapp(policy.client, mensaje)
