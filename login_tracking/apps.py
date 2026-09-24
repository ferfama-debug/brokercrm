from django.apps import AppConfig


class LoginTrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "login_tracking"
    verbose_name = "Registro de accesos"

    def ready(self):
        import login_tracking.signals  # noqa: F401
