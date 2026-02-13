from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    producer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_producer': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"
