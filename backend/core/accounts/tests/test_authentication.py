"""Token validation and profile provisioning through the API (DES-AUTH-01 to DES-AUTH-04)."""

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from accounts.models import Profile
from gradian_keycloak.errors import KeycloakError
from gradian_testing.covers import covers
from gradian_testing.tokens import OTHER_PRIVATE_KEY, make_token
from tests.helpers.base import ApiTestCase

ME = "/api/v1/me"
SUB = uuid.UUID("00000000-0000-4000-8000-000000000001")


def tamper(token: str, **changes: Any) -> str:
    """Re-encode the payload with changed claims but keep the original signature."""
    header, payload, signature = token.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    claims.update(changes)
    new = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{new}.{signature}"


@covers("SYS-ACC-01")
class TokenValidationTests(ApiTestCase):
    def assert_invalid(self, token: str) -> None:
        response = self.client.get(ME, **self.bearer(token))
        self.assertEqual(response.status_code, 401, response.content)
        self.assertEqual(response.json()["code"], "invalid_token")
        self.assertIn("Bearer", response["WWW-Authenticate"])
        self.assertFalse(Profile.objects.exists())

    def test_valid_token_is_accepted(self) -> None:
        self.assertEqual(self.client.get(ME, **self.bearer(make_token())).status_code, 200)

    def test_no_header_is_401_not_authenticated(self) -> None:
        response = self.client.get(ME)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "not_authenticated")

    def test_other_schemes_are_treated_as_anonymous(self) -> None:
        response = self.client.get(ME, HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")
        self.assertEqual(response.status_code, 401)

    def test_malformed_bearer_headers(self) -> None:
        for header in ["Bearer", "Bearer a b", "Bearer not-a-jwt", "Bearer \u00e9"]:
            with self.subTest(header=header):
                response = self.client.get(ME, HTTP_AUTHORIZATION=header)
                self.assertEqual(response.status_code, 401)

    def test_wrong_issuer(self) -> None:
        self.assert_invalid(make_token(issuer="http://evil.test/realms/gradian"))

    def test_wrong_audience(self) -> None:
        self.assert_invalid(make_token(audience="some-other-client"))

    def test_audience_list_containing_core_is_accepted(self) -> None:
        token = make_token(audience=["account", "gradian-core"])
        self.assertEqual(self.client.get(ME, **self.bearer(token)).status_code, 200)

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


@covers("SYS-AUTH-07")
class RoleResolutionTests(ApiTestCase):
    def test_no_panel_role_means_student_and_the_role_is_granted_in_keycloak(self) -> None:
        response = self.get_as(ME, roles=())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["panel"], "student")
        self.assertEqual(Profile.objects.get().role, "student")
        self.assertEqual(self.idp.granted, [("00000000-0000-4000-8000-000000000001", "student")])
        self.get_as(ME, roles=())
        self.assertEqual(len(self.idp.granted), 1)  # only on first sight

    def test_two_panel_roles(self) -> None:
        response = self.get_as(ME, roles=("student", "admin"))
        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(body["code"], "ambiguous_role")
        self.assertEqual(body["details"], {"roles": ["admin", "student"]})

    def test_offline_access_alone_is_not_a_panel_role(self) -> None:
        self.assertEqual(self.get_as(ME, roles=()).json()["panel"], "student")

    def test_service_role_together_with_a_panel_role_is_refused(self) -> None:
        response = self.get_as(ME, roles=("service", "admin"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "ambiguous_role")


@covers("SYS-ID-02")
class ProfileProvisioningTests(ApiTestCase):
    def test_first_request_creates_the_profile_from_claims(self) -> None:
        self.assertEqual(self.get_as(ME).status_code, 200)
        profile = Profile.objects.get(sub=SUB)
        self.assertEqual(profile.mobile, "09120000001")
        self.assertEqual(profile.email, "student.1.1@gradian.test")
        self.assertEqual((profile.first_name, profile.last_name), ("علی", "رضایی"))
        self.assertEqual(profile.role, "student")
        self.assertTrue(profile.is_active)

    def test_persian_digits_in_the_mobile_claim_are_normalized(self) -> None:
        self.get_as(ME, mobile="+98۹۱۲۰۰۰۰۰۰۱")
        self.assertEqual(Profile.objects.get(sub=SUB).mobile, "09120000001")

    def test_changed_claims_update_the_cache_in_the_same_request(self) -> None:
        self.get_as(ME)
        response = self.get_as(ME, email="new.address@gradian.test", last_name="کریمی")
        self.assertEqual(response.json()["email"], "new.address@gradian.test")
        profile = Profile.objects.get(sub=SUB)
        self.assertEqual(profile.email, "new.address@gradian.test")
        self.assertEqual(profile.last_name, "کریمی")

    def test_role_change_is_picked_up(self) -> None:
        self.get_as(ME)
        self.assertEqual(self.get_as(ME, roles=("professor",)).json()["panel"], "professor")
        self.assertEqual(Profile.objects.get(sub=SUB).role, "professor")

    def test_missing_identity_claim_is_403_and_creates_nothing(self) -> None:
        for claim in ("email", "given_name", "family_name", "preferred_username"):
            with self.subTest(claim=claim):
                response = self.get_as(ME, omit=[claim])
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["code"], "incomplete_identity")
                self.assertFalse(Profile.objects.exists())

    def test_consultant_without_a_type_is_incomplete(self) -> None:
        response = self.get_as(ME, roles=("consultant",))
        self.assertEqual(response.json()["code"], "incomplete_identity")
        self.assertEqual(
            self.get_as(ME, roles=("consultant",), consultant_type="top_ranker").status_code, 200
        )

    def test_email_already_used_by_another_user_is_a_conflict(self) -> None:
        self.get_as(ME)
        other = make_token(sub=uuid.uuid4(), mobile="09120000002")
        response = self.client.get(ME, **self.bearer(other))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "identity_conflict")

    def test_an_older_token_does_not_undo_a_newer_cache(self) -> None:
        """After PATCH /me the user's still-valid token carries the old email."""
        self.get_as(ME)
        Profile.objects.filter(sub=SUB).update(
            email="edited@gradian.test", identity_synced_at=timezone.now()
        )
        old_token = make_token(
            issued_at=int((datetime.now(UTC) - timedelta(minutes=5)).timestamp())
        )
        self.client.get(ME, **self.bearer(old_token))
        self.assertEqual(Profile.objects.get(sub=SUB).email, "edited@gradian.test")
        fresh = make_token(email="edited@gradian.test")
        self.assertEqual(self.client.get(ME, **self.bearer(fresh)).status_code, 200)


