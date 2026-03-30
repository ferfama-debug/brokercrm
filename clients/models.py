from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class Client(models.Model):

    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)

    # DNI como identificador fuerte
    dni = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    phone = models.CharField(max_length=20)

    email = models.EmailField(
        blank=True,
        null=True,
    )

    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_producer": True},
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 CAMPOS CRM / SEGUIMIENTO
    ESTADO_SEGUIMIENTO_CHOICES = [
        ("SIN_GESTION", "Sin gestión"),
        ("PENDIENTE", "Pendiente"),
        ("CONTACTADO", "Contactado"),
        ("EN_SEGUIMIENTO", "En seguimiento"),
        ("INTERESADO", "Interesado"),
        ("NO_INTERESADO", "No interesado"),
        ("CLIENTE", "Cliente"),
    ]

    seguimiento_estado = models.CharField(
        max_length=20,
        choices=ESTADO_SEGUIMIENTO_CHOICES,
        default="SIN_GESTION",
        db_index=True,
    )

    seguimiento_notas = models.TextField(
        blank=True,
        null=True,
    )

    ultimo_contacto = models.DateTimeField(
        blank=True,
        null=True,
    )

    proximo_seguimiento = models.DateField(
        blank=True,
        null=True,
        db_index=True,
    )

    permite_whatsapp = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name"]),
            models.Index(fields=["dni"]),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def nombre_completo(self):
        return f"{self.last_name}, {self.first_name}"

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    @property
    def cuotas_vencidas(self):
        from policies.models import Payment

        return Payment.objects.filter(policy__client=self, estado="VENCIDO").count()

    @property
    def cuotas_pendientes(self):
        from policies.models import Payment

        return Payment.objects.filter(policy__client=self, estado="PENDIENTE").count()

    @property
    def total_deuda_vencida(self):
        from policies.models import Payment

        pagos = Payment.objects.filter(policy__client=self, estado="VENCIDO")
        return sum(p.monto or 0 for p in pagos)

    @property
    def total_deuda_pendiente(self):
        from policies.models import Payment

        pagos = Payment.objects.filter(policy__client=self, estado="PENDIENTE")
        return sum(p.monto or 0 for p in pagos)

    @property
    def telefono_normalizado(self):
        if not self.phone:
            return ""
        return "".join(ch for ch in self.phone if ch.isdigit())

    @property
    def whatsapp_link(self):
        telefono = self.telefono_normalizado
        if not telefono:
            return ""
        return f"https://wa.me/{telefono}"

    @property
    def tiene_seguimiento_pendiente(self):
        return bool(self.proximo_seguimiento)

    def marcar_contactado(self, dias_hasta_proximo=7, guardar=True):
        self.ultimo_contacto = timezone.now()
        self.seguimiento_estado = "CONTACTADO"
        self.proximo_seguimiento = (
            self.ultimo_contacto.date() + timedelta(days=dias_hasta_proximo)
        )

        if guardar:
            self.save(
                update_fields=[
                    "ultimo_contacto",
                    "seguimiento_estado",
                    "proximo_seguimiento",
                ]
            )

    def actualizar_seguimiento(
        self,
        estado=None,
        notas=None,
        proximo_seguimiento=None,
        marcar_contacto=False,
        dias_hasta_proximo=7,
        guardar=True,
    ):
        update_fields = []

        if marcar_contacto:
            self.ultimo_contacto = timezone.now()
            self.seguimiento_estado = "CONTACTADO"
            self.proximo_seguimiento = (
                self.ultimo_contacto.date() + timedelta(days=dias_hasta_proximo)
            )
            update_fields.extend(
                ["ultimo_contacto", "seguimiento_estado", "proximo_seguimiento"]
            )

        if estado is not None:
            self.seguimiento_estado = estado
            if "seguimiento_estado" not in update_fields:
                update_fields.append("seguimiento_estado")

        if notas is not None:
            self.seguimiento_notas = notas
            update_fields.append("seguimiento_notas")

        if proximo_seguimiento is not None:
            self.proximo_seguimiento = proximo_seguimiento
            if "proximo_seguimiento" not in update_fields:
                update_fields.append("proximo_seguimiento")

        if guardar and update_fields:
            self.save(update_fields=update_fields)