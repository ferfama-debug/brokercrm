from datetime import date
from django.core.mail import send_mail
from django.conf import settings

from policies.models import Policy
from .models import Alert


def generate_expiration_alerts():

    today = date.today()

    policies = Policy.objects.filter(end_date__gte=today)

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
            level=level,
            defaults={
                "message": f"La póliza {policy.policy_number} vence en {days} días"
            },
        )

        if days == 7 and created:

            subject = "⚠ Póliza por vencer en 7 días"

            message = f"""
Cliente: {policy.client}

Compañía: {policy.company}
Póliza: {policy.policy_number}

La póliza vence el {policy.end_date}.

Contactar al cliente para renovación.
"""

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [policy.client.producer.email],
                fail_silently=True,
            )
