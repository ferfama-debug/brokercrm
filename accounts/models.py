from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    is_producer = models.BooleanField(default=False)
    
    # Nuevos campos para controlar el vencimiento de contraseñas
    password_changed_at = models.DateTimeField(default=timezone.now)
    force_password_change = models.BooleanField(default=False)

    # NUEVO INTERRUPTOR DE EMAILS (True = Envía al cliente + copia, False = Solo modo pruebas)
    enviar_emails_a_clientes = models.BooleanField(
        default=True, 
        verbose_name="Enviar emails a clientes"
    )

    def __str__(self):
        return self.username

    # Este método detecta automáticamente cuándo el usuario cambia su clave con éxito
    def save(self, *args, **kwargs):
        if self.pk:  # Si el usuario ya existe en el sistema...
            usuario_anterior = User.objects.get(pk=self.pk)
            # Si el hash de la contraseña nueva es diferente al anterior...
            if usuario_anterior.password != self.password:
                # Ponemos el reloj en cero y apagamos el bloqueo forzado
                self.password_changed_at = timezone.now()
                self.force_password_change = False
                
        super().save(*args, **kwargs)
