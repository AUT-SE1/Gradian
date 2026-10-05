"""Signing-key cache behaviour (SYS-NFR-03, DES-AUTH-01)."""

from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.exceptions import AuthenticationFailed

from accounts.errors import IdentityProviderUnavailableError
from accounts.jwks import MIN_REFRESH_INTERVAL_SECONDS, JwksCache
from accounts.keycloak import KeycloakError
from tests.helpers.covers import covers
from tests.helpers.tokens import KEY_ID, OTHER_PRIVATE_KEY, jwks_document


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@covers("SYS-NFR-03")
class JwksCacheTests(SimpleTestCase):
    def test_cached_key_survives_a_failing_refresh(self) -> None:
        cache = JwksCache()
        with patch("accounts.keycloak.fetch_jwks", return_value=jwks_document()):
            first = cache.get_key(KEY_ID)
        with patch("accounts.keycloak.fetch_jwks", side_effect=KeycloakError("down")) as fetch:
            self.assertIs(cache.get_key(KEY_ID), first)
        fetch.assert_not_called()

    def test_no_keys_and_keycloak_down_is_a_bad_gateway(self) -> None:
        with (
            patch("accounts.keycloak.fetch_jwks", side_effect=KeycloakError("down")),
            self.assertRaises(IdentityProviderUnavailableError),
        ):
            JwksCache().get_key(KEY_ID)

    def test_unknown_kid_triggers_one_refresh_then_picks_up_the_new_key(self) -> None:
        clock = Clock()
        cache = JwksCache(clock)
        with patch("accounts.keycloak.fetch_jwks", return_value=jwks_document()):
            cache.get_key(KEY_ID)
        clock.now += MIN_REFRESH_INTERVAL_SECONDS + 1
        rotated = jwks_document((KEY_ID, OTHER_PRIVATE_KEY), ("new-kid", OTHER_PRIVATE_KEY))
        with patch("accounts.keycloak.fetch_jwks", return_value=rotated) as fetch:
            self.assertIsNotNone(cache.get_key("new-kid"))
        fetch.assert_called_once()

    def test_random_kids_cannot_cause_a_fetch_storm(self) -> None:
        clock = Clock()
        cache = JwksCache(clock)
        with patch("accounts.keycloak.fetch_jwks", return_value=jwks_document()):
            cache.get_key(KEY_ID)
            clock.now += MIN_REFRESH_INTERVAL_SECONDS + 1
            with self.assertRaises(AuthenticationFailed):
                cache.get_key("nope-1")  # refreshes once, still unknown
        with patch("accounts.keycloak.fetch_jwks") as fetch:
            clock.now += 1
            with self.assertRaises(AuthenticationFailed):
                cache.get_key("nope-2")  # too soon: refused without a fetch
        fetch.assert_not_called()

    def test_missing_kid_is_refused(self) -> None:
        with self.assertRaises(AuthenticationFailed):
            JwksCache().get_key(None)
