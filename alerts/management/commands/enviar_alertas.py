from django.core.management.base import BaseCommand
from alerts.services import generate_expiration_alerts


class Command(BaseCommand):

    help = "Genera alertas y envía emails de vencimiento"

    def handle(self, *args, **kwargs):

        generate_expiration_alerts()

        self.stdout.write(
            self.style.SUCCESS("Alertas de vencimiento revisadas correctamente")
        )