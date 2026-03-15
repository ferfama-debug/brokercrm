from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta
from cloudinary.models import CloudinaryField


def ruta_poliza(instance, filename):
    return f"clientes/{instance.client.id}/polizas/{filename}"


def ruta_cuponera(instance, filename):
    return f"clientes/{instance.client.id}/cuponeras/{filename}"


class Policy(models.Model):

    TIPOS_POLIZA = [
        ("AUTO", "Auto"),
        ("MOTO", "Moto"),
        ("HOGAR", "Hogar"),
        ("VIDA", "Vida"),
        ("COMERCIO", "Comercio"),
        ("AP", "Accidentes Personales"),
        ("RC", "Responsabilidad Civil"),
        ("OTRO", "Otro"),
    ]

    FORMAS_PAGO = [
        ("TARJETA", "Tarjeta de crédito"),
        ("CBU", "Débito / CBU"),
        ("CUPONERA", "Cuponera de pago"),
    ]

    FRECUENCIAS_CUPONERA = [
        (1, "Mensual"),
        (3, "Trimestral"),
        (4, "Cuatrimestral"),
        (6, "Semestral"),
        (12, "Anual"),
    ]

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        verbose_name="Cliente",
        db_index=True,
    )

    company = models.CharField(
        max_length=100,
        verbose_name="Compañía",
    )

    policy_number = models.CharField(
        max_length=50,
        verbose_name="Número de póliza",
        db_index=True,
    )

    tipo_poliza = models.CharField(
        max_length=20,
        choices=TIPOS_POLIZA,
        default="AUTO",
        verbose_name="Tipo de póliza",
    )

    insurance_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Detalle del seguro",
    )

    start_date = models.DateField(
        verbose_name="Fecha de inicio"
    )

    end_date = models.DateField(
        verbose_name="Fecha de vencimiento",
        db_index=True,
    )

    # PDF de póliza en Cloudinary
    pdf_poliza = CloudinaryField(
        resource_type="raw",
        folder="clientes/polizas",
        blank=True,
        null=True,
        verbose_name="PDF de póliza",
    )

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMAS_PAGO,
        default="TARJETA",
        verbose_name="Forma de pago",
    )

    # PDF de cuponera en Cloudinary
    cuponera_pdf = CloudinaryField(
        resource_type="raw",
        folder="clientes/cuponeras",
        blank=True,
        null=True,
        verbose_name="Cuponera PDF",
    )

    frecuencia_cuponera = models.IntegerField(
        choices=FRECUENCIAS_CUPONERA,
        blank=True,
        null=True,
        verbose_name="Frecuencia de cuponera (meses)"
    )

    @property
    def estado(self):

        hoy = date.today()
        dias = (self.end_date - hoy).days

        if dias < 0:
            return "VENCIDA"
        elif dias <= 30:
            return "POR VENCER"
        else:
            return "ACTIVA"

    @property
    def proximo_pago_cuponera(self):

        if self.forma_pago != "CUPONERA":
            return None

        if not self.frecuencia_cuponera:
            return None

        fecha = self.start_date
        hoy = date.today()

        while fecha <= hoy:
            fecha = fecha + relativedelta(months=self.frecuencia_cuponera)

        return fecha

    def __str__(self):
        return f"{self.policy_number} - {self.client.nombre_completo()}"

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ["end_date"]
        indexes = [
            models.Index(fields=["end_date"]),
            models.Index(fields=["policy_number"]),
        ]
