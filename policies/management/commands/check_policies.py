from django.core.management.base import BaseCommand
from policies.models import Policy
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Verifica pólizas próximas a vencer"

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        limite = hoy + timedelta(days=3)

        # 🔥 CORRECCIÓN AQUÍ
        policies = Policy.objects.filter(end_date__range=(hoy, limite))

        if not policies.exists():
            self.stdout.write("No hay pólizas por vencer")
            return

        for policy in policies:
            self.stdout.write(f"⚠️ Póliza por vencer: {policy}")

        self.stdout.write(self.style.SUCCESS("✔ Chequeo completado"))