import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (KEY=value per line, no quotes). Real environment variables win.
if (BASE_DIR / ".env").exists():
    for line in (BASE_DIR / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # required: copy .env.example to .env
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,team4").split(",")

INSTALLED_APPS = ["core"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "gradian_auth.middleware.KeycloakAuthMiddleware",
]

# Required: copy .env.example to .env. See packages/gradian-keycloak/README.md for each setting.
KEYCLOAK_PUBLIC_URL = os.environ["KEYCLOAK_PUBLIC_URL"]
KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
KEYCLOAK_CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"]
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")

# Sign-in on this service's own pages (people arrive here by redirect from the panel).
GRADIAN_SERVICE_URL = os.environ.get("GRADIAN_SERVICE_URL", "http://localhost:8004")
GRADIAN_FRONTEND_URL = os.environ.get("GRADIAN_FRONTEND_URL", "http://localhost:5173")
GRADIAN_COOKIE_AUTH = True
GRADIAN_PUBLIC_PATHS = ("/health", "/auth")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Each team owns its own database.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

USE_TZ = True
TIME_ZONE = "Asia/Tehran"
