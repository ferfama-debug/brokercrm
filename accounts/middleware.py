from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse

class PasswordExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo actuamos si el usuario ya inició sesión
        if request.user.is_authenticated:
            
            # Configurá acá los días de vencimiento (ej: 90 días)
            DIAS_MAXIMOS = 90
            
            # Rutas permitidas para evitar que el sistema se bloquee a sí mismo en bucle
            urls_permitidas = [
                reverse('password_change'),
                reverse('password_change_done'),
                reverse('logout'),
            ]
            
            # Si el usuario no está yendo a las pantallas de cambio de clave o logout...
            if request.path not in urls_permitidas and not request.path.startswith('/admin/'):
                usuario = request.user
                ahora = timezone.now()
                
                # Calculamos cuántos días pasaron desde el último cambio
                dias_pasados = (ahora - usuario.password_changed_at).days
                
                # Si tiene el cambio forzado O si ya pasaron los 90 días...
                if usuario.force_password_change or dias_pasados >= DIAS_MAXIMOS:
                    # ¡Lo desviamos directo a cambiar la contraseña!
                    return redirect('password_change')

        return self.get_response(request)