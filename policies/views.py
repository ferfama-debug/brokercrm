from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Policy, Payment, Company, RiskType
from clients.models import Client
from datetime import date, timedelta
import os
import requests
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from django.contrib import messages

print("🔥 Integración Supabase inicializada")


def get_subir_archivo():
    try:
        from core.supabase_client import subir_archivo_supabase

        print("✅ Supabase client cargado correctamente")
        return subir_archivo_supabase
    except Exception as e:
        print("⚠️ Supabase no disponible:", e)
        return None


def procesar_archivo(file, carpeta):
    if not file:
        print(f"⚠️ No se recibió archivo para carpeta: {carpeta}")
        return None

    print(
        f"📂 Procesando archivo | carpeta={carpeta} | nombre={file.name} | size={getattr(file, 'size', 'N/A')}"
    )

    subir_archivo = get_subir_archivo()

    try:
        if subir_archivo:
            resultado = subir_archivo(file, carpeta)
            print(f"✅ Resultado subida ({carpeta}):", resultado)
            return resultado

        print(f"⚠️ No hay función de subida disponible para {carpeta}")
        return None
    except Exception as e:
        print(f"❌ Error subiendo archivo ({carpeta}):", e)
        return None


def descargar_adjunto_desde_url(url, nombre_archivo):
    if not url:
        return None

    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "application/pdf")
            return {
                "filename": nombre_archivo,
                "content": response.content,
                "mimetype": content_type,
            }

        print(
            f"⚠️ No se pudo descargar adjunto {nombre_archivo}: {response.status_code}"
        )
        return None
    except Exception as e:
        print(f"⚠️ Error descargando adjunto {nombre_archivo}: {e}")
        return None


def enviar_email_con_fallback(
    asunto,
    mensaje_texto,
    destinatarios,
    mensaje_html=None,
    adjuntos=None,
):
    remitente = (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "EMAIL_HOST_USER", None)
        or "onboarding@resend.dev"
    )

    adjuntos = adjuntos or []

    # 🟢 PROTOCOLO: COPIA OCULTA AUTOMÁTICA PARA LA EMPRESA 🟢
    copia_empresa = ["fuerzanaturalbroker@gmail.com"]

    # 1) Intento con SMTP configurado en Django
    try:
        email = EmailMultiAlternatives(
            subject=asunto,
            body=mensaje_texto,
            from_email=remitente,
            to=destinatarios,
            bcc=copia_empresa,  # Inyección de copia oculta quirúrgica
        )

        if mensaje_html:
            email.attach_alternative(mensaje_html, "text/html")

        for adjunto in adjuntos:
            if adjunto and adjunto.get("content"):
                email.attach(
                    adjunto["filename"],
                    adjunto["content"],
                    adjunto.get("mimetype", "application/pdf"),
                )

        enviados = email.send(fail_silently=False)

        if enviados == 1:
            print("✅ EMAIL enviado por SMTP con copia oculta a Fuerza Natural")
            return True, "smtp"
    except Exception as smtp_error:
        print("ERROR EMAIL SMTP:", smtp_error)

        # 2) Fallback a Resend API
        resend_api_key = getattr(settings, "RESEND_API_KEY", None)
        if not resend_api_key:
            return (
                False,
                f"SMTP falló y RESEND_API_KEY no está configurada: {smtp_error}",
            )

        try:
            payload = {
                "from": remitente,
                "to": destinatarios,
                "bcc": copia_empresa,  # Inyección de copia oculta en contingencia de Resend
                "subject": asunto,
                "text": mensaje_texto,
            }

            if mensaje_html:
                payload["html"] = mensaje_html

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )

            if response.status_code in (200, 201):
                print("✅ EMAIL enviado por Resend con copia oculta a Fuerza Natural")
                return True, "resend"

            print("ERROR EMAIL RESEND:", response.status_code, response.text)
            return (
                False,
                f"SMTP falló ({smtp_error}) y Resend devolvió {response.status_code}: {response.text}",
            )

        except Exception as resend_error:
            print("ERROR EMAIL RESEND EXCEPTION:", resend_error)
            return (
                False,
                f"SMTP falló ({smtp_error}) y Resend también falló ({resend_error})",
            )

    return False, "El servidor no confirmó el envío"


