"""Token validation (DES-AUTH-01, SYS-ACC-01)."""

import base64
import json
from typing import Any

from django.test import override_settings

from gradian_auth.errors import IdentityProviderUnavailableError, InvalidTokenError
from gradian_auth.tokens import validate_token
from gradian_keycloak.errors import KeycloakError
from gradian_testing.cases import AuthTestCase
from gradian_testing.covers import covers
from gradian_testing.tokens import OTHER_PRIVATE_KEY, make_token


def tamper(token: str, **changes: Any) -> str:
    """Re-encode the payload with changed claims but keep the original signature."""
    header, payload, signature = token.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    claims.update(changes)
    new = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{new}.{signature}"


@covers("SYS-ACC-01")
class ValidateTokenTests(AuthTestCase):
    def assert_invalid(self, token: str) -> None:
        with self.assertRaises(InvalidTokenError):
            validate_token(token)

    def test_a_valid_token_gives_its_claims(self) -> None:
        claims = validate_token(make_token(roles=("professor",)))
        self.assertEqual(claims["sub"], "00000000-0000-4000-8000-000000000001")
        self.assertIn("professor", claims["realm_access"]["roles"])

    def test_not_a_jwt(self) -> None:
        self.assert_invalid("not-a-jwt")

    def test_wrong_issuer(self) -> None:
        self.assert_invalid(make_token(issuer="http://evil.test/realms/gradian"))

    def test_the_issuer_comes_from_the_public_address_not_the_internal_one(self) -> None:
        internal = "http://keycloak.internal.test/realms/gradian"
        self.assert_invalid(make_token(issuer=internal))

    def test_wrong_audience(self) -> None:
        self.assert_invalid(make_token(audience="some-other-client"))

    def test_audience_list_containing_this_service_is_accepted(self) -> None:
        validate_token(make_token(audience=["account", "gradian-core"]))

    def test_the_audience_is_this_services_own_client_id(self) -> None:
        token = make_token(audience=["gradian-core", "group-3"])
        with override_settings(KEYCLOAK_CLIENT_ID="group-3"):
            validate_token(token)
        with override_settings(KEYCLOAK_CLIENT_ID="group-4"), self.assertRaises(InvalidTokenError):
            validate_token(token)

    def test_an_explicit_audience_wins(self) -> None:
        validate_token(make_token(audience="group-7"), audience="group-7")

    def test_expired(self) -> None:
        self.assert_invalid(make_token(issued_at=1_700_000_000))

    def test_alg_none(self) -> None:
        self.assert_invalid(make_token(algorithm="none"))

    def test_hs256_signed_with_a_shared_secret_is_refused(self) -> None:
        shared_secret: Any = "shared-secret-of-sufficient-length-32b"  # wrong key type on purpose
        self.assert_invalid(make_token(algorithm="HS256", key=shared_secret))

    def test_signed_by_an_unknown_key(self) -> None:
        self.assert_invalid(make_token(key=OTHER_PRIVATE_KEY))

    def test_unknown_kid(self) -> None:
        self.assert_invalid(make_token(kid="not-published"))

    def test_missing_kid(self) -> None:
        self.assert_invalid(make_token(kid=None))

    def test_tampered_payload(self) -> None:
        token = make_token(roles=("student",))
        self.assert_invalid(tamper(token, realm_access={"roles": ["admin"]}))

    def test_missing_required_claims(self) -> None:
        for claim in ("exp", "iss", "aud", "sub"):
            with self.subTest(claim=claim):
                self.assert_invalid(make_token(omit=[claim]))

    def test_keycloak_down_on_first_use_is_a_bad_gateway(self) -> None:
        self.fetch_jwks.side_effect = KeycloakError("down")
        with self.assertRaises(IdentityProviderUnavailableError):
            validate_token(make_token())

    def test_a_valid_token_keeps_working_when_the_key_fetch_starts_failing(self) -> None:
        validate_token(make_token())
        self.fetch_jwks.side_effect = KeycloakError("down")
        validate_token(make_token())
