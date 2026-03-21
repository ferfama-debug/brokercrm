from django.contrib import admin
from django.utils.html import format_html
from .models import Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = (
        'policy_number',
        'client',
        'company',
        'end_date',
        'estado_colored',
        'email_enviado',
    )

    list_filter = (
        'company',
        'email_vencimiento_enviado',
        'end_date',
    )

    search_fields = (
        'policy_number',
        'client__first_name',
        'client__last_name',
    )

    ordering = ('end_date',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(client__producer=request.user)

    # 🔥 ESTADO CON COLORES REALES
    def estado_colored(self, obj):
        estado = obj.estado

        if estado == "VENCIDA":
            color = "#dc3545"  # rojo
        elif estado == "POR VENCER":
            color = "#fd7e14"  # naranja
        else:
            color = "#28a745"  # verde

        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            estado
        )

    estado_colored.short_description = "Estado"

    # 🔥 EMAIL ENVIADO (ICONO)
    def email_enviado(self, obj):
        return obj.email_vencimiento_enviado

    email_enviado.boolean = True
    email_enviado.short_description = "Email enviado"