def formatear_fecha(valor):
    if not valor:
        return ""
    try:
        return valor.strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def construir_email_poliza(cliente, poliza):
    fecha_inicio = formatear_fecha(poliza.start_date)
    fecha_fin = formatear_fecha(poliza.end_date)
    aseguradora = poliza.company or "tu compañía"
    nombre_cliente = cliente.first_name or "cliente"

    asunto = f"Póliza disponible - {aseguradora}"

    mensaje_texto = f"""Hola {nombre_cliente} 👋

Te escribimos desde Fuerza Natural Broker de Seguros.

Te enviamos tu póliza de {aseguradora}.

📅 Vigencia: {fecha_inicio} al {fecha_fin}

📄 Documentación:
"""

    if poliza.pdf_poliza:
        mensaje_texto += f"\n• Póliza: {poliza.pdf_poliza}\n"

    if poliza.cuponera_pdf:
        mensaje_texto += f"• Cuponera de pago: {poliza.cuponera_pdf}\n"

    mensaje_texto += """

Cuando realices el pago, podés enviarnos el comprobante por este medio para registrarlo con la compañía y mantener tu cobertura al día.

Ante cualquier duda, estamos para ayudarte.

Fuerza Natural Broker
"""

    boton_poliza_html = ""
    if poliza.pdf_poliza:
        boton_poliza_html = f"""
                <tr>
                  <td style="padding-bottom:12px;">
                    <a href="{poliza.pdf_poliza}" style="display:inline-block; background:#0f172a; color:#ffffff; text-decoration:none; font-size:15px; font-weight:700; padding:14px 22px; border-radius:10px;">
                      📄 Descargar póliza
                    </a>
                  </td>
                </tr>
        """

    boton_cuponera_html = ""
    texto_cuponera_html = ""
    if poliza.cuponera_pdf:
        boton_cuponera_html = f"""
                <tr>
                  <td>
                    <a href="{poliza.cuponera_pdf}" style="display:inline-block; background:#2563eb; color:#ffffff; text-decoration:none; font-size:15px; font-weight:700; padding:14px 22px; border-radius:10px;">
                      💳 Descargar cuponera de pago
                    </a>
                  </td>
                </tr>
        """
        texto_cuponera_html = """
              <p style="margin:0 0 18px; font-size:15px; line-height:1.7; color:#374151;">
                Cuando realices el pago, podés enviarnos el comprobante por este medio para registrarlo con la compañía y mantener tu cobertura al día.
              </p>
        """

    mensaje_html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Póliza disponible</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f6f8; margin:0; padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:640px; background:#ffffff; border-radius:14px; overflow:hidden; border:1px solid #e5e7eb;">
          
          <tr>
            <td style="background:#0f172a; padding:28px 32px; text-align:center;">
              <div style="color:#ffffff; font-size:24px; font-weight:700; letter-spacing:0.3px;">
                Fuerza Natural Broker
              </div>
              <div style="color:#cbd5e1; font-size:14px; margin-top:6px;">
                Broker de Seguros
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 18px; font-size:16px; line-height:1.6;">
                Hola <strong>{nombre_cliente}</strong> 👋
              </p>

              <p style="margin:0 0 18px; font-size:16px; line-height:1.6;">
                Te escribimos desde <strong>Fuerza Natural Broker de Seguros</strong>.
              </p>

              <p style="margin:0 0 24px; font-size:16px; line-height:1.6;">
                Te enviamos tu póliza de <strong>{aseguradora}</strong>.
              </p>

              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 24px; background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px;">
                <tr>
                  <td style="padding:18px 20px;">
                    <div style="font-size:13px; color:#64748b; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:8px;">
                      Vigencia
                    </div>
                    <div style="font-size:18px; font-weight:700; color:#111827;">
                      {fecha_inicio} al {fecha_fin}
                    </div>
                  </td>
                </tr>
              </table>

              <div style="font-size:16px; font-weight:700; color:#111827; margin:0 0 14px;">
                Documentación
              </div>

              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:28px;">
                {boton_poliza_html}
                {boton_cuponera_html}
              </table>

              {texto_cuponera_html}

              <p style="margin:0; font-size:15px; line-height:1.7; color:#374151;">
                Ante cualquier duda, estamos para ayudarte.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 32px; background:#f8fafc; border-top:1px solid #e5e7eb;">
              <div style="font-size:15px; font-weight:700; color:#111827; margin-bottom:6px;">
                Fuerza Natural Broker
              </div>
              <div style="font-size:13px; color:#6b7280; line-height:1.6;">
                Este correo fue enviado desde tu gestión comercial.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    return asunto, mensaje_texto, mensaje_html


