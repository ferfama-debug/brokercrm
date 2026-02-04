from django.db import models
from django.conf import settings
from policies.models import Policy

User = settings.AUTH_USER_MODEL

class Alert(models.Model):
    LEVELS = (
        ('CRITICA', 'Crítica'),
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    level = models.CharField(max_length=10, choices=LEVELS)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
