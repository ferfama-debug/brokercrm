from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings

class PasswordExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. 🛡️ Defensa extrema: si el middleware se ejecuta antes de la autenticación de Django
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)

        # 2. Si el usuario no requiere cambio de contraseña, pasa normalmente
        if not getattr(request.user, 'force_password_change', False):
            return self.get_response(request)

        # 3. EXCLUSIONES CRÍTICAS: No interceptar archivos estáticos, media o el health check de Render
        path_actual = request.path
        if (
            path_actual.startswith(settings.STATIC_URL) or 
            path_actual.startswith(settings.MEDIA_URL) or 
            path_actual == '/health/' or 
            path_actual == '/health'
        ):
            return self.get_response(request)

        # 4. Resolución segura de URLs de control
        try:
            password_change_url = reverse('accounts:password_change')
            logout_url = reverse('accounts:logout')
        except NoReverseMatch:
            try:
                # Fallback sin namespace
                password_change_url = reverse('password_change')
                logout_url = reverse('logout')
            except NoReverseMatch:
                # Si fallan ambos, usamos rutas seguras harcodeadas
                password_change_url = '/accounts/password-change/'
                logout_url = '/accounts/logout/'

        # 5. Redirección forzada: Si no está en las pantallas permitidas, lo mandamos a cambiar la clave
        if path_actual != password_change_url and path_actual != logout_url:
            # Evitamos bucles si la URL de éxito (done) está en proceso
            if 'password-change/done' in path_actual:
                return self.get_response(request)
            return redirect(password_change_url)

        return self.get_response(request)