@login_required
def panel_cobranzas(request):
    hoy = date.today()
    en_3_dias = hoy + timedelta(days=3)

    if request.user.is_superuser:
        pagos = Payment.objects.select_related("policy", "policy__client")
    else:
        pagos = Payment.objects.filter(
            policy__client__producer=request.user
        ).select_related("policy", "policy__client")

    vencidos = pagos.filter(fecha_vencimiento__lt=hoy, fecha_pago__isnull=True).exclude(
        estado="ANULADO"
    )
    hoy_vencen = pagos.filter(fecha_vencimiento=hoy, fecha_pago__isnull=True).exclude(
        estado="ANULADO"
    )
    proximos = pagos.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=en_3_dias,
        fecha_pago__isnull=True,
    ).exclude(estado="ANULADO")

    return render(
        request,
        "policies/panel_cobranzas.html",
        {
            "vencidos": vencidos,
            "hoy": hoy_vencen,
            "proximos": proximos,
        },
    )


@login_required
def lista_polizas(request):
    """
    CIRUGÍA QUIRÚRGICA: Buscador inteligente potenciado.
    Ahora busca por Nombre, Apellido, N° Póliza, DNI y Patente.
    """
    compania = request.GET.get("compania")
    buscar = request.GET.get("buscar")

    if request.user.is_superuser:
        clientes = Client.objects.prefetch_related("policy_set")
    else:
        clientes = Client.objects.filter(producer=request.user).prefetch_related(
            "policy_set"
        )

    if buscar:
        # Buscador Multicampo (DNI y Patente incluidos)
        clientes = clientes.filter(
            Q(first_name__icontains=buscar)
            | Q(last_name__icontains=buscar)
            | Q(dni__icontains=buscar)  # Búsqueda por DNI
            | Q(policy__policy_number__icontains=buscar)
            | Q(policy__patente__icontains=buscar)  # Búsqueda por Patente
        ).distinct()

    if compania:
        clientes = clientes.filter(policy__company=compania).distinct()

    # --- CORRECCIÓN: Lista de compañías única y ordenada ---
    if request.user.is_superuser:
        companias = (
            Policy.objects.exclude(company__isnull=True)
            .exclude(company="")
            .values_list("company", flat=True)
            .distinct()
            .order_by("company")
        )
    else:
        companias = (
            Policy.objects.filter(client__producer=request.user)
            .exclude(company__isnull=True)
            .exclude(company="")
            .values_list("company", flat=True)
            .distinct()
            .order_by("company")
        )

    return render(
        request,
        "policies/lista_polizas.html",
        {
            "clientes": clientes,
            "companias": companias,
            "compania_seleccionada": compania,
            "buscar": buscar,
        },
    )


