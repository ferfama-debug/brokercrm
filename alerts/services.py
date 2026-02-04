from datetime import date
from policies.models import Policy
from .models import Alert

def generate_expiration_alerts():
    today = date.today()

    for policy in Policy.objects.all():
        days = (policy.end_date - today).days

        if days < 0:
            continue

        if days <= 7:
            level = 'CRITICA'
        elif days <= 15:
            level = 'ALTA'
        elif days <= 30:
            level = 'MEDIA'
        else:
            continue

        Alert.objects.get_or_create(
            user=policy.client.producer,
            policy=policy,
            level=level,
            defaults={
                'message': f'La póliza {policy.policy_number} vence en {days} días'
            }
        )
