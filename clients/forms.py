from django import forms
from .models import Client


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = "__all__"

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "producer": forms.Select(attrs={"class": "form-control"}),
        }
