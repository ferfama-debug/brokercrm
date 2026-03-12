from .models import Alert


def alert_count(request):

    if not request.user.is_authenticated:
        return {}

    # ALERTAS SEGÚN USUARIO
    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)
    else:
        alertas = Alert.objects.filter(user=request.user, resolved=False)

    total = alertas.count()

    # DETECTAR NIVEL MÁS ALTO
    color = ""

    if alertas.filter(level="CRITICA").exists():
        color = "critica"
    elif alertas.filter(level="ALTA").exists():
        color = "alta"
    elif alertas.filter(level="MEDIA").exists():
        color = "media"

    # ÚLTIMAS ALERTAS PARA CAMPANA
    ultimas_alertas = alertas.order_by("-created_at")[:5]

    return {
        "alert_count": total,
        "alert_color": color,
        "ultimas_alertas": ultimas_alertas,
    }
