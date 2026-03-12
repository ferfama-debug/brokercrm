from django.shortcuts import render, redirect, get_object_or_404
from .models import Policy
from clients.models import Client


def lista_polizas(request):

    compania = request.GET.get("compania")

    companias = Policy.objects.values_list("company", flat=True).distinct()

    if compania:
        clientes = (
            Client.objects.prefetch_related("policy_set")
            .filter(policy__company=compania)
            .distinct()
        )
    else:
        clientes = Client.objects.prefetch_related("policy_set")

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

    clientes = Client.objects.all()
    cliente_id = request.GET.get("cliente")

    if request.method == "POST":

        client = Client.objects.get(id=request.POST["client"])

        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            return render(
                request,
                "policies/crear_poliza.html",
                {
                    "clientes": clientes,
                    "cliente_id": cliente_id,
                    "error": "Debe completar las fechas de inicio y vencimiento",
                },
            )

        pdf = request.FILES.get("pdf_poliza")
        cuponera = request.FILES.get("cuponera_pdf")

        Policy.objects.create(
            client=client,
            company=request.POST.get("company"),
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=request.POST.get("tipo_poliza"),
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            pdf_poliza=pdf,
            cuponera_pdf=cuponera,
        )

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

        Policy.objects.create(
            client=poliza.client,
            company=poliza.company,
            policy_number=request.POST.get("policy_number"),
            tipo_poliza=poliza.tipo_poliza,
            start_date=start_date,
            end_date=end_date,
            forma_pago=request.POST.get("forma_pago"),
            pdf_poliza=pdf,
            cuponera_pdf=cuponera,
        )

        return redirect(f"/clientes/ver/{poliza.client.id}/")

    return render(
        request,
        "policies/renovar_poliza.html",
        {
            "poliza": poliza,
        },
    )
