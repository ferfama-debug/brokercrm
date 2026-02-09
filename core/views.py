from django.http import HttpResponse


def home(request):
    return HttpResponse("<h1>CRM Fuerza Natural Brokers funcionando 🚀</h1>")
