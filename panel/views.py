from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from clients.models import Client
from policies.models import Policy
from alerts.models import Alert
from django.contrib.auth.models import User


@login_required
def home(request):
    context = {
        "clientes": Client.objects.count(),
        "polizas": Policy.objects.count(),
        "alertas": Alert.objects.count(),
        "usuarios": User.objects.count(),
    }
    return render(request, "panel/dashboard.html", context)
