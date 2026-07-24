import os
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import models


def policy_directory_path(instance, filename):
    client_name = f"{instance.client.last_name}_{instance.client.first_name}".replace(
        " ", "_"
    )
    return f"polizas/cliente_{instance.client.id}_{client_name}/{filename}"


def cuponera_directory_path(instance, filename):
    client_name = f"{instance.client.last_name}_{instance.client.first_name}".replace(
        " ", "_"
    )
    return f"cuponeras/cliente_{instance.client.id}_{client_name}/{filename}"


def comprobante_directory_path(instance, filename):
    client = instance.policy.client
    client_name = f"{client.last_name}_{client.first_name}".replace(" ", "_")
    return f"comprobantes/cliente_{client.id}_{client_name}/{filename}"


class RiskType(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Riesgo"
        verbose_name_plural = "Tipos de Riesgos"
        ordering = ["nombre"]


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

    FRECUENCIAS_REFACTURACION = [
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

    patente = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Patente / Dominio",
        db_index=True,
    )

    # --- NUEVOS CAMPOS DE VEHÍCULO ---
    marca = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Marca del Auto"
    )
    modelo = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Modelo del Auto"
    )
    version_auto = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Versión del Auto"
    )
    anio_auto = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Año del Auto"
    )
    # ---------------------------------

    risk_type = models.ForeignKey(
        RiskType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo de Riesgo (Dinámico)",
    )

    tipo_poliza = models.CharField(
        max_length=20,
        choices=TIPOS_POLIZA,
        default="AUTO",
        verbose_name="Tipo de póliza (Categoría)",
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

    renovacion_de = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Renueva a la póliza anterior",
        related_name="renovaciones",
        help_text=(
            "Seleccione la póliza anterior correspondiente al mismo bien en caso"
            " de renovación."
        ),
    )

    fecha_primer_vencimiento_cuponera = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha primer vencimiento",
        help_text="Si se deja vacío, se usará la fecha de inicio de la póliza.",
    )

    email_vencimiento_enviado = models.BooleanField(
        default=False,
        verbose_name="Email de vencimiento enviado",
    )

    ultimo_envio_cuponera = models.DateField(
        null=True, blank=True, verbose_name="Última Cuponera Enviada"
    )
    ultimo_envio_vencimiento = models.DateField(
        null=True, blank=True, verbose_name="Último Aviso Vencimiento"
    )

    pdf_poliza = models.FileField(
        upload_to=policy_directory_path,
        blank=True,
        null=True,
        verbose_name="Archivo PDF de póliza",
    )

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMAS_PAGO,
        default="TARJETA",
        verbose_name="Forma de pago",
    )

    cuponera_pdf = models.FileField(
        upload_to=cuponera_directory_path,
        blank=True,
        null=True,
        verbose_name="Archivo PDF cuponera",
    )

    frecuencia_cuponera = models.IntegerField(
        choices=FRECUENCIAS_REFACTURACION,
        default=1,
        verbose_name="Frecuencia de refacturación (meses)",
    )

    anulada = models.BooleanField(default=False, verbose_name="¿Póliza Anulada?")
    fecha_anulacion = models.DateField(
        null=True, blank=True, verbose_name="Fecha de Anulación"
    )
    motivo_anulacion = models.TextField(
        null=True, blank=True, verbose_name="Motivo de la baja"
    )

    # 🟢 CAMPO AGREGADO PARA SOLUCIONAR EL ERROR DE "created_at"
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.company_obj:
            self.company = self.company_obj.nombre
        super().save(*args, **kwargs)

    @property
    def pdf_url(self):
        if self.pdf_poliza:
            try:
                return self.pdf_poliza.url
            except Exception:
                return str(self.pdf_poliza)
        return None

    @property
    def cuponera_url(self):
        if self.cuponera_pdf:
            try:
                return self.cuponera_pdf.url
            except Exception:
                return str(self.cuponera_pdf)
        return None

    @property
    def estado(self):
        if self.anulada:
            return "ANULADA"

        if not self.end_date:
            return "SIN FECHA"

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
        proximo = (
            self.pagos.filter(fecha_pago__isnull=True)
            .order_by("fecha_vencimiento")
            .first()
        )
        return proximo.fecha_vencimiento if proximo else None

    def __str__(self):
        return f"{self.policy_number} - {self.client.nombre_completo()}"

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ["end_date"]
        indexes = [
            models.Index(fields=["end_date"]),
            models.Index(fields=["policy_number"]),
            models.Index(fields=["patente"]),
        ]


class Payment(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PROXIMO", "Próximo a vencer"),
        ("HOY", "Vence hoy"),
        ("PAGADO", "Pagado"),
        ("VENCIDO", "Vencido"),
        ("ANULADO", "Anulado"),
    ]

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Póliza",
    )

    numero_cuota = models.IntegerField(verbose_name="Número de cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    fecha_pago = models.DateField(
        blank=True, null=True, verbose_name="Fecha de pago"
    )
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
    comprobante = models.FileField(
        upload_to=comprobante_directory_path,
        blank=True,
        null=True,
        verbose_name="Archivo comprobante",
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
        if self.policy.anulada:
            return "ANULADO"

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
            f"Hola {cliente} 👋\n\n"
            "Esperamos que te encuentres muy bien.\n\n"
            "Te escribimos desde *Fuerza Natural Broker de Seguros* para"
            " recordarte el próximo vencimiento de tu póliza.\n\n"
            f"📌 Póliza N°: {numero_poliza}\n"
            f"💳 Cuota N°: {self.numero_cuota}\n"
            f"📅 Vencimiento: {fecha}\n\n"
            "Te recomendamos realizar el pago antes de la fecha indicada para"
            " evitar cualquier interrupción en tu cobertura.\n\n"
            "Una vez realizado, podés enviarnos el comprobante por este medio"
            " para registrarlo.\n\n"
            "Ante cualquier consulta, estamos para ayudarte.\n\n"
            "Saludos cordiales,\n"
            "*Fuerza Natural Broker de Seguros*"
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


class EmailLog(models.Model):
    ESTADO_CHOICES = [
        ("ENVIADO", "Enviado"),
        ("ERROR", "Error"),
        ("OMITIDO", "Omitido"),
    ]

    TIPO_CHOICES = [
        ("VENCIMIENTO_POLIZA", "Vencimiento de póliza"),
        ("VENCIMIENTO_CUPONERA", "Vencimiento de cuponera"),
        ("CUMPLEANOS", "Cumpleaños"),
    ]

    policy = models.ForeignKey(
        "Policy",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )
    payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    destinatario = models.EmailField(blank=True, null=True)
    asunto = models.CharField(max_length=255, blank=True)
    error = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Email"
        verbose_name_plural = "Registros de Emails"
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"{self.tipo} - {self.estado} - {self.destinatario}"