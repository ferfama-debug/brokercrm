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
            "seguimiento_estado": forms.Select(attrs={"class": "form-control"}),
            "seguimiento_notas": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "ultimo_contacto": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "proximo_seguimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
            ),
            "permite_whatsapp": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "ultimo_contacto" in self.fields:
            self.fields["ultimo_contacto"].input_formats = ["%Y-%m-%dT%H:%M"]
            if self.instance and self.instance.pk and self.instance.ultimo_contacto:
                self.initial["ultimo_contacto"] = (
                    self.instance.ultimo_contacto.strftime("%Y-%m-%dT%H:%M")
                )
