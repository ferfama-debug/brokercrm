from datetime import date
from django.core.mail import send_mail
from django.conf import settings

from policies.models import Policy
from .models import Alert


def generate_expiration_alerts():

    today = date.today()

    # Trae pólizas vigentes con relaciones optimizadas
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

        # Evita duplicar alertas del mismo tipo
        alert, created = Alert.objects.get_or_create(
            user=policy.client.producer,
            policy=policy,
            level=level,
            resolved=False,
            defaults={
                "message": f"La póliza {policy.policy_number} del cliente {policy.client} vence en {days} días"
            },
        )

        # Enviar email solo cuando faltan exactamente 7 días
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