@login_required
def crear_poliza(request):
    if request.user.is_superuser:
        clientes = Client.objects.all()
    else:
        clientes = Client.objects.filter(producer=request.user)

    clientes = clientes.order_by("last_name", "first_name")

    cliente_id = request.GET.get("cliente")
    companias = Company.objects.all().order_by("nombre")
    riesgos = RiskType.objects.all().order_by("nombre")

    if request.method == "POST":
        if request.user.is_superuser:
            client = get_object_or_404(Client, id=request.POST.get("client"))
        else:
            client = get_object_or_404(
                Client, id=request.POST.get("client"), producer=request.user
            )

        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            return render(
                request,
                "policies/crear_poliza.html",
                {
                    "clientes": clientes,
                    "cliente_id": cliente_id,
                    "companias": companias,
                    "riesgos": riesgos,
                    "error": "Debe completar las fechas",
                },
            )

        print("===== DEBUG SUBIDA POLIZA (CREAR) =====")
        archivo_poliza = request.FILES.get("pdf_poliza")
        archivo_cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = procesar_archivo(archivo_poliza, "polizas_clientes")
        cuponera_url = procesar_archivo(archivo_cuponera, "cuponeras_clientes")

        company_id = request.POST.get("company")
        company_obj = None
        company_nombre = None

        if company_id:
            try:
                company_obj = Company.objects.get(id=company_id)
                company_nombre = company_obj.nombre
            except Exception:
                company_nombre = request.POST.get("company")

        risk_type_id = request.POST.get("risk_type")
        risk_type_obj = None
        if risk_type_id:
            try:
                risk_type_obj = RiskType.objects.get(id=risk_type_id)
            except Exception:
                pass

        frecuencia_val = request.POST.get("frecuencia_cuponera")
        frecuencia_int = int(frecuencia_val) if frecuencia_val else 1

        nueva_poliza = Policy(
            client=client,
            company=company_nombre,
            company_obj=company_obj,
            policy_number=request.POST.get("policy_number"),
            patente=request.POST.get("patente"),
            risk_type=risk_type_obj,
            tipo_poliza=request.POST.get("tipo_poliza"),
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=frecuencia_int,
            fecha_primer_vencimiento_cuponera=request.POST.get(
                "fecha_primer_vencimiento_cuponera"
            )
            or None,
            pdf_poliza=pdf_url or None,
            cuponera_pdf=cuponera_url or None,
        )

        nueva_poliza.save()

        # 🟢 Tanda de cuotas basada estrictamente en la Frecuencia 🟢
        if nueva_poliza.forma_pago == "CUPONERA":
            base_date = (
                nueva_poliza.fecha_primer_vencimiento_cuponera
                or nueva_poliza.start_date
            )

            if isinstance(base_date, str):
                base_date = date.fromisoformat(base_date)

            n_cuotas_a_generar = frecuencia_int

            for i in range(n_cuotas_a_generar):
                fecha_vencimiento_calculada = base_date + relativedelta(months=i)
                n_cuota = i + 1

                if not Payment.objects.filter(
                    policy=nueva_poliza, numero_cuota=n_cuota
                ).exists():
                    Payment.objects.create(
                        policy=nueva_poliza,
                        numero_cuota=n_cuota,
                        fecha_vencimiento=fecha_vencimiento_calculada,
                        estado="PENDIENTE",
                    )

        messages.success(request, "✅ Póliza creada correctamente")
        return redirect(f"/clientes/ver/{client.id}/")

    return render(
        request,
        "policies/crear_poliza.html",
        {
            "clientes": clientes,
            "cliente_id": cliente_id,
            "companias": companias,
            "riesgos": riesgos,
        },
    )


@login_required
def renovar_poliza(request, poliza_id):
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(Policy, id=poliza_id, client__producer=request.user)

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            return render(
                request,
                "policies/renovar_poliza.html",
                {
                    "poliza": poliza,
                    "error": "Debe completar las fechas",
                },
            )

        print("===== DEBUG SUBIDA POLIZA (RENOVAR) =====")
        archivo_poliza = request.FILES.get("pdf_poliza")
        archivo_cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = procesar_archivo(archivo_poliza, "polizas_clientes")
        cuponera_url = procesar_archivo(archivo_cuponera, "cuponeras_clientes")

        frecuencia_val = request.POST.get("frecuencia_cuponera")
        frecuencia_int = int(frecuencia_val) if frecuencia_val else 1

        nueva_poliza = Policy(
            client=poliza.client,
            company=poliza.company,
            company_obj=poliza.company_obj,
            policy_number=request.POST.get("policy_number"),
            patente=request.POST.get("patente") or poliza.patente,
            risk_type=poliza.risk_type,
            tipo_poliza=poliza.tipo_poliza,
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=frecuencia_int,
            fecha_primer_vencimiento_cuponera=request.POST.get(
                "fecha_primer_vencimiento_cuponera"
            )
            or None,
            pdf_poliza=pdf_url or poliza.pdf_poliza,
            cuponera_pdf=cuponera_url or poliza.cuponera_pdf,
        )

        nueva_poliza.save()

        # 🟢 Tanda de cuotas basada estrictamente en la Frecuencia (Renovación) 🟢
        if nueva_poliza.forma_pago == "CUPONERA":
            base_date = (
                nueva_poliza.fecha_primer_vencimiento_cuponera
                or nueva_poliza.start_date
            )

            if isinstance(base_date, str):
                base_date = date.fromisoformat(base_date)

            n_cuotas_a_generar = frecuencia_int

            for i in range(n_cuotas_a_generar):
                fecha_vencimiento_calculada = base_date + relativedelta(months=i)
                n_cuota = i + 1

                if not Payment.objects.filter(
                    policy=nueva_poliza, numero_cuota=n_cuota
                ).exists():
                    Payment.objects.create(
                        policy=nueva_poliza,
                        numero_cuota=n_cuota,
                        fecha_vencimiento=fecha_vencimiento_calculada,
                        estado="PENDIENTE",
                    )

        messages.success(request, "🔄 Póliza renovada correctamente")
        return redirect(f"/clientes/ver/{poliza.client.id}/")

    return render(
        request,
        "policies/renovar_poliza.html",
        {
            "poliza": poliza,
        },
    )


