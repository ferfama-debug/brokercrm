from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Company, Payment, Policy, RiskType


# --- Inline para ver pagos dentro de la Póliza ---
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1  # Deja una fila vacía para agregar una cuota fácilmente
    fields = (
        "numero_cuota",
        "fecha_vencimiento",
        "fecha_pago",
        "estado",
        "comprobante",
    )
    readonly_fields = ()
    can_delete = True
    show_change_link = True


# --- Inline para ver las renovaciones hijas de esta póliza ---
class RenovacionInline(admin.TabularInline):
    model = Policy
    fk_name = "renovacion_de"
    extra = 0
    fields = (
        "policy_number",
        "start_date",
        "end_date",
        "forma_pago",
    )
    # 🟢 Quitamos los campos de readonly_fields para evitar que se muestren como guiones (-) 
    # y permitimos que `show_change_link = True` genere el enlace para ver/editar la póliza.
    readonly_fields = ()
    can_delete = False
    show_change_link = True
    verbose_name = "Póliza Renovada (Posterior)"
    verbose_name_plural = "Historial de Renovaciones Posteriores"


@admin.register(RiskType)
class RiskTypeAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    inlines = [PaymentInline, RenovacionInline]

    list_display = (
        "policy_number",
        "patente",
        "client",
        "company_obj",
        "risk_type",
        "end_date",
        "estado_colored",
        "email_enviado",
    )

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "client",
                    "company_obj",
                    "policy_number",
                    "renovacion_de",
                    "ver_poliza_anterior_link",
                    "patente",
                    "risk_type",
                    "tipo_poliza",
                    "insurance_type",
                )
            },
        ),
        (
            "Vigencia de Póliza",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Configuración de Cuponera y Pagos",
            {
                "fields": (
                    "forma_pago",
                    "frecuencia_cuponera",
                    "fecha_primer_vencimiento_cuponera",
                    "cuponera_pdf",
                ),
                "description": "Si la forma de pago es Cuponera, definí aquí cuándo debe vencer la primera cuota.",
            },
        ),
        (
            "Documentación y Alertas",
            {
                "fields": ("pdf_poliza", "email_vencimiento_enviado"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("ver_poliza_anterior_link",)

    list_filter = (
        "risk_type",
        "company_obj",
        "email_vencimiento_enviado",
        "end_date",
    )

    search_fields = (
        "policy_number",
        "patente",
        "client__first_name",
        "client__last_name",
    )

    ordering = ("end_date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(client__producer=request.user)

    def ver_poliza_anterior_link(self, obj):
        if obj.renovacion_de:
            url = reverse("admin:policies_policy_change", args=[obj.renovacion_de.pk])
            return format_html(
                '<a href="{}" target="_blank">🔗 Ver póliza anterior (N°: {})</a>',
                url,
                obj.renovacion_de.policy_number,
            )
        return "Es una póliza original (sin renovación previa)"

    ver_poliza_anterior_link.short_description = "Póliza de Origen"

    def estado_colored(self, obj):
        estado = obj.estado
        if estado == "VENCIDA":
            color = "#dc3545"
        elif estado == "POR VENCER":
            color = "#fd7e14"
        else:
            color = "#28a745"

        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            estado,
        )

    estado_colored.short_description = "Estado"

    def email_enviado(self, obj):
        return obj.email_vencimiento_enviado

    email_enviado.boolean = True
    email_enviado.short_description = "Email enviado"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "get_client",
        "policy",
        "numero_cuota",
        "fecha_vencimiento",
        "fecha_pago",
        "estado",
    )

    list_filter = (
        "estado",
        "policy__client",
        "policy__company_obj",
        "fecha_vencimiento",
    )

    search_fields = (
        "policy__policy_number",
        "policy__client__first_name",
        "policy__client__last_name",
    )

    ordering = ("fecha_vencimiento",)

    def get_client(self, obj):
        return obj.policy.client

    get_client.short_description = "Cliente"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "policy", "policy__client"
        )
        if request.user.is_superuser:
            return qs
        return qs.filter(policy__client__producer=request.user)