from django.apps import AppConfig

class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'

    def ready(self):
        from .services import generate_expiration_alerts
        try:
            generate_expiration_alerts()
        except Exception:
            pass
