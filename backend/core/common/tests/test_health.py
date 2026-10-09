from unittest.mock import patch

from django.test import TestCase

from gradian_keycloak.errors import KeycloakError
from gradian_testing.covers import covers


@covers("SYS-NFR-03")
class HealthTests(TestCase):
    def test_live_needs_nothing(self) -> None:
        response = self.client.get("/health/live")
        self.assertEqual((response.status_code, response.json()), (200, {"status": "ok"}))

    def test_ready_when_database_and_keycloak_are_up(self) -> None:
        with patch("gradian_keycloak.realm.fetch_jwks", return_value={"keys": []}):
            response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"database": "ok", "keycloak": "ok"})

    def test_ready_fails_when_keycloak_is_down(self) -> None:
        with patch("gradian_keycloak.realm.fetch_jwks", side_effect=KeycloakError("down")):
            response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"], {"database": "ok", "keycloak": "error"})

    def test_ready_fails_when_the_database_is_down(self) -> None:
        with (
            patch("gradian_keycloak.realm.fetch_jwks", return_value={"keys": []}),
            patch("common.health.connection.cursor", side_effect=RuntimeError("db down")),
        ):
            response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["database"], "error")
        self.assertNotIn("db down", response.content.decode())
