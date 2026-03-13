from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Alert


@login_required
def alertas(request):

    nivel = request.GET.get("nivel")

    # Si es administrador ve todas
    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)

    # Si es productor ve solo las suyas
    else:
        alertas = Alert.objects.filter(user=request.user, resolved=False)

    # FILTRO POR NIVEL (para el radar)
    if nivel:
        alertas = alertas.filter(level=nivel)

    alertas = alertas.order_by("-created_at")

    return render(
        request,
        "alerts/alertas.html",
        {
            "alertas": alertas,
        },
    )
