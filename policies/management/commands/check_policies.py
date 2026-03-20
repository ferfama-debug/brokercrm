from django.core.management.base import BaseCommand
from policies.models import Policy
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Verifica pólizas próximas a vencer"

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        limite = hoy + timedelta(days=3)

        policies = Policy.objects.filter(vigencia_hasta__range=(hoy, limite))

        for policy in policies:
            self.stdout.write(f"⚠️ Póliza por vencer: {policy}")

        self.stdout.write(self.style.SUCCESS("✔ Chequeo completado"))
