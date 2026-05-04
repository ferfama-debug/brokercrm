from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from policies.models import Payment


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
        ).select_related("policy", "policy__client")

        enviados = 0

        for pago in pagos:
            cliente = pago.policy.client
            if not cliente or not cliente.email:
                continue

            # Obtener URL de cuponera si existe
            cuponera_url = (
                pago.policy.cuponera_pdf if pago.policy.cuponera_pdf else None
            )

            # Botón de descarga opcional
            boton_html = ""
            if cuponera_url:
                boton_html = f"""
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{cuponera_url}" 
                       style="background-color: #22c55e; color: #ffffff; padding: 14px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                       📥 Descargar Cuponera de Pago
                    </a>
                </div>
                """

            try:
                # Estética Mejorada Fuerza Natural Broker
                html_content = f"""
                <div style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
                    <div style="max-width:520px; margin:auto; background:white; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb;">
                        <div style="background:#0f172a; padding:30px 20px; text-align:center;">
                            <img src="https://crm.fuerzanaturalbroker.com/static/images/img/logo.png" style="width:160px; height:auto; display:block; margin:auto;" />
                        </div>
                        <div style="padding:28px 24px; color:#1f2937;">
                            <h2 style="margin-top:0; text-align:center;">Hola {cliente.first_name} 👋</h2>
                            <p style="font-size:16px; line-height:1.5; text-align:center;">Te recordamos el próximo vencimiento de tu cuota de seguro:</p>
                            
                            <div style="background:#f9fafb; padding:16px; border-left:4px solid #22c55e; margin:20px 0; font-size:15px;">
                                <strong>Póliza:</strong> {pago.policy.policy_number}<br>
                                <strong>Cuota:</strong> #{pago.numero_cuota}<br>
                                <strong>Vence el:</strong> {pago.fecha_vencimiento.strftime('%d/%m/%Y')}
                            </div>

                            {boton_html}

                            <p style="font-size:15px; line-height:1.5; color:#4b5563;">Una vez realizado el pago ante la compañía, envianos el comprobante por este medio para registrarlo.</p>
                            
                            <hr style="border:0; border-top:1px solid #e5e7eb; margin:25px 0;">
                            
                            <p style="line-height:1.5; font-size:14px; text-align:center; color:#6b7280;">
                                Saludos,<br>
                                <strong>Fuerza Natural Broker de Seguros</strong>
                            </p>
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

                # Marcamos como enviado
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
