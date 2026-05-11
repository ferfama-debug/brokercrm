from django.contrib import admin
from django.utils.html import format_html
from .models import Policy, Company, Payment, RiskType


# --- NUEVO: Inline para ver pagos dentro de la Póliza ---
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0  # No mostrar filas vacías extra
    fields = (
        "numero_cuota",
        "fecha_vencimiento",
        "fecha_pago",
        "estado",
        "comprobante",
    )
    readonly_fields = (
        "numero_cuota",
        "fecha_vencimiento",
    )  # Para no editarlos por error aquí
    can_delete = True
    show_change_link = True  # Permite ir al detalle del pago si necesitas


@admin.register(RiskType)
class RiskTypeAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    # Agregamos el Inline aquí
    inlines = [PaymentInline]

    list_display = (
        "policy_number",
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

    list_filter = (
        "risk_type",
        "company_obj",
        "email_vencimiento_enviado",
        "end_date",
    )

    search_fields = (
        "policy_number",
        "client__first_name",
        "client__last_name",
    )

    ordering = ("end_date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(client__producer=request.user)

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
    # MEJORA: Agregamos 'get_client' y 'policy' para saber de quién es el pago
    list_display = (
        "get_client",
        "policy",
        "numero_cuota",
        "fecha_vencimiento",
        "fecha_pago",
        "estado",
    )

    # MEJORA: Filtros por cliente y compañía en la barra lateral
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

    # Función para mostrar el nombre del cliente en la lista de pagos
    def get_client(self, obj):
        return obj.policy.client

    get_client.short_description = "Cliente"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("policy", "policy__client")
        if request.user.is_superuser:
            return qs
        return qs.filter(policy__client__producer=request.user)
