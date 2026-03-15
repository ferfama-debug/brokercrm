from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Alert


@login_required
def alertas(request):

    nivel = request.GET.get("nivel", "")

    # Base queryset
    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)
    else:
        alertas = Alert.objects.filter(
            user=request.user,
            resolved=False
        )

    # Filtro por nivel (usado por el radar)
    if nivel:
        alertas = alertas.filter(level=nivel)

    alertas = alertas.order_by("-created_at")

    return render(
        request,
        "alerts/alertas.html",
        {
            "alertas": alertas,
            "nivel": nivel,
        },
    )
