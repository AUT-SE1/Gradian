"""Base classes for fast tests: a fake key set and a stubbed Keycloak Admin API."""

from unittest.mock import patch

from django.core.cache import cache
from django.test import tag
from rest_framework.test import APITestCase

from gradian_keycloak.errors import KeycloakError
from gradian_testing.cases import FakeKeycloakMixin
from gradian_testing.fakes import FakeIdentityAdmin


class ApiTestCase(FakeKeycloakMixin, APITestCase):
    """Every request is validated against the fake key set; nothing touches the network."""

    def setUp(self) -> None:
        super().setUp()
        cache.clear()  # rate-limit counters
        self.idp = FakeIdentityAdmin()
        admin = patch("gradian_keycloak.admin_client.get_admin_client", return_value=self.idp)
        admin.start()
        self.addCleanup(admin.stop)


@tag("integration")
class IntegrationTestCase(APITestCase):
    """Base for tests that need the running stack (test plan 2.3). Fails, never skips."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from gradian_keycloak import realm

        try:
            realm.check_reachable()
        except KeycloakError as exc:
            raise AssertionError(
                "Keycloak is not reachable. Start the system first: make start"
            ) from exc
