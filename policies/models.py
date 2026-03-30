from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta


class Company(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Compañía"
        verbose_name_plural = "Compañías"


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
        max_length=100, verbose_name="Compañía", blank=True, null=True
    )

    company_obj = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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

    start_date = models.DateField(verbose_name="Fecha de inicio")

    end_date = models.DateField(
        verbose_name="Fecha de vencimiento",
        db_index=True,
    )

    email_vencimiento_enviado = models.BooleanField(
        default=False,
        verbose_name="Email de vencimiento enviado",
    )

    pdf_poliza = models.TextField(
        blank=True,
        null=True,
        verbose_name="URL PDF de póliza",
    )

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMAS_PAGO,
        default="TARJETA",
        verbose_name="Forma de pago",
    )

    cuponera_pdf = models.TextField(
        blank=True,
        null=True,
        verbose_name="URL cuponera",
    )

    frecuencia_cuponera = models.IntegerField(
        choices=FRECUENCIAS_CUPONERA,
        blank=True,
        null=True,
        verbose_name="Frecuencia de cuponera (meses)",
    )

    def _normalizar_url(self, valor):
        if not valor:
            return None

        valor = str(valor).strip()
        return valor or None

    def save(self, *args, **kwargs):
        if self.company_obj:
            self.company = self.company_obj.nombre

        self.pdf_poliza = self._normalizar_url(self.pdf_poliza)
        self.cuponera_pdf = self._normalizar_url(self.cuponera_pdf)

        if self.forma_pago != "CUPONERA":
            self.frecuencia_cuponera = None

        super().save(*args, **kwargs)

        if self.forma_pago == "CUPONERA" and self.frecuencia_cuponera:
            if self.pagos.exists():
                return

            from .models import Payment

            frecuencia = int(self.frecuencia_cuponera)

            fecha = self.start_date
            fecha_fin = self.end_date

            if isinstance(fecha, str):
                fecha = date.fromisoformat(fecha)

            if isinstance(fecha_fin, str):
                fecha_fin = date.fromisoformat(fecha_fin)

            numero = 1

            while fecha <= fecha_fin:
                Payment.objects.create(
                    policy=self, numero_cuota=numero, fecha_vencimiento=fecha
                )
                fecha = fecha + relativedelta(months=frecuencia)
                numero += 1

    @property
    def pdf_url(self):
        return self._normalizar_url(self.pdf_poliza)

    @property
    def cuponera_url(self):
        return self._normalizar_url(self.cuponera_pdf)

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

        frecuencia = int(self.frecuencia_cuponera)
        fecha = self.start_date
        hoy = date.today()

        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)

        while fecha <= hoy:
            fecha = fecha + relativedelta(months=frecuencia)

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


class Payment(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PROXIMO", "Próximo a vencer"),
        ("HOY", "Vence hoy"),
        ("PAGADO", "Pagado"),
        ("VENCIDO", "Vencido"),
    ]

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Póliza",
    )

    numero_cuota = models.IntegerField(verbose_name="Número de cuota")

    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")

    fecha_pago = models.DateField(blank=True, null=True, verbose_name="Fecha de pago")

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="PENDIENTE",
        verbose_name="Estado",
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Monto",
    )

    comprobante = models.TextField(
        blank=True,
        null=True,
        verbose_name="URL comprobante",
    )

    recordatorio_enviado = models.BooleanField(
        default=False,
        verbose_name="Recordatorio enviado",
    )

    @property
    def dias_restantes(self):
        return (self.fecha_vencimiento - date.today()).days

    @property
    def estado_calculado(self):
        hoy = date.today()

        if self.fecha_pago:
            return "PAGADO"

        dias = (self.fecha_vencimiento - hoy).days

        if dias < 0:
            return "VENCIDO"
        elif dias == 0:
            return "HOY"
        elif dias <= 3:
            return "PROXIMO"
        else:
            return "PENDIENTE"

    def mensaje_whatsapp(self):
        cliente = self.policy.client.nombre_completo()
        numero_poliza = self.policy.policy_number
        fecha = self.fecha_vencimiento.strftime("%d/%m/%Y")

        return (
            f"Hola {cliente}, te recordamos que la cuota {self.numero_cuota} "
            f"de tu póliza {numero_poliza} vence el {fecha}. "
            "Por favor, realizá el pago para evitar suspensión de cobertura. "
            "Cualquier duda estamos para ayudarte."
        )

    def whatsapp_link(self):
        telefono = getattr(self.policy.client, "telefono", "")
        mensaje = self.mensaje_whatsapp().replace(" ", "%20")

        return f"https://wa.me/{telefono}?text={mensaje}"

    def save(self, *args, **kwargs):
        self.estado = self.estado_calculado
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.policy.policy_number} - Cuota {self.numero_cuota}"

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["fecha_vencimiento"]