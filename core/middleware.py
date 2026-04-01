from django.shortcuts import redirect


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Si intenta entrar al admin
        if request.path.startswith("/admin"):

            # Si no está logueado → que siga (Django maneja login)
            if not request.user.is_authenticated:
                return self.get_response(request)

            # Si NO es superusuario → lo sacamos
            if not request.user.is_superuser:
                return redirect("/")

        return self.get_response(request)