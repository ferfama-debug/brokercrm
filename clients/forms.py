from django import forms
from .models import Client   # ← ESTE ES EL CAMBIO IMPORTANTE

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Client       # ← TAMBIÉN ESTE
        fields = "__all__"
