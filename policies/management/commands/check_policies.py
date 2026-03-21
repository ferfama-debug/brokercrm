from django.core.management.base import BaseCommand
from policies.models import Policy
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Verifica pólizas próximas a vencer y envía emails"

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        objetivo = hoy + timedelta(days=2)

        # 🔥 SOLO 2 DÍAS ANTES Y NO ENVIADAS
        policies = Policy.objects.filter(
            end_date=objetivo,
            email_vencimiento_enviado=False
        )

        if not policies.exists():
            self.stdout.write("No hay pólizas para enviar hoy")
            return

        for policy in policies:
            self.stdout.write(f"⚠️ Póliza por vencer: {policy}")

            cliente = policy.client

            # 🔴 SI NO TIENE EMAIL → SALTEA
            if not cliente.email:
                self.stdout.write(
                    f"❌ Cliente sin email: {cliente.nombre_completo()}"
                )
                continue

            asunto = f"⚠️ Tu póliza está por vencer ({policy.policy_number})"

            mensaje = f"""
Hola {cliente.first_name},

Tu póliza está por vencer:

📌 Compañía: {policy.company}
📄 Número: {policy.policy_number}
📅 Vencimiento: {policy.end_date}
"""

            if policy.pdf_poliza:
                mensaje += f"\n📎 Ver póliza:\n{policy.pdf_poliza}\n"

            mensaje += "\nPor favor contactanos para renovarla.\n\nFuerza Natural Broker"

            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [cliente.email],
                    fail_silently=False,
                )

                # 🔥 MARCAR COMO ENVIADO
                policy.email_vencimiento_enviado = True
                policy.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"📧 Email enviado a {cliente.email}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error enviando email: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("✔ Chequeo y envío completado"))