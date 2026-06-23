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

            # 🟢 CORRECCIÓN QUIRÚRGICA: Solo omitimos si YA se generó una alerta HOY para este cumpleaños
            ya_enviado = Alert.objects.filter(
                user=cliente.producer,
                tipo="CUMPLEANIOS",
                message=mensaje,
                created_at__date=hoy,  # 👈 Control estricto del día, ignorando alertas históricas
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
                    <div style="max-width:520px; margin:auto; background:white; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb;">

                        <div style="background:#0f172a; padding:24px 20px; text-align:center;">
                            <img src="https://crm.fuerzanaturalbroker.com/static/images/img/logo.png"
                                 alt="Fuerza Natural Broker"
                                 style="max-width:200px; display:block;margin:0 auto;" />
                        </div>

                        <div style="padding:28px 24px; color:#1f2937;">
                            <h2 style="margin-top:0;">Hola {cliente.first_name} 👋</h2>

                            <p style="font-size:16px; line-height:1.5;">
                                Hoy es un día especial, y desde
                                <strong>Fuerza Natural Broker</strong>
                                queremos saludarte y desearte un muy feliz cumpleaños.
                            </p>

                            <p style="font-size:16px; line-height:1.5;">
                                Esperamos que disfrutes mucho tu día y que este nuevo año venga lleno
                                de buenos momentos, salud y proyectos cumplidos.
                            </p>

                            <div style="text-align:center; margin:30px 0;">
                                <div style="display:inline-block; background:#2563eb; color:white; padding:14px 22px; border-radius:8px; font-weight:bold;">
                                    🎂 ¡Feliz cumpleaños!
                                </div>
                            </div>

                            <p style="font-size:14px; color:#555; line-height:1.5;">
                                Gracias por confiar en nosotros para acompañarte en la protección
                                de lo que más valorás.
                            </p>

                            <p style="margin-top:24px; line-height:1.5;">
                                Saludos,<br>
                                <strong>Fuerza Natural Broker</strong>
                            </p>
                        </div>
                    </div>
                </div>
                """

                text_content = (
                    f"Hola {cliente.first_name},\n\n"
                    "Desde Fuerza Natural Broker queremos saludarte y desearte "
                    "un muy feliz cumpleaños.\n\n"
                    "Esperamos que disfrutes mucho tu día y que este nuevo año "
                    "venga lleno de buenos momentos, salud y proyectos cumplidos.\n\n"
                    "Gracias por confiar en nosotros.\n\n"
                    "Saludos,\n"
                    "Fuerza Natural Broker"
                )

                # 🟢 COPIA OCULTA (BCC): Agregamos tu mail para que te llegue el respaldo exacto
                email = EmailMultiAlternatives(
                    subject=f"🎉 ¡Feliz cumpleaños {cliente.first_name}!",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[cliente.email],
                    bcc=["fuerzanaturalbroker@gmail.com"],  # 👈 Te cae una copia oculta a vos
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
                f"Cumpleaños processed. Enviados: {enviados}. "
                f"Omitidos: {omitidos}. Errores: {errores}."
            )
        )