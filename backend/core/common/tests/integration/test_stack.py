"""Needs the running stack: `make itest` starts it and runs these."""

import requests
from django.conf import settings

from tests.helpers.base import IntegrationTestCase
from tests.helpers.covers import covers


@covers("SYS-OPS-01", "SYS-NFR-03")
class StackTests(IntegrationTestCase):
    def test_ready_endpoint_is_healthy_against_the_real_keycloak(self) -> None:
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200, response.content)

    def test_keycloak_issuer_matches_what_core_expects(self) -> None:
        """If KC_HOSTNAME and KEYCLOAK_ISSUER disagree, every token would be refused."""
        realm_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
        url = f"{realm_url}/.well-known/openid-configuration"
        document = requests.get(url, timeout=5).json()
        self.assertEqual(document["issuer"], settings.KEYCLOAK_ISSUER)
