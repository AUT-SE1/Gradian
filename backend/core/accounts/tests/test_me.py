"""GET/PATCH /me, /auth/config and the access rules for what exists so far (AC-ACCESS)."""

import uuid
from typing import Any

from accounts.keycloak import KeycloakError
from accounts.models import Profile
from tests.helpers.base import ApiTestCase
from tests.helpers.covers import covers
from tests.helpers.tokens import make_token, service_token

ME = "/api/v1/me"
SUB = uuid.UUID("00000000-0000-4000-8000-000000000001")


@covers("SYS-AUTH-02")
class MePanelTests(ApiTestCase):
    def test_each_role_lands_on_its_own_panel(self) -> None:
        cases = {
            "student": {},
            "consultant": {"consultant_type": "consultant"},
            "professor": {},
            "admin": {},
        }
        for role, extra in cases.items():
            with self.subTest(role=role):
                Profile.objects.all().delete()
                body = self.get_as(ME, roles=(role,), **extra).json()
                self.assertEqual(body["panel"], role)
                self.assertEqual(body["home_path"], f"/{role}")

    def test_top_ranker_uses_the_consultant_panel(self) -> None:
        body = self.get_as(ME, roles=("consultant",), consultant_type="top_ranker").json()
        self.assertEqual((body["panel"], body["consultant_type"]), ("consultant", "top_ranker"))
        self.assertEqual(body["home_path"], "/consultant")

    def test_response_carries_identity_and_display_name(self) -> None:
        body = self.get_as(ME).json()
        self.assertEqual(body["sub"], str(SUB))
        self.assertEqual(body["mobile"], "09120000001")
        self.assertEqual(body["full_name"], "علی رضایی")


@covers("SYS-ACC-01")
class AccessMatrixTests(ApiTestCase):
    """The rows of the access matrix (test plan section 4) for endpoints that exist so far."""

    def test_me(self) -> None:
        self.assertEqual(self.client.get(ME).status_code, 401)  # anonymous
        for role, extra in [
            ("student", {}),
            ("consultant", {"consultant_type": "consultant"}),
            ("professor", {}),
            ("admin", {}),
        ]:
            with self.subTest(role=role):
                Profile.objects.all().delete()
                self.assertEqual(self.get_as(ME, roles=(role,), **extra).status_code, 200)
        service = self.client.get(ME, **self.bearer(service_token()))
        self.assertEqual(service.status_code, 403)
        self.assertEqual(service.json()["code"], "permission_denied")

    def test_auth_config_is_public(self) -> None:
        self.assertEqual(self.client.get("/api/v1/auth/config").status_code, 200)
        self.assertEqual(self.get_as("/api/v1/auth/config").status_code, 200)

    def test_a_broken_token_does_not_block_public_endpoints(self) -> None:
        response = self.client.get("/api/v1/auth/config", HTTP_AUTHORIZATION="Bearer garbage")
        self.assertEqual(response.status_code, 200)


@covers("SYS-AUTH-06")
class AuthConfigTests(ApiTestCase):
    def test_returns_what_the_frontend_needs_to_sign_in_and_out(self) -> None:
        body = self.client.get("/api/v1/auth/config").json()
        self.assertEqual(
            body,
            {
                "issuer": "http://keycloak.test/realms/gradian",
                "registration_endpoint": (
                    "http://keycloak.test/realms/gradian/protocol/openid-connect/registrations"
                ),
                "realm": "gradian",
                "client_id": "gradian-web",
                "end_session_url": "http://keycloak.test/realms/gradian/protocol/openid-connect/logout",
                "landing_url": "http://frontend.test/",
            },
        )


@covers("SYS-ID-05")
class PatchMeTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.get_as(ME)  # create the profile
        self.auth = self.bearer(make_token())

    def patch(self, data: dict[str, str]) -> Any:
        return self.client.patch(ME, data, format="json", **self.auth)

    def test_identity_change_goes_to_keycloak_first_then_the_cache(self) -> None:
        response = self.patch({"first_name": "محمد", "email": "New@Gradian.test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.idp.updates,
            [(str(SUB), {"first_name": "محمد", "email": "new@gradian.test"})],
        )
        profile = Profile.objects.get(sub=SUB)
        self.assertEqual((profile.first_name, profile.email), ("محمد", "new@gradian.test"))

    def test_keycloak_failure_is_502_and_nothing_changes(self) -> None:
        self.idp.fail_with = KeycloakError("down")
        response = self.patch({"first_name": "محمد"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "identity_provider_unavailable")
        self.assertEqual(Profile.objects.get(sub=SUB).first_name, "علی")

    def test_keycloak_conflict_is_409(self) -> None:
        self.idp.fail_with = KeycloakError("conflict", status=409)
        response = self.patch({"email": "taken@gradian.test"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Profile.objects.get(sub=SUB).email, "student.1.1@gradian.test")

    def test_core_owned_fields_do_not_touch_keycloak(self) -> None:
        response = self.patch({"bio": "دانشجوی سال اول", "field_of_study": "mathematics"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.idp.updates, [])
        profile = Profile.objects.get(sub=SUB)
        self.assertEqual((profile.bio, profile.field_of_study), ("دانشجوی سال اول", "mathematics"))

    def test_unchanged_identity_values_do_not_call_keycloak(self) -> None:
        self.patch({"first_name": "علی"})
        self.assertEqual(self.idp.updates, [])

    def test_validation_errors_use_the_error_shape(self) -> None:
        response = self.patch({"first_name": "<b>", "email": "nope", "bio": "x" * 501})
        body = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["code"], "validation_error")
        self.assertEqual(set(body["details"]), {"first_name", "email", "bio"})
        self.assertEqual(self.idp.updates, [])

    def test_empty_patch_is_rejected(self) -> None:
        self.assertEqual(self.patch({}).status_code, 400)

    def test_role_mobile_and_sub_cannot_be_changed(self) -> None:
        response = self.patch({"role": "admin", "mobile": "09999999999", "sub": str(uuid.uuid4())})
        self.assertEqual(response.status_code, 400)
        profile = Profile.objects.get(sub=SUB)
        self.assertEqual((profile.role, profile.mobile), ("student", "09120000001"))

    def test_patch_needs_authentication(self) -> None:
        self.assertEqual(self.client.patch(ME, {"bio": "x"}, format="json").status_code, 401)
