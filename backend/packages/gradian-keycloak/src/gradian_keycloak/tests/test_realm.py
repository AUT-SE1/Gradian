from unittest.mock import patch

import requests

from gradian_keycloak.errors import KeycloakError
from gradian_keycloak.realm import check_reachable, fetch_jwks
from gradian_keycloak.tests.base import FakeResponse, KeycloakSettingsTestCase


class FetchJwksTests(KeycloakSettingsTestCase):
    def test_returns_the_key_document_from_the_internal_address(self) -> None:
        document = {"keys": [{"kid": "k1"}]}
        with patch("requests.get", return_value=FakeResponse(200, document)) as get:
            self.assertEqual(fetch_jwks(), document)
        self.assertEqual(
            get.call_args.args[0],
            "http://keycloak.internal.test/realms/gradian/protocol/openid-connect/certs",
        )
        self.assertEqual(get.call_args.kwargs["timeout"], 5.0)

    def test_every_failure_is_a_keycloak_error(self) -> None:
        cases = {
            "unreachable": requests.ConnectionError("down"),
            "server error": FakeResponse(503, {}),
            "not json": FakeResponse(200, text="<html>"),
            "not an object": FakeResponse(200, ["keys"]),
        }
        for name, outcome in cases.items():
            with self.subTest(name=name):
                patcher = (
                    patch("requests.get", side_effect=outcome)
                    if isinstance(outcome, Exception)
                    else patch("requests.get", return_value=outcome)
                )
                with patcher, self.assertRaises(KeycloakError):
                    fetch_jwks()

    def test_check_reachable_fails_with_the_same_error(self) -> None:
        with (
            patch("requests.get", side_effect=requests.Timeout()),
            self.assertRaises(KeycloakError),
        ):
            check_reachable()
