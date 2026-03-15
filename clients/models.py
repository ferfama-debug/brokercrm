from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Client(models.Model):

    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)

    # DNI como identificador fuerte
    dni = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    phone = models.CharField(max_length=20)

    email = models.EmailField(
        blank=True,
        null=True,
    )

    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_producer": True},
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name"]),
            models.Index(fields=["dni"]),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def nombre_completo(self):
        return f"{self.last_name}, {self.first_name}"

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"