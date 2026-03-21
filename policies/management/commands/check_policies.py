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

        self.stdout.write(f"📅 Ejecutando chequeo para fecha objetivo: {objetivo}")

        # 🔥 SOLO 2 DÍAS ANTES Y NO ENVIADAS
        policies = Policy.objects.filter(
            end_date=objetivo,
            email_vencimiento_enviado=False
        ).select_related("client")

        if not policies.exists():
            self.stdout.write("✔ No hay pólizas para enviar hoy")
            return

        self.stdout.write(f"🔎 Se encontraron {policies.count()} pólizas para notificar")

        for policy in policies:
            cliente = policy.client

            self.stdout.write(f"⚠️ Procesando póliza: {policy.policy_number}")

            # 🔴 SIN EMAIL → SALTA
            if not cliente.email:
                self.stdout.write(
                    self.style.WARNING(
                        f"❌ Cliente sin email: {cliente.nombre_completo()}"
                    )
                )
                continue

            asunto = f"⚠️ Tu póliza está por vencer ({policy.policy_number})"

            fecha_vencimiento = policy.end_date.strftime("%d/%m/%Y")

            mensaje = f"""
Hola {cliente.first_name},

Te recordamos que tu póliza está próxima a vencer:

📌 Compañía: {policy.company}
📄 Número: {policy.policy_number}
📅 Vencimiento: {fecha_vencimiento}
"""

            if policy.pdf_poliza:
                mensaje += f"\n📎 Ver póliza:\n{policy.pdf_poliza}\n"

            mensaje += "\nPodés contactarnos para renovarla.\n\nFuerza Natural Broker de Seguros"

            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [cliente.email],
                    fail_silently=False,
                )

                # 🔥 MARCAR COMO ENVIADO (PRO)
                policy.email_vencimiento_enviado = True
                policy.save(update_fields=["email_vencimiento_enviado"])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"📧 Email enviado a {cliente.email}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error enviando email ({policy.policy_number}): {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("✔ Chequeo y envío completado"))