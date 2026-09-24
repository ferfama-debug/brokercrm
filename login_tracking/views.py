from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from .models import LoginLog


@staff_member_required
def dashboard(request):
    hace_24h = timezone.now() - timedelta(hours=24)

    accesos_recientes = LoginLog.objects.all()[:100]
    logins_exitosos_24h = LoginLog.objects.filter(
        evento="login_exitoso", timestamp__gte=hace_24h
    ).count()
    logins_fallidos_24h = LoginLog.objects.filter(
        evento="login_fallido", timestamp__gte=hace_24h
    ).count()

    # IPs con muchos intentos fallidos recientes: posible acceso indebido
    ips_sospechosas = (
        LoginLog.objects.filter(evento="login_fallido", timestamp__gte=hace_24h)
        .values("ip_address")
        .distinct()
    )

    contexto = {
        "accesos_recientes": accesos_recientes,
        "logins_exitosos_24h": logins_exitosos_24h,
        "logins_fallidos_24h": logins_fallidos_24h,
        "ips_sospechosas": ips_sospechosas,
    }
    return render(request, "login_tracking/dashboard.html", contexto)
