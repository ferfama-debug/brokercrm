from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from policies.models import Policy


class Command(BaseCommand):
    help = "Verifica pólizas próximas a vencer y envía emails"

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        fechas_objetivo = [hoy + timedelta(days=1), hoy + timedelta(days=2)]

        self.stdout.write(
            f"Ejecutando chequeo para fechas objetivo: {fechas_objetivo[0]} y {fechas_objetivo[1]}"
        )

        policies = (
            Policy.objects.filter(
                end_date__in=fechas_objetivo,
                email_vencimiento_enviado=False,
            )
            .select_related("client")
            .order_by("end_date")
        )

        if not policies.exists():
            self.stdout.write(self.style.WARNING("No hay pólizas para enviar hoy"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Se encontraron {policies.count()} pólizas para notificar"
            )
        )

        enviados = 0
        omitidos = 0
        errores = 0

        for policy in policies:
            cliente = policy.client

            self.stdout.write(f"Procesando póliza: {policy.policy_number}")

            if not cliente:
                self.stdout.write(
                    self.style.WARNING(
                        f"Póliza sin cliente asociado: {policy.policy_number}"
                    )
                )
                omitidos += 1
                continue

            if not cliente.email:
                self.stdout.write(
                    self.style.WARNING(
                        f"Cliente sin email: {cliente.nombre_completo()}"
                    )
                )
                omitidos += 1
                continue

            fecha_vencimiento = policy.end_date.strftime("%d/%m/%Y")
            dias_restantes = (policy.end_date - hoy).days

            asunto = f"Tu póliza está por vencer ({policy.policy_number})"

            mensaje = (
                f"Hola {cliente.first_name},\n\n"
                f"Te recordamos que tu póliza está próxima a vencer.\n\n"
                f"Compañía: {policy.company or 'No informada'}\n"
                f"Número: {policy.policy_number}\n"
                f"Vencimiento: {fecha_vencimiento}\n"
                f"Días restantes: {dias_restantes}\n"
            )

            if policy.pdf_poliza:
                mensaje += f"\nVer póliza:\n{policy.pdf_poliza}\n"

            mensaje += (
                "\nPodés contactarnos para renovarla.\n\n"
                "Fuerza Natural Broker de Seguros"
            )

            try:
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cliente.email],
                    fail_silently=False,
                )

                policy.email_vencimiento_enviado = True
                policy.save(update_fields=["email_vencimiento_enviado"])

                self.stdout.write(
                    self.style.SUCCESS(f"Email enviado a {cliente.email}")
                )
                enviados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error enviando email de póliza {policy.policy_number}: {str(e)}"
                    )
                )
                errores += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Chequeo completado. Enviados: {enviados}, Omitidos: {omitidos}, Errores: {errores}"
            )
        )
