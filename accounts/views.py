from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse


def health(request):
    return HttpResponse("OK")


User = get_user_model()


def login_view(request):
    try:
        user = User.objects.get(username="admin")
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("/admin/")
    except User.DoesNotExist:
        messages.error(request, "No existe el usuario admin")
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/")


def crear_admin_rapido(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123",
        )
        return HttpResponse("Usuario creado")

    return HttpResponse("Usuario ya existe")
