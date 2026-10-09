"""Plain Django integration: the middleware and the decorators (DES-AUTH-01, DES-AUTH-03)."""

from typing import Any

from django.test import override_settings

from gradian_auth import context
from gradian_auth.decorators import require_user
from gradian_testing.cases import AuthTestCase
from gradian_testing.covers import covers
from gradian_testing.tokens import OTHER_PRIVATE_KEY, make_token, service_token

MIDDLEWARE = ["gradian_auth.middleware.KeycloakAuthMiddleware"]


@override_settings(ROOT_URLCONF="gradian_auth.tests.urls", MIDDLEWARE=MIDDLEWARE)
class MiddlewareTestCase(AuthTestCase):
    def call(self, path: str, token: str | None = None) -> Any:
        extra = self.bearer(token) if token else {}
        return self.client.get(path, **extra)


@covers("SYS-ACC-01")
class MiddlewareTests(MiddlewareTestCase):
    def test_no_header_means_anonymous_and_the_view_decides(self) -> None:
        response = self.call("/open")
        self.assertEqual((response.status_code, response.json()), (200, {"kind": "anonymous"}))

    def test_a_valid_person_token_gives_the_view_the_principal(self) -> None:
        body = self.call("/open", make_token(roles=("professor",))).json()
        self.assertEqual(
            body,
            {"kind": "user", "sub": "00000000-0000-4000-8000-000000000001", "panel": "professor"},
        )

    def test_a_valid_service_token_gives_the_view_a_service_principal(self) -> None:
        body = self.call("/open", service_token()).json()
        self.assertEqual(body, {"kind": "service", "client_id": "group-service-1"})

    def test_a_bad_token_is_refused_before_the_view_runs(self) -> None:
        for name, token in {
            "other key": make_token(key=OTHER_PRIVATE_KEY),
            "wrong audience": make_token(audience="group-9"),
            "expired": make_token(issued_at=1_700_000_000),
        }.items():
            with self.subTest(name=name):
                response = self.call("/open", token)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["code"], "invalid_token")
                self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_a_malformed_bearer_header_is_refused(self) -> None:
        response = self.client.get("/open", HTTP_AUTHORIZATION="Bearer a b")
        self.assertEqual((response.status_code, response.json()["code"]), (401, "invalid_token"))

    def test_another_scheme_is_anonymous(self) -> None:
        response = self.client.get("/open", HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")
        self.assertEqual(response.json(), {"kind": "anonymous"})

    def test_a_person_whose_identity_is_incomplete_is_refused_naming_the_fields(self) -> None:
        response = self.call("/open", make_token(omit=["email"]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "incomplete_identity")
        self.assertEqual(response.json()["details"], {"fields": ["email"]})

    def test_errors_have_the_shared_shape_with_a_persian_message(self) -> None:
        body = self.call("/open", "garbage").json()
        self.assertEqual(set(body), {"code", "message", "details"})
        self.assertRegex(body["message"], "[\u0600-\u06ff]")

    def test_keycloak_down_is_a_bad_gateway(self) -> None:
        from gradian_keycloak.errors import KeycloakError

        self.fetch_jwks.side_effect = KeycloakError("down")
        response = self.call("/open", make_token())
        self.assertEqual(
            (response.status_code, response.json()["code"]), (502, "identity_provider_unavailable")
        )

    def test_the_user_is_noted_for_the_log_lines_only_during_the_request(self) -> None:
        before = context.user_sub.get()
        self.call("/open", make_token())
        self.assertEqual(context.user_sub.get(), before)


class PublicPathTests(MiddlewareTestCase):
    def test_health_is_public_and_never_looks_at_the_token(self) -> None:
        self.assertEqual(self.call("/health", "garbage").status_code, 200)
        self.assertEqual(self.call("/health/deep", "garbage").status_code, 200)

    def test_other_paths_are_not_public(self) -> None:
        self.assertEqual(self.call("/open", "garbage").status_code, 401)

    def test_the_public_paths_are_configurable(self) -> None:
        with override_settings(GRADIAN_PUBLIC_PATHS=("/open",)):
            self.assertEqual(self.call("/open", "garbage").status_code, 200)
            self.assertEqual(self.call("/health", "garbage").status_code, 401)

    def test_a_prefix_only_matches_whole_path_segments(self) -> None:
        with override_settings(GRADIAN_PUBLIC_PATHS=("/op",)):
            self.assertEqual(self.call("/open", "garbage").status_code, 401)


@covers("SYS-ACC-02")
class DecoratorTests(MiddlewareTestCase):
    def test_a_signed_in_person_passes_require_user(self) -> None:
        self.assertEqual(self.call("/any", make_token()).status_code, 200)

    def test_no_token_is_401_not_authenticated_with_the_challenge_header(self) -> None:
        for path in ("/any", "/classes/3", "/service"):
            with self.subTest(path=path):
                response = self.call(path)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["code"], "not_authenticated")
                self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_roles_are_checked(self) -> None:
        for roles, expected in {
            ("student",): 200,
            ("professor",): 200,
            ("admin",): 403,
            ("consultant",): 403,
        }.items():
            with self.subTest(roles=roles):
                response = self.call(
                    "/classes/3", make_token(roles=roles, consultant_type="consultant")
                )
                self.assertEqual(response.status_code, expected)
                if expected == 403:
                    self.assertEqual(response.json()["code"], "permission_denied")

    def test_view_arguments_still_reach_the_view(self) -> None:
        self.assertEqual(self.call("/classes/42", make_token()).json()["number"], 42)

    def test_a_service_is_not_a_person_and_a_person_is_not_a_service(self) -> None:
        self.assertEqual(self.call("/any", service_token()).status_code, 403)
        self.assertEqual(self.call("/classes/1", service_token()).status_code, 403)
        self.assertEqual(self.call("/service", make_token()).status_code, 403)
        self.assertEqual(self.call("/service", service_token()).status_code, 200)

    def test_require_user_without_parentheses_is_caught_early(self) -> None:
        with self.assertRaises(TypeError):
            require_user(lambda request: None)  # type: ignore[arg-type]  # the mistake under test


@override_settings(ROOT_URLCONF="gradian_auth.tests.urls", MIDDLEWARE=[])
class WithoutMiddlewareTests(AuthTestCase):
    def test_every_guarded_view_stays_closed(self) -> None:
        for path in ("/any", "/classes/1", "/service"):
            with self.subTest(path=path):
                response = self.client.get(path, **self.bearer(make_token()))
                self.assertEqual(response.status_code, 401)
