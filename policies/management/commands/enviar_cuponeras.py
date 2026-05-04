from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from policies.models import Payment
from alerts.models import Alert


class Command(BaseCommand):
    help = "Envía recordatorios de cuponera 2 días antes del vencimiento"

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        fecha_objetivo = hoy + timedelta(days=2)

        # Buscamos cuotas que vencen exactamente en 2 días y no están pagadas
        pagos = Payment.objects.filter(
            fecha_vencimiento=fecha_objetivo,
            fecha_pago__isnull=True,
            recordatorio_enviado=False,
            policy__forma_pago="CUPONERA",
        ).select_related("policy", "policy__client", "policy__client__producer")

        enviados = 0

        for pago in pagos:
            cliente = pago.policy.client
            if not cliente or not cliente.email:
                continue

            try:
                # Estética Fuerza Natural Broker
                html_content = f"""
                <div style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
                    <div style="max-width:520px; margin:auto; background:white; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb;">
                        <div style="background:#0f172a; padding:24px 20px; text-align:center;">
                            <img src="https://crm.fuerzanaturalbroker.com/static/images/img/logo.png" style="max-width:200px;" />
                        </div>
                        <div style="padding:28px 24px; color:#1f2937;">
                            <h2 style="margin-top:0;">Hola {cliente.first_name} 👋</h2>
                            <p style="font-size:16px; line-height:1.5;">Te recordamos el próximo vencimiento de tu cuota de seguro:</p>
                            <div style="background:#f9fafb; padding:16px; border-left:4px solid #2563eb; margin:20px 0;">
                                <strong>Póliza:</strong> {pago.policy.policy_number}<br>
                                <strong>Cuota:</strong> #{pago.numero_cuota}<br>
                                <strong>Vence el:</strong> {pago.fecha_vencimiento.strftime('%d/%m/%Y')}
                            </div>
                            <p style="font-size:16px; line-height:1.5;">Una vez realizado el pago ante la compañía, envianos el comprobante por este medio para registrarlo.</p>
                            <p style="margin-top:24px; line-height:1.5;">Saludos,<br><strong>Fuerza Natural Broker</strong></p>
                        </div>
                    </div>
                </div>
                """

                email = EmailMultiAlternatives(
                    subject=f"📌 Recordatorio de pago: Cuota #{pago.numero_cuota}",
                    body=f"Hola {cliente.first_name}, vence tu cuota #{pago.numero_cuota} el {pago.fecha_vencimiento}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[cliente.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                # Marcamos como enviado en la base de datos
                pago.recordatorio_enviado = True
                pago.save()
                enviados += 1

            except Exception as e:
                self.stderr.write(f"Error con {cliente.email}: {e}")

        if enviados > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Mails de cuponera enviados: {enviados}")
            )
        else:
            self.stdout.write("No hay cuotas que venzan en 2 días para avisar hoy.")
