from django.shortcuts import render, redirect, get_object_or_404
from .models import Policy, Payment
from clients.models import Client
from datetime import date

# 🔥 SUPABASE
from core.supabase_client import subir_archivo_supabase


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

        # 🔥 ARCHIVOS
        pdf = request.FILES.get("pdf_poliza")
        cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = None
        cuponera_url = None

        # 🔥 SUBIDA A SUPABASE
        if pdf:
            pdf_url = subir_archivo_supabase(pdf, "polizas_clientes")

        if cuponera:
            cuponera_url = subir_archivo_supabase(cuponera, "cuponeras_clientes")

        # 🔥 GUARDADO
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

        print("GUARDADO PDF:", pdf_url)
        print("GUARDADO CUPONERA:", cuponera_url)

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

        # 🔥 ARCHIVOS
        pdf = request.FILES.get("pdf_poliza")
        cuponera = request.FILES.get("cuponera_pdf")

        pdf_url = None
        cuponera_url = None

        # 🔥 SUBIDA A SUPABASE
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

        return redirect(f"/clientes/ver/{poliza.client.id}/")

    return render(
        request,
        "policies/renovar_poliza.html",
        {
            "poliza": poliza,
        },
    )


# 🔥 MARCAR PAGO
def marcar_pago(request, pago_id):

    pago = get_object_or_404(Payment, id=pago_id)

    pago.estado = "PAGADO"
    pago.fecha_pago = date.today()
    pago.save()

    return redirect(f"/clientes/ver/{pago.policy.client.id}/")
