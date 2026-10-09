"""Shared pieces of the gradian-keycloak tests."""

import json
from typing import Any

import requests
from django.test import SimpleTestCase, override_settings

KEYCLOAK_SETTINGS = {
    "KEYCLOAK_PUBLIC_URL": "http://keycloak.public.test",
    "KEYCLOAK_URL": "http://keycloak.internal.test",
    "KEYCLOAK_CLIENT_ID": "svc-client",
    "KEYCLOAK_CLIENT_SECRET": "svc-secret",
}


@override_settings(**KEYCLOAK_SETTINGS)
class KeycloakSettingsTestCase(SimpleTestCase):
    pass


class FakeResponse:
    def __init__(
        self,
        status: int = 200,
        body: Any = None,
        headers: dict[str, str] | None = None,
        text: str | None = None,
    ) -> None:
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self.content = (
            text if text is not None else json.dumps(body) if body is not None else ""
        ).encode()

    def json(self) -> Any:
        if not self.content:
            raise ValueError("no body")
        return json.loads(self.content)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class StubTokens:
    """Stands in for ServiceTokenClient where the token itself is not under test."""

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer stub-token"}
