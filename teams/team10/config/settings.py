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
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,team10").split(",")

INSTALLED_APPS = ["core"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Each team owns its own database.
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

USE_TZ = True
TIME_ZONE = "Asia/Tehran"
