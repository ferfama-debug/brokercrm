from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "message",
        "tipo",
        "level",
        "user",
        "policy",
        "resolved",
        "created_at",
    )
    list_filter = (
        "tipo",
        "level",
        "resolved",
        "created_at",
    )
    search_fields = (
        "message",
        "policy__policy_number",
        "policy__client__first_name",
        "policy__client__last_name",
        "user__username",
        "user__email",
    )
    list_select_related = (
        "user",
        "policy",
        "policy__client",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "user",
            "policy",
            "policy__client",
        )
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)