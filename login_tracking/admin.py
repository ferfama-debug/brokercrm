from django.contrib import admin

from .models import LoginLog


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "usuario_o_intento",
        "evento",
        "ip_address",
        "user_agent_corto",
    )
    list_filter = ("evento", "timestamp")
    search_fields = ("user__username", "username_intentado", "ip_address")
    readonly_fields = [f.name for f in LoginLog._meta.fields]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        # Los registros solo los crea el sistema, no un humano desde el admin.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def usuario_o_intento(self, obj):
        return obj.user.username if obj.user else f"(intento) {obj.username_intentado}"
    usuario_o_intento.short_description = "Usuario"

    def user_agent_corto(self, obj):
        return (obj.user_agent[:60] + "...") if len(obj.user_agent) > 60 else obj.user_agent
    user_agent_corto.short_description = "Dispositivo/Navegador"
