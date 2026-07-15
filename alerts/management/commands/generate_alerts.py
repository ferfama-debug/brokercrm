from django.core.management.base import BaseCommand
# 👈 IMPORTANTE: Cambiamos el import para traer la función que ejecuta todo
from alerts.services import generar_todas_las_alertas


class Command(BaseCommand):
    help = "Genera todas las alertas del sistema (vencimientos, cuotas, deudas y cumpleaños)"

    def handle(self, *args, **kwargs):
        # Ejecutamos el motor completo de alertas
        generar_todas_las_alertas()

        self.stdout.write(
            self.style.SUCCESS("Todas las alertas del sistema fueron procesadas correctamente.")
        )