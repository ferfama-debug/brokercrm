from django.db import models
from datetime import date


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

    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, verbose_name="Cliente"
    )

    company = models.CharField(max_length=100, verbose_name="Compañía")

    policy_number = models.CharField(max_length=50, verbose_name="Número de póliza")

    tipo_poliza = models.CharField(
        max_length=20,
        choices=TIPOS_POLIZA,
        default="AUTO",
        verbose_name="Tipo de póliza",
    )

    insurance_type = models.CharField(
        max_length=100, blank=True, verbose_name="Detalle del seguro"
    )

    start_date = models.DateField(verbose_name="Fecha de inicio")

    end_date = models.DateField(verbose_name="Fecha de vencimiento")

    # PDF de la póliza
    pdf_poliza = models.FileField(
        upload_to="polizas/", blank=True, null=True, verbose_name="PDF de póliza"
    )

    # Forma de pago
    forma_pago = models.CharField(
        max_length=20,
        choices=FORMAS_PAGO,
        default="TARJETA",
        verbose_name="Forma de pago",
    )

    # PDF de cuponera
    cuponera_pdf = models.FileField(
        upload_to="cuponeras/", blank=True, null=True, verbose_name="Cuponera PDF"
    )

    @property
    def estado(self):
        hoy = date.today()
        dias = (self.end_date - hoy).days

        if dias < 0:
            return "VENCIDA"

        if dias <= 30:
            return "POR VENCER"

        return "ACTIVA"

    def __str__(self):
        return f"{self.policy_number} - {self.client}"

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ["end_date"]
