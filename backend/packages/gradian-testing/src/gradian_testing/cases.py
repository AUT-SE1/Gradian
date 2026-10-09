"""Test base classes: tokens are validated against a fake key set, nothing leaves the process."""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from gradian_auth.jwks import jwks_cache
from gradian_testing.settings import KEYCLOAK_TEST_SETTINGS
from gradian_testing.tokens import jwks_document, make_token


class FakeKeycloakMixin(unittest.TestCase):
    """Replaces the fetch of Keycloak's public keys with the test key set (`self.jwks`).

    Put it before the Django test case: `class T(FakeKeycloakMixin, TestCase)`.
    """

    client: Any
    jwks: dict[str, Any]
    fetch_jwks: MagicMock

    def setUp(self) -> None:
        super().setUp()
        jwks_cache.clear()
        self.addCleanup(jwks_cache.clear)
        self.jwks = jwks_document()
        fetch = patch("gradian_keycloak.realm.fetch_jwks", side_effect=lambda: self.jwks)
        self.fetch_jwks = fetch.start()
        self.addCleanup(fetch.stop)

    @staticmethod
    def bearer(token: str) -> dict[str, Any]:
        """Keyword arguments for `self.client.get(path, **self.bearer(token))`."""
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def get_as(self, path: str, **token_kwargs: Any) -> Any:
        """GET `path` with a token made from `make_token(**token_kwargs)`."""
        return self.client.get(path, **self.bearer(make_token(**token_kwargs)))


@override_settings(**KEYCLOAK_TEST_SETTINGS)
class AuthTestCase(FakeKeycloakMixin, SimpleTestCase):
    """For services that do not use a database or Django REST Framework.

    The Keycloak settings are those of `KEYCLOAK_TEST_SETTINGS`. To use other values, subclass
    and add your own `@override_settings`, which wins.
    """
