from .models import Alert


def alert_count(request):

    if not request.user.is_authenticated:
        return {}

    if request.user.is_superuser:
        alertas = Alert.objects.filter(resolved=False)
    else:
        alertas = Alert.objects.filter(user=request.user, resolved=False)

    total = alertas.count()

    color = ""

    if alertas.filter(level="CRITICA").exists():
        color = "critica"
    elif alertas.filter(level="ALTA").exists():
        color = "alta"
    elif alertas.filter(level="MEDIA").exists():
        color = "media"

    ultimas_alertas = alertas.order_by("-created_at")[:5]

    return {
        "alert_count": total,
        "alert_color": color,
        "ultimas_alertas": list(ultimas_alertas),
    }
