# App: login_tracking

Registra automáticamente quién ingresa a tu CRM (login exitoso, login fallido y logout),
guardando usuario, IP, navegador/dispositivo y fecha/hora. Incluye un dashboard visual
y aparece también en el admin de Django.

## 1. Instalación (diff exacto para brokercrm/settings.py)

En tu `INSTALLED_APPS`, agregá `"login_tracking"` al final de la lista:

```python
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "clients",
    "policies",
    "alerts",
    "dashboard",
    "core",
    "panel",
    "login_tracking",   # <-- nueva línea
]
```

No hace falta tocar nada más en `settings.py`: ya usa `AUTH_USER_MODEL = "accounts.User"`,
y el modelo `LoginLog` está armado para funcionar con cualquier modelo de usuario
personalizado (usa `settings.AUTH_USER_MODEL`, no el `User` de Django por defecto),
así que es compatible con tu `accounts.User` sin cambios.

Copiá la carpeta `login_tracking/` dentro de tu proyecto Django (al mismo nivel que tus
otras apps).

En `settings.py`, agregá la app:

```python
INSTALLED_APPS = [
    ...
    "login_tracking",
]
```

## 2. Migraciones

```bash
python manage.py makemigrations login_tracking
python manage.py migrate
```

## 3. Dashboard (opcional pero recomendado)

En el `urls.py` principal de tu proyecto:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("accesos/", include("login_tracking.urls")),
]
```

Con esto, entrando a `https://crm.fuerzanaturalbroker.com/accesos/` (estando logueado
como staff/admin) vas a ver el panel con los últimos 100 accesos, y un resumen de
logins exitosos vs. fallidos en las últimas 24 horas.

## 4. Ver los registros desde el admin de Django

Como ya está registrado en `admin.py`, también vas a poder verlos en
`/admin/login_tracking/loginlog/`, con filtros por fecha y tipo de evento, y buscador
por usuario o IP.

## 5. (Opcional) Alertas por email ante accesos sospechosos

Si querés que te avise por correo cuando detecte muchos intentos fallidos desde una
misma IP, se puede agregar fácilmente a `signals.py` usando `django.core.mail.send_mail`
dentro de `registrar_login_fallido`. Avisame si querés que te lo agregue.

## 6. Geolocalización por IP (opcional)

Los campos `pais` y `ciudad` del modelo están listos para usarse. Para completarlos
automáticamente podés integrar una librería como `django-ipware` + un servicio de
geolocalización (por ejemplo ipinfo.io o geoip2 con la base de datos de MaxMind).
Si querés, te agrego esa parte también.

## Notas de seguridad

- El dashboard solo es visible para usuarios `staff` (`@staff_member_required`).
- Los registros del admin son de solo lectura: nadie puede editarlos ni borrarlos
  manualmente desde ahí, para que el historial sea confiable.
- Si tu servidor está detrás de un proxy/load balancer (Nginx, Cloudflare, etc.),
  verificá que esté seteado el header `X-Forwarded-For` correctamente para que la IP
  registrada sea la real del visitante y no la del proxy.
