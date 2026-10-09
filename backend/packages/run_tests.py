#!/usr/bin/env python3
"""Run the tests of the Gradian packages with minimal Django settings, without Core.

    python packages/run_tests.py                      # every package
    python packages/run_tests.py gradian_auth.tests   # one package, or any test label

The packages must be installed (`pip install -e` each one). Run through `make test`, or by hand
inside any environment that has them.
"""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

DEFAULT_LABELS = ["gradian_keycloak.tests", "gradian_auth.tests", "gradian_testing.tests"]


def main(labels: list[str]) -> int:
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    settings.configure(
        SECRET_KEY="packages-tests-only",  # noqa: S106  # throwaway value for the test run
        DEBUG=False,
        USE_TZ=True,
        INSTALLED_APPS=[],
        DATABASES={},
        ALLOWED_HOSTS=["testserver"],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        LOGGING={
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {"null": {"class": "logging.NullHandler"}},
            "root": {"handlers": ["null"], "level": "INFO"},
        },
    )
    django.setup()
    runner = get_runner(settings)(verbosity=1)
    failures = runner.run_tests(labels or DEFAULT_LABELS)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
