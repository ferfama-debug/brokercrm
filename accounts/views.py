from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse


def health(request):
    return HttpResponse("OK")


User = get_user_model()


def login_view(request):
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/")


def crear_admin_rapido(request):
    user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@test.com",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    if created:
        user.set_password("admin123")
        user.save()
    else:
        cambios = False

        if not user.is_staff:
            user.is_staff = True
            cambios = True

        if not user.is_superuser:
            user.is_superuser = True
            cambios = True

        if not user.is_active:
            user.is_active = True
            cambios = True

        user.set_password("admin123")
        cambios = True

        if cambios:
            user.save()

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("/admin/")
