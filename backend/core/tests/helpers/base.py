"""Base classes for fast tests: a fake key set and a stubbed Keycloak Admin API."""

from collections.abc import Mapping
from typing import Any
from unittest.mock import patch

from django.core.cache import cache
from django.test import tag
from rest_framework.test import APITestCase

from accounts.jwks import jwks_cache
from accounts.keycloak import KeycloakError, KeycloakUser
from tests.helpers.tokens import jwks_document, make_token


class FakeIdentityAdmin:
    """Records calls, and can be told to fail (DES-ID-05, DES-ID-04 without Keycloak)."""

    def __init__(self) -> None:
        self.updates: list[tuple[str, dict[str, str]]] = []
        self.users: list[KeycloakUser] = []
        self.fail_with: KeycloakError | None = None

    def update_user(self, sub: str, changes: Mapping[str, str]) -> None:
        if self.fail_with:
            raise self.fail_with
        self.updates.append((sub, dict(changes)))

    def list_panel_users(self) -> list[KeycloakUser]:
        if self.fail_with:
            raise self.fail_with
        return list(self.users)


class ApiTestCase(APITestCase):
    """Every request is validated against the fake key set; nothing touches the network."""

    def setUp(self) -> None:
        super().setUp()
        jwks_cache.clear()
        cache.clear()  # rate-limit counters
        self.addCleanup(jwks_cache.clear)
        self.jwks = jwks_document()
        self.idp = FakeIdentityAdmin()
        fetch = patch("accounts.keycloak.fetch_jwks", side_effect=lambda: self.jwks)
        admin = patch("accounts.keycloak.get_admin_client", return_value=self.idp)
        self.fetch_jwks = fetch.start()
        admin.start()
        self.addCleanup(fetch.stop)
        self.addCleanup(admin.stop)

    @staticmethod
    def bearer(token: str) -> dict[str, Any]:
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def get_as(self, path: str, **token_kwargs: Any) -> Any:
        return self.client.get(path, **self.bearer(make_token(**token_kwargs)))


@tag("integration")
class IntegrationTestCase(APITestCase):
    """Base for tests that need the running stack (test plan 2.3). Fails, never skips."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from accounts import keycloak

        try:
            keycloak.check_reachable()
        except KeycloakError as exc:
            raise AssertionError(
                "Keycloak is not reachable. Start the stack first: make up bootstrap"
            ) from exc
