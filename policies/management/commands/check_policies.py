from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from policies.models import Policy, Payment, EmailLog


class Command(BaseCommand):
    help = (
        "Verifica pólizas (a 15 y 2 días) y pagos próximos a vencer y envía emails respetando la"
        " configuración del productor (Verde: cliente + copia, Rojo: solo modo pruebas al broker)"
    )

    def handle(self, *args, **kwargs):
        hoy = timezone.localdate()
        fecha_15 = hoy + timedelta(days=15)
        fecha_2 = hoy + timedelta(days=2)
        fechas_objetivo = [fecha_2, fecha_15]

        self.stdout.write(f"Ejecutando chequeo para fechas objetivo: {fechas_objetivo}")

        enviados = 0
        omitidos = 0
        errores = 0

        # ==========================================================
        # 1. POLIZAS / AVISO PREVIO A 15 DÍAS
        # ==========================================================
        policies_15 = (
            Policy.objects.filter(
                end_date=fecha_15,
                email_15_dias_enviado=False,
            )
            .select_related("client", "client__producer")
            .order_by("end_date")
        )

        if policies_15.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se encontraron {policies_15.count()} pólizas para notificar a 15 días"
                )
            )

            for policy in policies_15:
                cliente = policy.client

                self.stdout.write(f"Procesando póliza (15 días): {policy.policy_number}")

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

                # 🟢 VERIFICACIÓN DEL INTERRUPTOR DEL PRODUCTOR
                productor = cliente.producer
                enviar_a_cliente = True
                if productor and not getattr(productor, "enviar_emails_a_clientes", True):
                    enviar_a_cliente = False
                    self.stdout.write(
                        self.style.WARNING(
                            f"Modo pruebas activado (Rojo) para el productor {productor}. "
                            f"El correo de aviso a 15 días de la póliza {policy.policy_number} se enviará solo de forma interna."
                        )
                    )

                fecha_vencimiento = policy.end_date.strftime("%d/%m/%Y")
                dias_restantes = (policy.end_date - hoy).days

                asunto = f"Aviso de Vencimiento Próximo: Póliza {policy.policy_number}"

                mensaje = (
                    f"Hola {cliente.first_name},\n\n"
                    "Te informamos que tu póliza se encuentra próxima a vencer en 15 días.\n\n"
                    f"Compañía: {policy.company or 'No informada'}\n"
                    f"Número: {policy.policy_number}\n"
                    f"Vencimiento: {fecha_vencimiento}\n"
                    f"Días restantes: {dias_restantes}\n"
                )

                if policy.pdf_poliza:
                    mensaje += f"\nVer póliza:\n{policy.pdf_poliza}\n"

                mensaje += (
                    "\nPodés contactarnos con anticipación para gestionar su renovación.\n\n"
                    "Fuerza Natural Broker de Seguros"
                )

                try:
                    html_content = render_to_string(
                        "emails/recordatorio_poliza.html",
                        {
                            "cliente": cliente,
                            "policy": policy,
                            "fecha_vencimiento": fecha_vencimiento,
                            "dias_restantes": dias_restantes,
                        },
                    )

                    # 🟢 CONFIGURACIÓN DE DESTINATARIOS SEGÚN EL INTERRUPTOR
                    if enviar_a_cliente:
                        destinatario_final = cliente.email
                        emails_to = [cliente.email]
                        emails_bcc = ["fuerzanaturalbroker@gmail.com"]
                        tipo_log_estado = "ENVIADO"
                    else:
                        destinatario_final = "fuerzanaturalbroker@gmail.com"
                        emails_to = ["fuerzanaturalbroker@gmail.com"]
                        emails_bcc = []
                        tipo_log_estado = "ENVIADO_PRUEBA_ROJO"

                    email = EmailMultiAlternatives(
                        subject=asunto,
                        body=mensaje,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=emails_to,
                        bcc=emails_bcc,
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                    EmailLog.objects.create(
                        policy=policy,
                        client=cliente,
                        tipo="AVISO_15_DIAS",
                        estado=tipo_log_estado,
                        destinatario=destinatario_final,
                        asunto=asunto,
                    )

                    policy.email_15_dias_enviado = True
                    policy.save()

                    if enviar_a_cliente:
                        self.stdout.write(
                            self.style.SUCCESS(f"Email de aviso a 15 días enviado a {cliente.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"Email de prueba a 15 días enviado al broker (Modo Rojo)")
                        )
                    enviados += 1

                except Exception as e:
                    EmailLog.objects.create(
                        policy=policy,
                        client=cliente,
                        tipo="AVISO_15_DIAS",
                        estado="ERROR",
                        destinatario=cliente.email if cliente else None,
                        asunto=asunto if "asunto" in locals() else "",
                        error=str(e),
                    )

                    self.stdout.write(
                        self.style.ERROR(
                            f"Error enviando email a 15 días de póliza {policy.policy_number}: {str(e)}"
                        )
                    )
                    errores += 1

        # ==========================================================
        # 2. POLIZAS / VENCIMIENTO A 2 DÍAS
        # ==========================================================
        policies_2 = (
            Policy.objects.filter(
                end_date=fecha_2,
                email_vencimiento_enviado=False,
            )
            .select_related("client", "client__producer")
            .order_by("end_date")
        )

        if policies_2.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se encontraron {policies_2.count()} pólizas para notificar a 2 días"
                )
            )

            for policy in policies_2:
                cliente = policy.client

                self.stdout.write(f"Procesando póliza (2 días): {policy.policy_number}")

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

                # 🟢 VERIFICACIÓN DEL INTERRUPTOR DEL PRODUCTOR
                productor = cliente.producer
                enviar_a_cliente = True
                if productor and not getattr(productor, "enviar_emails_a_clientes", True):
                    enviar_a_cliente = False
                    self.stdout.write(
                        self.style.WARNING(
                            f"Modo pruebas activado (Rojo) para el productor {productor}. "
                            f"El correo de la póliza {policy.policy_number} se enviará solo de forma interna."
                        )
                    )

                fecha_vencimiento = policy.end_date.strftime("%d/%m/%Y")
                dias_restantes = (policy.end_date - hoy).days

                asunto = f"Tu póliza está por vencer ({policy.policy_number})"

                mensaje = (
                    f"Hola {cliente.first_name},\n\n"
                    "Te recordamos que tu póliza está próxima a vencer.\n\n"
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
                    html_content = render_to_string(
                        "emails/recordatorio_poliza.html",
                        {
                            "cliente": cliente,
                            "policy": policy,
                            "fecha_vencimiento": fecha_vencimiento,
                            "dias_restantes": dias_restantes,
                        },
                    )

                    # 🟢 CONFIGURACIÓN DE DESTINATARIOS SEGÚN EL INTERRUPTOR
                    if enviar_a_cliente:
                        destinatario_final = cliente.email
                        emails_to = [cliente.email]
                        emails_bcc = ["fuerzanaturalbroker@gmail.com"]
                        tipo_log_estado = "ENVIADO"
                    else:
                        destinatario_final = "fuerzanaturalbroker@gmail.com"
                        emails_to = ["fuerzanaturalbroker@gmail.com"]
                        emails_bcc = []
                        tipo_log_estado = "ENVIADO_PRUEBA_ROJO"

                    email = EmailMultiAlternatives(
                        subject=asunto,
                        body=mensaje,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=emails_to,
                        bcc=emails_bcc,
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                    EmailLog.objects.create(
                        policy=policy,
                        client=cliente,
                        tipo="VENCIMIENTO_POLIZA",
                        estado=tipo_log_estado,
                        destinatario=destinatario_final,
                        asunto=asunto,
                    )

                    policy.email_vencimiento_enviado = True
                    policy.save()

                    if enviar_a_cliente:
                        self.stdout.write(
                            self.style.SUCCESS(f"Email de póliza enviado a {cliente.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"Email de prueba de póliza enviado al broker (Modo Rojo)")
                        )
                    enviados += 1

                except Exception as e:
                    EmailLog.objects.create(
                        policy=policy,
                        client=cliente,
                        tipo="VENCIMIENTO_POLIZA",
                        estado="ERROR",
                        destinatario=cliente.email if cliente else None,
                        asunto=asunto if "asunto" in locals() else "",
                        error=str(e),
                    )

                    self.stdout.write(
                        self.style.ERROR(
                            f"Error enviando email de póliza {policy.policy_number}: {str(e)}"
                        )
                    )
                    errores += 1

        # ==========================================================
        # 3. PAGOS / CUPONERA
        # ==========================================================
        pagos = (
            Payment.objects.filter(
                fecha_vencimiento=fecha_2,
                recordatorio_enviado=False,
                fecha_pago__isnull=True,
                policy__forma_pago="CUPONERA",
            )
            .select_related("policy", "policy__client", "policy__client__producer")
            .order_by("fecha_vencimiento", "policy__policy_number", "numero_cuota")
        )

        if pagos.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se encontraron {pagos.count()} pagos de cuponera para notificar"
                )
            )

            for pago in pagos:
                policy = pago.policy
                cliente = policy.client if policy else None

                self.stdout.write(
                    f"Procesando cuota {pago.numero_cuota} de póliza "
                    f"{policy.policy_number if policy else 'sin póliza'}"
                )

                if not policy or not cliente:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Pago sin póliza o cliente asociado: cuota #{pago.numero_cuota}"
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

                # 🟢 VERIFICACIÓN DEL INTERRUPTOR PARA PAGOS
                productor = cliente.producer
                enviar_a_cliente = True
                if productor and not getattr(productor, "enviar_emails_a_clientes", True):
                    enviar_a_cliente = False
                    self.stdout.write(
                        self.style.WARNING(
                            f"Modo pruebas activado (Rojo) para el productor {productor}. "
                            f"El correo de cuota #{pago.numero_cuota} se enviará solo de forma interna."
                        )
                    )

                fecha_vencimiento = pago.fecha_vencimiento.strftime("%d/%m/%Y")
                dias_restantes = (pago.fecha_vencimiento - hoy).days

                asunto = (
                    f"Recordatorio de pago de cuponera "
                    f"({policy.policy_number} - cuota {pago.numero_cuota})"
                )

                mensaje = (
                    f"Hola {cliente.first_name},\n\n"
                    "Te recordamos que tenés un próximo vencimiento de cuponera.\n\n"
                    f"Póliza: {policy.policy_number}\n"
                    f"Compañía: {policy.company or 'No informada'}\n"
                    f"Cuota: {pago.numero_cuota}\n"
                    f"Vencimiento: {fecha_vencimiento}\n"
                    f"Días restantes: {dias_restantes}\n"
                )

                if pago.monto:
                    mensaje += f"Monto: ${pago.monto}\n"

                if policy.cuponera_pdf:
                    mensaje += f"\nVer cuponera:\n{policy.cuponera_pdf}\n"

                mensaje += (
                    "\nTe recomendamos realizar el pago antes de la fecha indicada.\n"
                    "Si ya abonaste, podés ignorar este mensaje.\n\n"
                    "Fuerza Natural Broker de Seguros"
                )

                try:
                    html_content = render_to_string(
                        "emails/recordatorio_cuponera.html",
                        {
                            "cliente": cliente,
                            "policy": policy,
                            "pago": pago,
                            "fecha_vencimiento": fecha_vencimiento,
                            "dias_restantes": dias_restantes,
                        },
                    )

                    # 🟢 CONFIGURACIÓN DE DESTINATARIOS SEGÚN EL INTERRUPTOR
                    if enviar_a_cliente:
                        destinatario_final = cliente.email
                        emails_to = [cliente.email]
                        emails_bcc = ["fuerzanaturalbroker@gmail.com"]
                        tipo_log_estado = "ENVIADO"
                    else:
                        destinatario_final = "fuerzanaturalbroker@gmail.com"
                        emails_to = ["fuerzanaturalbroker@gmail.com"]
                        emails_bcc = []
                        tipo_log_estado = "ENVIADO_PRUEBA_ROJO"

                    email = EmailMultiAlternatives(
                        subject=asunto,
                        body=mensaje,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=emails_to,
                        bcc=emails_bcc,
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                    EmailLog.objects.create(
                        policy=policy,
                        payment=pago,
                        client=cliente,
                        tipo="VENCIMIENTO_CUPONERA",
                        estado=tipo_log_estado,
                        destinatario=destinatario_final,
                        asunto=asunto,
                    )

                    pago.recordatorio_enviado = True
                    pago.save()

                    if enviar_a_cliente:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Email de cuponera enviado a {cliente.email}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Email de prueba de cuponera enviado al broker (Modo Rojo)"
                            )
                        )
                    enviados += 1

                except Exception as e:
                    EmailLog.objects.create(
                        policy=policy,
                        payment=pago,
                        client=cliente,
                        tipo="VENCIMIENTO_CUPONERA",
                        estado="ERROR",
                        destinatario=cliente.email if cliente else None,
                        asunto=asunto if "asunto" in locals() else "",
                        error=str(e),
                    )

                    self.stdout.write(
                        self.style.ERROR(
                            f"Error enviando email de cuponera "
                            f"{policy.policy_number} cuota {pago.numero_cuota}: {str(e)}"
                        )
                    )
                    errores += 1
        else:
            self.stdout.write(
                self.style.WARNING("No hay pagos de cuponera para enviar hoy")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Chequeo completado. Enviados: {enviados}, Omitidos:"
                f" {omitidos}, Errores: {errores}"
            )
        )
