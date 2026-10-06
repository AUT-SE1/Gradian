"""Django settings. Everything configurable comes from the environment (see .env.example)."""

from pathlib import Path

import django_stubs_ext
from django.core.exceptions import ImproperlyConfigured

from gradian import env

# Lets annotations like ModelAdmin[Profile] work at runtime (they are only types otherwise).
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
env.load_dotenv(Path(env.get("DOTENV_FILE", str(REPO_ROOT / ".env"))))

ENVIRONMENT = env.get("ENVIRONMENT", "development")
if ENVIRONMENT not in {"development", "test", "production"}:
    raise ImproperlyConfigured(
        f"ENVIRONMENT must be development, test or production, not {ENVIRONMENT!r}"
    )
IS_PRODUCTION = ENVIRONMENT == "production"

SECRET_KEY = env.require("DJANGO_SECRET_KEY")
DEBUG = env.flag("DJANGO_DEBUG", False) and not IS_PRODUCTION
ALLOWED_HOSTS = env.csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "common",
    "accounts",
]

MIDDLEWARE = [
    "common.middleware.RequestContextMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gradian.urls"
WSGI_APPLICATION = "gradian.wsgi.application"
ASGI_APPLICATION = "gradian.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.require("POSTGRES_DB"),
        "USER": env.require("POSTGRES_USER"),
        "PASSWORD": env.require("POSTGRES_PASSWORD"),
        "HOST": env.get("POSTGRES_HOST", "localhost"),
        "PORT": env.get("POSTGRES_PORT", "5432"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DES-XC-03: Persian, Tehran time. Error codes stay English, messages are Persian.
LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ISSUER must equal the `iss` claim, i.e. the URL clients sign in through.
# INTERNAL_URL is how this server reaches Keycloak (inside docker: http://keycloak:8080).
KEYCLOAK_ISSUER = env.require("KEYCLOAK_ISSUER").rstrip("/")
KEYCLOAK_REALM = env.get("KEYCLOAK_REALM", "gradian")
if not KEYCLOAK_ISSUER.endswith(f"/realms/{KEYCLOAK_REALM}"):
    raise ImproperlyConfigured(
        f"KEYCLOAK_ISSUER must end with /realms/{KEYCLOAK_REALM}, got {KEYCLOAK_ISSUER!r}"
    )
KEYCLOAK_INTERNAL_URL = env.get(
    "KEYCLOAK_INTERNAL_URL", KEYCLOAK_ISSUER.removesuffix(f"/realms/{KEYCLOAK_REALM}")
).rstrip("/")
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
KEYCLOAK_WEB_CLIENT_ID = env.get("KEYCLOAK_WEB_CLIENT_ID", "gradian-web")
# The audience every token must carry, and the client whose service account calls the Admin API.
KEYCLOAK_CORE_CLIENT_ID = env.get("KEYCLOAK_CORE_CLIENT_ID", "gradian-core")
KEYCLOAK_CORE_CLIENT_SECRET = env.require("KEYCLOAK_CORE_CLIENT_SECRET")
KEYCLOAK_TIMEOUT_SECONDS = float(env.get("KEYCLOAK_TIMEOUT_SECONDS", "5"))

FRONTEND_URL = env.require("FRONTEND_URL").rstrip("/")
CORS_ALLOWED_ORIGINS = env.csv("CORS_ALLOWED_ORIGINS", FRONTEND_URL)
PUBLIC_RATE_LIMIT = env.get("PUBLIC_RATE_LIMIT", "60/min")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["accounts.authentication.KeycloakBearerAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.exception_handler",
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Gradian Core Service",
    "DESCRIPTION": "Identity, panels and group-service registry. Source of truth for the API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
    "SCHEMA_PATH_PREFIX": r"/api/v1",
}

# DES-XC-01: JSON lines with request id and user `sub`.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_context": {"()": "common.logging.RequestContextFilter"}},
    "formatters": {"json": {"()": "common.logging.JsonFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "json",
        }
    },
    "root": {"handlers": ["console"], "level": env.get("LOG_LEVEL", "INFO")},
}

# DES-XC-02: production hardening.
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^health/"]  # container health checks speak plain HTTP
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
