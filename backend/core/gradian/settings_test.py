"""Settings for `make test`: no containers, no .env. SQLite in memory, fake Keycloak values."""

import os

_DEFAULTS = {
    "ENVIRONMENT": "test",
    "DJANGO_SECRET_KEY": "test-only-secret-key-not-for-any-real-deployment-0123456789",
    "POSTGRES_DB": "unused",
    "POSTGRES_USER": "unused",
    "POSTGRES_PASSWORD": "unused",
    "POSTGRES_HOST": "unused",
    "POSTGRES_PORT": "5432",
    "KEYCLOAK_PUBLIC_URL": "http://keycloak.test",
    "KEYCLOAK_URL": "http://keycloak.internal.test",
    "KEYCLOAK_CORE_CLIENT_SECRET": "test-client-secret",
    "FRONTEND_URL": "http://frontend.test",
}
for _key, _value in _DEFAULTS.items():
    os.environ.setdefault(_key, _value)

from gradian.settings import *  # noqa: E402, F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast, tests only
# Keep test output quiet; tests that read logs use assertLogs, which still sees every record.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "INFO"},
}
