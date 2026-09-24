from django.conf import settings
from django.db import models


class LoginLog(models.Model):
    EVENT_CHOICES = (
        ("login_exitoso", "Login exitoso"),
        ("login_fallido", "Login fallido"),
        ("logout", "Logout"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_logs",
    )
    username_intentado = models.CharField(
        max_length=150,
        blank=True,
        help_text="Se guarda cuando el login falla y no sabemos qué usuario es.",
    )
    evento = models.CharField(max_length=20, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Registro de acceso"
        verbose_name_plural = "Registros de acceso"
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        quien = self.user.username if self.user else (self.username_intentado or "desconocido")
        return f"{quien} - {self.evento} - {self.timestamp:%Y-%m-%d %H:%M}"
