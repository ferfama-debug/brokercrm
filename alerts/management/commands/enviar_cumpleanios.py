from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from clients.models import Client
from alerts.models import Alert


class Command(BaseCommand):
    help = "Envía emails automáticos de cumpleaños a clientes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula el envío sin mandar emails ni crear alertas",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
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
        errores = 0

        for cliente in clientes:
            if not cliente.producer:
                omitidos += 1
                continue

            mensaje = (
                f"Cumpleaños {hoy.year}: "
                f"Hoy es el cumpleaños de {cliente.first_name} {cliente.last_name}"
            )

            ya_enviado = Alert.objects.filter(
                user=cliente.producer,
                tipo="CUMPLEANIOS",
                message=mensaje,
                resolved=False,
            ).exists()

            if ya_enviado:
                omitidos += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Enviaría mail a {cliente.email} - {cliente}"
                )
                enviados += 1
                continue

            try:
                send_mail(
                    subject=f"¡Feliz cumpleaños {cliente.first_name}!",
                    message=(
                        f"Hola {cliente.first_name},\n\n"
                        "Te deseamos un muy feliz cumpleaños.\n\n"
                        "¡Que tengas un excelente día!\n\n"
                        "Fuerza Natural Broker"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cliente.email],
                    fail_silently=False,
                )

                Alert.objects.create(
                    user=cliente.producer,
                    tipo="CUMPLEANIOS",
                    resolved=False,
                    message=mensaje,
                    level="MEDIA",
                )

                enviados += 1

            except Exception as e:
                errores += 1
                self.stderr.write(f"Error enviando cumpleaños a {cliente.email}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Cumpleaños procesados. Enviados: {enviados}. "
                f"Omitidos: {omitidos}. Errores: {errores}."
            )
        )
