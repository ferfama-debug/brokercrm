from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    list_display = (
        "last_name",
        "first_name",
        "phone",
        "producer",
        "seguimiento_estado",
        "proximo_seguimiento",
        "cuotas_vencidas",
        "cuotas_pendientes",
    )

    list_filter = (
        "producer",
        "seguimiento_estado",
    )

    search_fields = (
        "first_name",
        "last_name",
        "dni",
        "phone",
        "email",
    )

    readonly_fields = (
        "whatsapp_link",
        "cuotas_vencidas",
        "cuotas_pendientes",
        "total_deuda_vencida",
        "total_deuda_pendiente",
    )

    fieldsets = (
        (
            "Datos personales",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "dni",
                    "phone",
                    "email",
                    "producer",
                )
            },
        ),
        (
            "CRM / Seguimiento",
            {
                "fields": (
                    "seguimiento_estado",
                    "seguimiento_notas",
                    "ultimo_contacto",
                    "proximo_seguimiento",
                    "permite_whatsapp",
                )
            },
        ),
        (
            "Finanzas",
            {
                "fields": (
                    "cuotas_vencidas",
                    "cuotas_pendientes",
                    "total_deuda_vencida",
                    "total_deuda_pendiente",
                )
            },
        ),
        ("WhatsApp", {"fields": ("whatsapp_link",)}),
    )
