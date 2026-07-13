from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

class PasswordExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si el usuario inició sesión y tiene el bloqueo de contraseña activo
        if request.user.is_authenticated and getattr(request.user, 'force_password_change', False):
            try:
                # Intentamos buscar las rutas usando el namespace 'accounts:' de tu CRM
                password_change_url = reverse('accounts:password_change')
                logout_url = reverse('accounts:logout')
            except NoReverseMatch:
                try:
                    # Si no existiera el namespace, probamos con los nombres directos
                    password_change_url = reverse('password_change')
                    logout_url = reverse('logout')
                except NoReverseMatch:
                    # Si no encuentra ninguna de las dos rutas, dejamos pasar al usuario 
                    # para evitar que la página web tire un Error 500 en producción.
                    return self.get_response(request)

            # Si el usuario intenta navegar a cualquier lado que NO sea cambiar la clave o desloguearse:
            if request.path != password_change_url and request.path != logout_url:
                return redirect(password_change_url)

        return self.get_response(request)