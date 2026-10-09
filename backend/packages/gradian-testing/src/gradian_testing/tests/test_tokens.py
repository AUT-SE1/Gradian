import jwt
from django.test import SimpleTestCase

from gradian_auth.principals import ServicePrincipal, UserPrincipal, build_principal
from gradian_auth.tokens import validate_token
from gradian_keycloak.admin_client import NewUser
from gradian_keycloak.errors import KeycloakError
from gradian_testing.cases import AuthTestCase
from gradian_testing.covers import covers
from gradian_testing.fakes import FakeIdentityAdmin
from gradian_testing.tokens import KEY_ID, jwks_document, make_token, service_token


class MakeTokenTests(AuthTestCase):
    def test_the_default_token_is_a_valid_student_for_this_service(self) -> None:
        principal = build_principal(validate_token(make_token()))
        assert isinstance(principal, UserPrincipal)
        self.assertEqual(principal.panel, "student")

    def test_claims_can_be_changed_and_dropped(self) -> None:
        claims = jwt.decode(
            make_token(roles=("admin",), email=None, extra={"azp": "x"}),
            options={"verify_signature": False},
        )
        self.assertIn("admin", claims["realm_access"]["roles"])
        self.assertNotIn("email", claims)
        self.assertEqual(claims["azp"], "x")

    def test_a_service_token_has_the_service_role_and_no_person(self) -> None:
        principal = build_principal(validate_token(service_token()))
        self.assertIsInstance(principal, ServicePrincipal)

    def test_the_key_set_publishes_the_signing_key(self) -> None:
        self.assertEqual([key["kid"] for key in jwks_document()["keys"]], [KEY_ID])

    def test_the_mixin_replaces_the_key_fetch(self) -> None:
        validate_token(make_token())
        self.fetch_jwks.assert_called_once()

    def test_bearer_builds_the_header_for_the_test_client(self) -> None:
        self.assertEqual(self.bearer("abc"), {"HTTP_AUTHORIZATION": "Bearer abc"})


class FakeIdentityAdminTests(SimpleTestCase):
    def test_it_records_what_was_asked(self) -> None:
        fake = FakeIdentityAdmin()
        fake.update_user("u1", {"email": "a@x.test"})
        fake.grant_role("u1", "student")
        fake.set_enabled("u1", False)
        fake.set_panel_role("u1", "admin", "")
        sub = fake.create_user(NewUser("09", "a@x.test", "a", "b", "pw", "student", ""))
        self.assertEqual(fake.updates, [("u1", {"email": "a@x.test"})])
        self.assertEqual(fake.granted, [("u1", "student")])
        self.assertEqual(fake.enabled, [("u1", False)])
        self.assertEqual(fake.roles, [("u1", "admin", "")])
        self.assertEqual(len(fake.created), 1)
        self.assertTrue(sub)

    def test_it_can_be_told_to_fail_every_call(self) -> None:
        fake = FakeIdentityAdmin()
        fake.fail_with = KeycloakError("down", 502)
        calls = (
            lambda: fake.update_user("u", {}),
            lambda: fake.grant_role("u", "student"),
            lambda: fake.set_enabled("u", True),
            lambda: fake.set_panel_role("u", "admin", ""),
            lambda: fake.list_panel_users(),
        )
        for call in calls:
            with self.assertRaises(KeycloakError):
                call()


class CoversTests(SimpleTestCase):
    def test_it_tags_the_test_and_rejects_bad_ids(self) -> None:
        @covers("SYS-AUTH-02")
        class Tagged(SimpleTestCase):
            pass

        self.assertEqual(Tagged.tags, {"req-SYS-AUTH-02"})  # type: ignore[attr-defined]  # set by django.test.tag
        with self.assertRaises(ValueError):
            covers("auth-02")
