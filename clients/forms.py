from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"

        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "phone": "Teléfono",
            "email": "Email",
            "producer": "Productor",
        }

