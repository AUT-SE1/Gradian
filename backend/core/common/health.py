"""Liveness and readiness (DES-API-06). Failure details go to the log, not to the response."""

import logging
from typing import Literal

from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger("gradian.health")


def live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def _database() -> Literal["ok", "error"]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "ok"
    except Exception:
        logger.exception("readiness: database check failed")
        return "error"


def _keycloak() -> Literal["ok", "error"]:
    from accounts import keycloak

    try:
        keycloak.check_reachable()
        return "ok"
    except keycloak.KeycloakError:
        logger.warning("readiness: Keycloak is not reachable")
        return "error"


def ready(request: HttpRequest) -> JsonResponse:
    checks = {"database": _database(), "keycloak": _keycloak()}
    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "unavailable", "checks": checks},
        status=200 if healthy else 503,
    )
