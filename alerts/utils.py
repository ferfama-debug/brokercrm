from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from policies.models import Policy


def check_policy_expirations():
    today = timezone.now().date()

    alert_days = [7, 3, 0]

    for days in alert_days:
        target_date = today + timedelta(days=days)

        policies = Policy.objects.filter(end_date=target_date)

        for policy in policies:
            subject = f"⚠️ Póliza por vencer ({days} días)"

            message = f"""
Hola {policy.client.name},

Tu póliza tipo {policy.policy_type} vence el {policy.end_date}.

Por favor contactate con nosotros para renovarla.

Fuerza Natural Broker de Seguros
"""

            send_mail(
                subject,
                message,
                None,
                [policy.client.email],
                fail_silently=False,
            )