from django.shortcuts import render, redirect, get_object_or_404
from .models import Policy, Payment
from clients.models import Client
from datetime import date

from core.supabase_client import subir_archivo_supabase

from django.core.mail import send_mail
from django.conf import settings

# 🔥 MENSAJES
from django.contrib import messages


def lista_polizas(request):

    compania = request.GET.get("compania")

    companias = Policy.objects.values_list("company", flat=True).distinct()

    clientes = Client.objects.prefetch_related("policy_set")

    if compania:
        clientes = clientes.filter(policy__company=compania).distinct()

    return render(
        request,
        "policies/lista_polizas.html",
        {
            "clientes": clientes,
            "companias": companias,
            "compania_seleccionada": compania,
        },
    )


def crear_poliza(request):

    clientes = Client.objects.all().order_by("last_name", "first_name")
    cliente_id = request.GET.get("cliente")

    if request.method == "POST":

        client = get_object_or_404(Client, id=request.POST.get("client"))

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

        pdf = request.FILES.get("pdf_poliza")
        cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = None
        cuponera_url = None

        if pdf:
            pdf_url = subir_archivo_supabase(pdf, "polizas_clientes")

        if cuponera:
            cuponera_url = subir_archivo_supabase(cuponera, "cuponeras_clientes")

        nueva_poliza = Policy(
            client=client,
            company=request.POST.get("company"),
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=request.POST.get("tipo_poliza"),
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=request.POST.get("frecuencia_cuponera"),
            pdf_poliza=pdf_url,
            cuponera_pdf=cuponera_url,
        )

        nueva_poliza.save()

        messages.success(request, "✅ Póliza creada correctamente")

        return redirect(f"/clientes/ver/{client.id}/")

    return render(
        request,
        "policies/crear_poliza.html",
        {
            "clientes": clientes,
            "cliente_id": cliente_id,
        },
    )


def renovar_poliza(request, poliza_id):

    poliza = get_object_or_404(Policy, id=poliza_id)

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

        pdf = request.FILES.get("pdf_poliza")
        cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = None
        cuponera_url = None

        if pdf:
            pdf_url = subir_archivo_supabase(pdf, "polizas_clientes")

        if cuponera:
            cuponera_url = subir_archivo_supabase(cuponera, "cuponeras_clientes")

        nueva_poliza = Policy(
            client=poliza.client,
            company=poliza.company,
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=poliza.tipo_poliza,
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            frecuencia_cuponera=request.POST.get("frecuencia_cuponera"),
            pdf_poliza=pdf_url,
            cuponera_pdf=cuponera_url,
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


def marcar_pago(request, pago_id):

    pago = get_object_or_404(Payment, id=pago_id)

    pago.estado = "PAGADO"
    pago.fecha_pago = date.today()
    pago.save()

    messages.success(request, "💰 Pago registrado correctamente")

    return redirect(f"/clientes/ver/{pago.policy.client.id}/")


# 🔥 EMAIL PROFESIONAL
def enviar_poliza(request, poliza_id):

    poliza = get_object_or_404(Policy, id=poliza_id)
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
        mensaje += f"\n💳 Ver cuponera:\n{poliza.cuponera_pdf}\n"

    mensaje += "\nFuerza Natural Broker de Seguros"

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [cliente.email],
            fail_silently=False,
        )

        messages.success(request, f"✅ Email enviado correctamente a {cliente.email}")

    except Exception as e:
        print("ERROR EMAIL:", e)
        messages.error(request, "❌ Error al enviar el email")

    return redirect(f"/clientes/ver/{cliente.id}/")