@login_required
def marcar_pago(request, pago_id):
    if request.user.is_superuser:
        pago = get_object_or_404(Payment, id=pago_id)
    else:
        pago = get_object_or_404(
            Payment, id=pago_id, policy__client__producer=request.user
        )

    if request.method == "POST":
        print("===== DEBUG SUBIDA COMPROBANTE =====")
        archivo_comprobante = request.FILES.get("comprobante")
        comprobante_url = procesar_archivo(archivo_comprobante, "comprobantes_pagos")

        if archivo_comprobante and not comprobante_url:
            messages.error(request, "❌ El comprobante no se pudo subir")
            return render(
                request,
                "policies/cargar_comprobante.html",
                {
                    "pago": pago,
                },
            )

        if comprobante_url:
            pago.comprobante = comprobante_url

        pago.estado = "PAGADO"
        pago.fecha_pago = date.today()
        pago.recordatorio_enviado = True
        pago.save()

        messages.success(request, "📎 Comprobante cargado y pago registrado")
        return redirect(f"/clientes/ver/{pago.policy.client.id}/")

    return render(
        request,
        "policies/cargar_comprobante.html",
        {
            "pago": pago,
        },
    )


@login_required
def enviar_poliza(request, poliza_id):
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(Policy, id=poliza_id, client__producer=request.user)

    cliente = poliza.client

    if not cliente.email:
        messages.error(request, "❌ El cliente no tiene email cargado")
        return redirect(f"/clientes/ver/{cliente.id}/")

    asunto, mensaje_texto, mensaje_html = construir_email_poliza(cliente, poliza)

    adjuntos = []

    if poliza.pdf_poliza:
        adjunto_poliza = descargar_adjunto_desde_url(
            poliza.pdf_poliza,
            f"poliza_{poliza.policy_number or poliza.id}.pdf",
        )
        if adjunto_poliza:
            adjuntos.append(adjunto_poliza)

    if poliza.cuponera_pdf:
        adjunto_cuponera = descargar_adjunto_desde_url(
            poliza.cuponera_pdf,
            f"cuponera_{poliza.policy_number or poliza.id}.pdf",
        )
        if adjunto_cuponera:
            adjuntos.append(adjunto_cuponera)

    ok, proveedor = enviar_email_con_fallback(
        asunto=asunto,
        mensaje_texto=mensaje_texto,
        mensaje_html=mensaje_html,
        destinatarios=[cliente.email],
        adjuntos=adjuntos,
    )

    if ok:
        messages.success(request, f"✅ Email enviado a {cliente.email}")
    else:
        messages.error(request, f"❌ Error al enviar el email: {proveedor}")

    return redirect("/")


@login_required
def detalle_poliza(request, poliza_id):
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(Policy, id=poliza_id, client__producer=request.user)

    return render(
        request,
        "policies/detalle_poliza.html",
        {
            "poliza": poliza,
        },
    )


@login_required
def anular_poliza(request, poliza_id):
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(Policy, id=poliza_id, client__producer=request.user)

    if request.method == "POST":
        motivo = request.POST.get("motivo_anulacion", "Sin motivo especificado")

        poliza.anulada = True
        poliza.fecha_anulacion = date.today()
        poliza.motivo_anulacion = motivo
        poliza.save()

        pagos_pendientes = poliza.pagos.filter(fecha_pago__isnull=True)
        for pago in pagos_pendientes:
            pago.estado = "ANULADO"
            pago.save()

        messages.warning(
            request,
            f"⚠️ La póliza {poliza.policy_number} ha sido anulada y sus cobros cancelados.",
        )
        return redirect(f"/clientes/ver/{poliza.client.id}/")

    return render(request, "policies/anular_poliza_confirmar.html", {"poliza": poliza})


@login_required
def reporte_anulaciones(request):
    if request.user.is_superuser:
        polizas_anuladas = Policy.objects.filter(anulada=True).select_related(
            "client", "risk_type"
        )
    else:
        polizas_anuladas = Policy.objects.filter(
            anulada=True, client__producer=request.user
        ).select_related("client", "risk_type")

    return render(
        request,
        "policies/reporte_anulaciones.html",
        {"polizas_anuladas": polizas_anuladas},
    )
