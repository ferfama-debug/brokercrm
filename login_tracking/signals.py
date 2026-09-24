from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import LoginLog


def get_client_ip(request):
    """Obtiene la IP real del visitante, incluso detrás de un proxy/load balancer."""
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request):
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")[:300]


@receiver(user_logged_in)
def registrar_login_exitoso(sender, request, user, **kwargs):
    LoginLog.objects.create(
        user=user,
        evento="login_exitoso",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    LoginLog.objects.create(
        user=user,
        evento="logout",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@receiver(user_login_failed)
def registrar_login_fallido(sender, credentials, request=None, **kwargs):
    LoginLog.objects.create(
        username_intentado=str(credentials.get("username", ""))[:150],
        evento="login_fallido",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
