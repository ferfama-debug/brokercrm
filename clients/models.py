from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Cliente(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    productor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_producer': True}
    )
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"
