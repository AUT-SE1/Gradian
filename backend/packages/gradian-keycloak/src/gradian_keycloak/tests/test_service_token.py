from unittest.mock import patch

import requests
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from gradian_keycloak.errors import KeycloakError
from gradian_keycloak.service_token import EXPIRY_MARGIN_SECONDS, ServiceTokenClient
from gradian_keycloak.tests.base import FakeResponse, KeycloakSettingsTestCase


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def token_response(token: str = "t1", expires_in: int = 300) -> FakeResponse:
    return FakeResponse(200, {"access_token": token, "expires_in": expires_in})


class ServiceTokenTests(KeycloakSettingsTestCase):
    def test_asks_for_the_clients_own_token_with_client_credentials(self) -> None:
        with patch("requests.post", return_value=token_response()) as post:
            token = ServiceTokenClient().access_token()
        self.assertEqual(token, "t1")
        self.assertEqual(
            post.call_args.args[0],
            "http://keycloak.internal.test/realms/gradian/protocol/openid-connect/token",
        )
        self.assertEqual(
            post.call_args.kwargs["data"],
            {
                "grant_type": "client_credentials",
                "client_id": "svc-client",
                "client_secret": "svc-secret",
            },
        )

    def test_the_token_is_reused_until_shortly_before_it_expires(self) -> None:
        clock = Clock()
        client = ServiceTokenClient(clock)
        with patch("requests.post", side_effect=[token_response("a"), token_response("b")]) as post:
            self.assertEqual(client.access_token(), "a")
            clock.now += 300 - EXPIRY_MARGIN_SECONDS - 1
            self.assertEqual(client.access_token(), "a")
            clock.now += 2
            self.assertEqual(client.access_token(), "b")
        self.assertEqual(post.call_count, 2)

    def test_clear_forces_a_new_token(self) -> None:
        client = ServiceTokenClient()
        with patch("requests.post", side_effect=[token_response("a"), token_response("b")]):
            client.access_token()
            client.clear()
            self.assertEqual(client.access_token(), "b")

    def test_a_failed_fetch_is_a_keycloak_error_and_the_next_call_tries_again(self) -> None:
        client = ServiceTokenClient()
        failures = [
            requests.ConnectionError("down"),
            FakeResponse(401, {}),
            FakeResponse(200, {"no_token": True}),
            FakeResponse(200, text="not json"),
        ]
        for failure in failures:
            with self.subTest(failure=repr(failure)):
                patcher = (
                    patch("requests.post", side_effect=failure)
                    if isinstance(failure, Exception)
                    else patch("requests.post", return_value=failure)
                )
                with patcher, self.assertRaises(KeycloakError):
                    client.access_token()
        with patch("requests.post", return_value=token_response("ok")):
            self.assertEqual(client.access_token(), "ok")

    def test_without_a_client_secret_it_says_which_setting_is_missing(self) -> None:
        with (
            override_settings(KEYCLOAK_CLIENT_SECRET=""),
            self.assertRaisesMessage(ImproperlyConfigured, "KEYCLOAK_CLIENT_SECRET"),
        ):
            ServiceTokenClient().access_token()

    def test_auth_headers_carry_the_bearer_token(self) -> None:
        with patch("requests.post", return_value=token_response("abc")):
            self.assertEqual(ServiceTokenClient().auth_headers(), {"Authorization": "Bearer abc"})
