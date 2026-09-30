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
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = ["core"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "gradian.urls"
WSGI_APPLICATION = "gradian.wsgi.application"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

USE_TZ = True
TIME_ZONE = "Asia/Tehran"

# --- Keycloak ---
# ISSUER must match the `iss` claim (the URL clients log in through).
# JWKS_URL is how *this* server reaches Keycloak (may differ inside docker).
KEYCLOAK_ISSUER = os.environ["KEYCLOAK_ISSUER"]
KEYCLOAK_JWKS_URL = os.environ.get(
    "KEYCLOAK_JWKS_URL", KEYCLOAK_ISSUER + "/protocol/openid-connect/certs"
)

# --- Team services ---
# 8080 = Keycloak (auth), 8000 = main backend, 8001-8010 = the ten team services (teams/teamN/).
# The core forwards /api/teams/<n>/... to TEAM_URL, where {n} = team number and {port} = its port.
TEAM_SERVICES = [
    ("exam-simulation", "University entrance exam simulation"),
    ("assessment-exams", "Educational assessment exams"),
    ("final-exam-prep", "Final high-school exam preparation"),
    ("private-classes", "Private classes"),
    ("advising", "Educational advising and study planning"),
    ("books", "Book-related services"),
    ("analysis", "Educational analysis"),
    ("question-services", "Question and test-related services"),
    ("major-selection", "Smart university/major selection"),
    ("other-services", "Other educational support services"),
]
TEAM_URL = os.environ.get("TEAM_URL", "http://localhost:{port}")
TEAM_BASE_PORT = 8001
