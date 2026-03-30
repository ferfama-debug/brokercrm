from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from policies.models import Policy


def check_policy_expirations():
    today = timezone.now().date()

    alert_days = [7, 3, 0]

    for days in alert_days:
        target_date = today + timedelta(days=days)

        policies = Policy.objects.filter(
            end_date=target_date
        ).select_related("client")

        for policy in policies:

            if not policy.client.email:
                continue

            subject = f"⚠️ Póliza por vencer ({days} días)"

            mensaje = f"""
Hola {policy.client.first_name},

Tu póliza N° {policy.policy_number} ({policy.tipo_poliza})
vence el {policy.end_date}.

Por favor contactate con nosotros para renovarla.

Fuerza Natural Broker de Seguros
"""

            try:
                send_mail(
                    subject,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [policy.client.email],
                    fail_silently=True,
                )
            except Exception as e:
                print("❌ Error enviando mail:", e)