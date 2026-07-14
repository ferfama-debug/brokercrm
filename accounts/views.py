from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse
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


# 🔒 VISTA DE CAMBIO DE CONTRASEÑA (Cierra sesión automáticamente al terminar)
class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        # 1. Guardamos la contraseña nueva en la base de datos
        user = form.save()
        
        # 2. Apagamos el bloqueo (force_password_change = False)
        user.force_password_change = False
        user.save()
        
        # 3. Deslogueamos al usuario de la sesión actual
        logout(self.request)
        
        # 4. Dejamos un mensaje para que aparezca en la pantalla de login
        messages.success(self.request, "Contraseña actualizada con éxito. Por favor, iniciá sesión con tu nueva contraseña.")
        
        # 5. Redirigimos directo al login
        return redirect("accounts:login")