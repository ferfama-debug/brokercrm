from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # Agregamos los campos al listado general para que los veas a simple vista
    list_display = ('username', 'email', 'is_producer', 'is_staff', 'is_active', 'force_password_change', 'password_changed_at')
    list_filter = ('is_producer', 'is_staff', 'is_active', 'force_password_change')

    # Agregamos la nueva sección de seguridad al final de la ficha del usuario
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Rol', {'fields': ('is_producer',)}),
        ('Seguridad de Contraseñas', {'fields': ('password_changed_at', 'force_password_change')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_producer', 'is_staff', 'is_active'),
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('username',)