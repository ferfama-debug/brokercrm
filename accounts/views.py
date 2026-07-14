from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse
# 🌟 Importaciones certificadas para el cambio de contraseña
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

def health(request):
    return HttpResponse("OK")


User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or "/"
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


def crear_admin_rapido(request):
    return HttpResponse("No disponible", status=403)


# 🔒 VISTA CERTIFICADA PARA CAMBIO DE CONTRASEÑA FORZOSO
# Esta vista procesa el cambio de clave y apaga automáticamente el tilde en la base de datos.
class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        # 1. Guarda la contraseña nueva y mantiene la sesión del usuario activa
        response = super().form_valid(form)
        
        # 2. Desactiva el flag 'force_password_change' en la base de datos
        user = self.request.user
        user.force_password_change = False
        user.save()
        
        return response