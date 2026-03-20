from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# CORE
# =========================

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", get_random_secret_key())

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,brokercrm.onrender.com"
).split(",")


# =========================
# APPS
# =========================

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
]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "brokercrm.urls"


# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "brokercrm.wsgi.application"


# =========================
# DATABASE
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =========================
# AUTH
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"


# =========================
# LOCALIZATION
# =========================

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Mendoza"

USE_I18N = True
USE_TZ = True


# =========================
# STATIC FILES
# =========================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =========================
# MEDIA
# =========================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# SEGURIDAD
# =========================

CSRF_TRUSTED_ORIGINS = [
    "https://brokercrm.onrender.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

if DEBUG:
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SAMESITE = "Lax"
else:
    CSRF_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SAMESITE = "None"

SECURE_SSL_REDIRECT = False


# =========================
# LOGIN
# =========================

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/admin/login/"


# =========================
# EMAIL ALERTAS (🔥 LISTO)
# =========================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# 🔥 PONÉ ACÁ TU MAIL EMPRESA
EMAIL_HOST_USER = "fuerzanaturalbroker@gmail.com"

# 🔥 APP PASSWORD (SIN ESPACIOS)
EMAIL_HOST_PASSWORD = "bnrmhkxspegcrhdp"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# =========================
# JAZZMIN CONFIG
# =========================

JAZZMIN_SETTINGS = {
    "site_title": "Fuerza Natural Broker de Seguros",
    "site_header": "Fuerza Natural Broker de Seguros",
    "site_brand": "Fuerza Natural Broker de Seguros",
    "site_logo": "images/img/logo.png",
    "login_logo": "images/img/logo.png",
    "custom_css": "images/css/crm.css",
    "site_logo_classes": "img-circle",
    "site_logo_width": "120px",
    "welcome_sign": "Ingreso Para Productores",
    "copyright": "Fuerza Natural Broker de Seguros",
}


# =========================
# SUPABASE CONFIG
# =========================

SUPABASE_URL = "https://hgpnzjjnlujgaiblzmpp.supabase.co".strip()
SUPABASE_KEY = "sb_publishable_3JBNutKqw2k5EnvL2jd-TQ_BnSBD-Hj".strip()