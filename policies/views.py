from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Policy, Payment, Company
from clients.models import Client
from datetime import date, timedelta

from django.core.mail import send_mail
from django.conf import settings

from django.contrib import messages

print("🔥 SUPABASE URL:", settings.SUPABASE_URL)
print("🔥 SUPABASE KEY:", settings.SUPABASE_KEY)


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

    vencidos = pagos.filter(fecha_vencimiento__lt=hoy, fecha_pago__isnull=True)
    hoy_vencen = pagos.filter(fecha_vencimiento=hoy, fecha_pago__isnull=True)
    proximos = pagos.filter(
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=en_3_dias,
        fecha_pago__isnull=True,
    )

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

    compania = request.GET.get("compania")
    buscar = request.GET.get("buscar")

    if request.user.is_superuser:
        clientes = Client.objects.prefetch_related("policy_set")
    else:
        clientes = Client.objects.filter(producer=request.user).prefetch_related(
            "policy_set"
        )

    if buscar:
        clientes = clientes.filter(
            Q(first_name__icontains=buscar)
            | Q(last_name__icontains=buscar)
            | Q(policy__policy_number__icontains=buscar)
        ).distinct()

    if compania:
        clientes = clientes.filter(policy__company=compania).distinct()

    companias = Policy.objects.values_list("company", flat=True).distinct()

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

    if request.method == "POST":

        # 🔥 CORRECCIÓN SEGURA
        if request.user.is_superuser:
            client = get_object_or_404(Client, id=request.POST.get("client"))
        else:
            client = get_object_or_404(
                Client,
                id=request.POST.get("client"),
                producer=request.user
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
                    "error": "Debe completar las fechas",
                },
            )

        archivo_poliza = request.FILES.get("pdf_poliza")
        archivo_cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = procesar_archivo(archivo_poliza, "polizas_clientes")
        cuponera_url = procesar_archivo(
            archivo_cuponera, "cuponeras_clientes"
        )

        company_id = request.POST.get("company")
        company_obj = None
        company_nombre = None

        if company_id:
            try:
                company_obj = Company.objects.get(id=company_id)
                company_nombre = company_obj.nombre
            except Exception:
                company_nombre = request.POST.get("company")

        nueva_poliza = Policy(
            client=client,
            company=company_nombre,
            company_obj=company_obj,
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=request.POST.get("tipo_poliza"),
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=(
                int(request.POST.get("frecuencia_cuponera"))
                if request.POST.get("frecuencia_cuponera")
                else None
            ),
            pdf_poliza=pdf_url or None,
            cuponera_pdf=cuponera_url or None,
        )

        nueva_poliza.save()

        messages.success(request, "✅ Póliza creada correctamente")

        return redirect(f"/clientes/ver/{client.id}/")

    companias = Company.objects.all().order_by("nombre")

    return render(
        request,
        "policies/crear_poliza.html",
        {
            "clientes": clientes,
            "cliente_id": cliente_id,
            "companias": companias,
        },
    )


@login_required
def renovar_poliza(request, poliza_id):

    # 🔥 CORRECCIÓN SEGURA
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(
            Policy,
            id=poliza_id,
            client__producer=request.user
        )

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

        archivo_poliza = request.FILES.get("pdf_poliza")
        archivo_cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = procesar_archivo(archivo_poliza, "polizas_clientes")
        cuponera_url = procesar_archivo(
            archivo_cuponera, "cuponeras_clientes"
        )

        nueva_poliza = Policy(
            client=poliza.client,
            company=poliza.company,
            company_obj=poliza.company_obj,
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=poliza.tipo_poliza,
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=(
                int(request.POST.get("frecuencia_cuponera"))
                if request.POST.get("frecuencia_cuponera")
                else None
            ),
            pdf_poliza=pdf_url or None,
            cuponera_pdf=cuponera_url or None,
        )

        nueva_poliza.save()

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

    # 🔥 CORRECCIÓN SEGURA
    if request.user.is_superuser:
        pago = get_object_or_404(Payment, id=pago_id)
    else:
        pago = get_object_or_404(
            Payment,
            id=pago_id,
            policy__client__producer=request.user
        )

    if request.method == "POST":

        comprobante_url = procesar_archivo(
            request.FILES.get("comprobante"), "comprobantes_pagos"
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

    # 🔥 CORRECCIÓN SEGURA
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(
            Policy,
            id=poliza_id,
            client__producer=request.user
        )

    cliente = poliza.client

    if not cliente.email:
        messages.error(request, "❌ El cliente no tiene email cargado")
        return redirect(f"/clientes/ver/{cliente.id}/")

    asunto = f"Póliza {poliza.policy_number} - Fuerza Natural Broker"

    mensaje = f"""
Hola {cliente.first_name},

Te enviamos tu póliza:

📌 Compañía: {poliza.company}
📅 Vigencia: {poliza.start_date} - {poliza.end_date}
"""

    if poliza.pdf_poliza:
        mensaje += f"\n📄 Ver póliza:\n{poliza.pdf_poliza}\n"

    if poliza.cuponera_pdf:
        mensaje += f"\n💳 Te adjuntamos la cuponera:\n{poliza.cuponera_pdf}\n"
        mensaje += "\nCuando realices cada pago, envianos el comprobante.\n"

    mensaje += "\nFuerza Natural Broker de Seguros"

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [cliente.email],
            fail_silently=False,
        )

        messages.success(request, f"✅ Email enviado a {cliente.email}")

    except Exception as e:
        print("ERROR EMAIL:", e)
        messages.error(request, "❌ Error al enviar el email")

    return redirect(f"/clientes/ver/{cliente.id}/")


@login_required
def detalle_poliza(request, poliza_id):

    # 🔥 CORRECCIÓN SEGURA
    if request.user.is_superuser:
        poliza = get_object_or_404(Policy, id=poliza_id)
    else:
        poliza = get_object_or_404(
            Policy,
            id=poliza_id,
            client__producer=request.user
        )

    return render(
        request,
        "policies/detalle_poliza.html",
        {
            "poliza": poliza,
        },
    )