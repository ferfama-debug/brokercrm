from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from clients.models import Client
from alerts.models import Alert


class Command(BaseCommand):
    help = "Envía emails automáticos de cumpleaños a clientes"

    def handle(self, *args, **kwargs):
        hoy = timezone.localdate()

        clientes = (
            Client.objects.filter(
                fecha_nacimiento__day=hoy.day,
                fecha_nacimiento__month=hoy.month,
                email__isnull=False,
            )
            .exclude(email="")
            .select_related("producer")
        )

        enviados = 0
        omitidos = 0

        for cliente in clientes:
            if not cliente.producer:
                omitidos += 1
                continue

            mensaje = (
                f"Hoy es el cumpleaños de {cliente.first_name} {cliente.last_name}"
            )

            ya_existe = Alert.objects.filter(
                user=cliente.producer,
                tipo="CUMPLEANIOS",
                message=mensaje,
                resolved=False,
            ).exists()

            if ya_existe:
                omitidos += 1
                continue

            Alert.objects.create(
                user=cliente.producer,
                tipo="CUMPLEANIOS",
                resolved=False,
                message=mensaje,
                level="MEDIA",
            )

            send_mail(
                subject=f"¡Feliz cumpleaños {cliente.first_name}!",
                message=(
                    f"Hola {cliente.first_name},\n\n"
                    "Te deseamos un muy feliz cumpleaños.\n\n"
                    "¡Que tengas un excelente día!\n\n"
                    "Saludos."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[cliente.email],
                fail_silently=False,
            )

            enviados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cumpleaños procesados. Enviados: {enviados}. Omitidos: {omitidos}."
            )
        )
