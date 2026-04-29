from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
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
                html_content = f"""
                <div style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
                    <div style="max-width:500px; margin:auto; background:white; border-radius:10px; overflow:hidden;">

                        <div style="background:#0f172a; color:white; padding:20px; text-align:center;">
                            <h2>Fuerza Natural Broker</h2>
                            <p>Broker de Seguros</p>
                        </div>

                        <div style="padding:25px;">
                            <h3>Hola {cliente.first_name} 👋</h3>

                            <p>🎉 Hoy es un día especial.</p>

                            <p>Desde <strong>Fuerza Natural Broker</strong> queremos desearte un muy feliz cumpleaños.</p>

                            <p>Esperamos que tengas un gran día y un excelente año por delante.</p>

                            <div style="text-align:center; margin:30px 0;">
                                <div style="display:inline-block; background:#2563eb; color:white; padding:12px 20px; border-radius:8px;">
                                    🎂 ¡Feliz Cumpleaños!
                                </div>
                            </div>

                            <p style="font-size:14px; color:#555;">
                                Gracias por confiar en nosotros para cuidar lo que más valorás.
                            </p>

                            <p style="margin-top:20px;">
                                Saludos,<br>
                                <strong>Fuerza Natural Broker</strong>
                            </p>
                        </div>
                    </div>
                </div>
                """

                email = EmailMultiAlternatives(
                    subject=f"🎉 ¡Feliz cumpleaños {cliente.first_name}!",
                    body="Feliz cumpleaños",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[cliente.email],
                )

                email.attach_alternative(html_content, "text/html")
                email.send()

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
