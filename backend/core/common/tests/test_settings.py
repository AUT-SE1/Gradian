"""Settings: locale, required variables, production hardening (SYS-NFR-05, OPS-06, NFR-01)."""

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from gradian import env
from tests.helpers.covers import covers

CORE_DIR = Path(__file__).resolve().parents[2]
PRODUCTION_ENV = {
    "DOTENV_FILE": "/nonexistent/.env",
    "ENVIRONMENT": "production",
    "DJANGO_SECRET_KEY": "x9Qz-long-random-production-style-key-with-many-unique-chars-1234567890",
    "DJANGO_ALLOWED_HOSTS": "gradian.example",
    "POSTGRES_DB": "gradian",
    "POSTGRES_USER": "gradian",
    "POSTGRES_PASSWORD": "pw",
    "KEYCLOAK_ISSUER": "https://auth.example/realms/gradian",
    "KEYCLOAK_CORE_CLIENT_SECRET": "secret",
    "FRONTEND_URL": "https://gradian.example",
}


def run_manage(*args: str, **overrides: str | None) -> subprocess.CompletedProcess[str]:
    environment = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "VIRTUAL_ENV"}}
    environment["PYTHONPATH"] = str(CORE_DIR)
    environment.update({k: v for k, v in overrides.items() if v is not None})
    for key, value in overrides.items():
        if value is None:
            environment.pop(key, None)
    return subprocess.run(  # noqa: S603
        [sys.executable, "manage.py", *args],
        cwd=CORE_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


@covers("SYS-NFR-05")
class LocaleTests(SimpleTestCase):
    def test_persian_and_tehran(self) -> None:
        self.assertEqual(settings.LANGUAGE_CODE, "fa")
        self.assertEqual(settings.TIME_ZONE, "Asia/Tehran")


@covers("SYS-OPS-06")
class RequiredSettingsTests(SimpleTestCase):
    def test_missing_variable_is_named_in_the_error(self) -> None:
        with self.assertRaisesMessage(ImproperlyConfigured, "KEYCLOAK_CORE_CLIENT_SECRET"):
            env.require("KEYCLOAK_CORE_CLIENT_SECRET", environ={})

    def test_empty_counts_as_missing(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            env.require("FRONTEND_URL", environ={"FRONTEND_URL": ""})

    def test_startup_fails_naming_the_missing_variable(self) -> None:
        result = run_manage(
            "check", **{**PRODUCTION_ENV, "ENVIRONMENT": "development", "POSTGRES_PASSWORD": None}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_PASSWORD", result.stderr)

    def test_issuer_must_match_the_realm(self) -> None:
        result = run_manage(
            "check", **{**PRODUCTION_ENV, "KEYCLOAK_ISSUER": "https://auth.example/realms/other"}
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KEYCLOAK_ISSUER", result.stderr)


class DotenvTests(SimpleTestCase):
    def test_real_environment_wins_over_the_file(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "# comment\nA=from-file\nB=from-file\n\nbroken line\n", encoding="utf-8"
            )
            environ = {"A": "from-env"}
            env.load_dotenv(path, environ)
        self.assertEqual(environ, {"A": "from-env", "B": "from-file"})


@covers("SYS-NFR-01")
class ProductionHardeningTests(SimpleTestCase):
    def test_check_deploy_passes_for_production_settings(self) -> None:
        result = run_manage("check", "--deploy", "--fail-level", "WARNING", **PRODUCTION_ENV)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_debug_cannot_be_enabled_in_production(self) -> None:
        result = run_manage(
            "shell",
            "-c",
            "from django.conf import settings; print(settings.DEBUG)",
            **PRODUCTION_ENV,
            DJANGO_DEBUG="1",
        )
        self.assertEqual(result.stdout.strip().splitlines()[-1], "False", result.stderr)
