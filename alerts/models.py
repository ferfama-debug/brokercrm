from django.db import models
from django.conf import settings
from policies.models import Policy

User = settings.AUTH_USER_MODEL


class Alert(models.Model):

    LEVELS = (
        ("CRITICA", "Crítica"),
        ("ALTA", "Alta"),
        ("MEDIA", "Media"),
    )

    # 🔥 NUEVO: tipos de alerta (automatización)
    TIPOS = (
        ("DEUDA", "Deuda"),
        ("VENCIMIENTO", "Vencimiento"),
        ("MANUAL", "Manual"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True,
    )

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        db_index=True,
    )

    message = models.CharField(
        max_length=255
    )

    level = models.CharField(
        max_length=10,
        choices=LEVELS,
        db_index=True,
    )

    # 🔥 NUEVO
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default="MANUAL",
        db_index=True,
    )

    resolved = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    def __str__(self):
        return f"{self.level} - {self.message}"

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ["-created_at"]

        # 🔥 CLAVE: evita duplicados automáticos
        unique_together = ("policy", "tipo", "resolved")