@covers("SYS-AUTH-08")
class DisabledAccountTests(ApiTestCase):
    def test_inactive_profile_is_refused_even_with_a_valid_token(self) -> None:
        self.get_as(ME)
        Profile.objects.filter(sub=SUB).update(is_active=False)
        response = self.get_as(ME)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "account_disabled")


@covers("SYS-NFR-03")
class KeycloakOutageTests(ApiTestCase):
    def test_a_valid_token_keeps_working_when_the_key_fetch_starts_failing(self) -> None:
        self.assertEqual(self.get_as(ME).status_code, 200)
        self.fetch_jwks.side_effect = KeycloakError("down")
        self.assertEqual(self.get_as(ME).status_code, 200)

    def test_first_ever_request_with_keycloak_down_is_502(self) -> None:
        self.fetch_jwks.side_effect = KeycloakError("down")
        response = self.get_as(ME)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "identity_provider_unavailable")


class QueryBudgetTests(ApiTestCase):
    def test_an_unchanged_request_is_one_read_and_no_writes(self) -> None:
        self.get_as(ME)  # create
        with CaptureQueriesContext(connection) as queries:
            self.get_as(ME)
        statements = [q["sql"].split()[0].upper() for q in queries.captured_queries]
        self.assertEqual(statements.count("SELECT"), 1, statements)
        self.assertFalse({"INSERT", "UPDATE", "DELETE"} & set(statements), statements)


@override_settings(PUBLIC_RATE_LIMIT="2/min")
@covers("SYS-NFR-01")
class PublicRateLimitTests(ApiTestCase):
    def test_public_endpoint_returns_429_past_the_limit(self) -> None:
        statuses = [self.client.get("/api/v1/auth/config").status_code for _ in range(3)]
        self.assertEqual(statuses, [200, 200, 429])
        body = self.client.get("/api/v1/auth/config").json()
        self.assertEqual(body["code"], "throttled")
