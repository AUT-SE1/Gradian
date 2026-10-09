"""Django REST Framework integration: authentication, permissions, error handler."""

from typing import Any
from unittest.mock import patch

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.test import override_settings
from rest_framework.test import APISimpleTestCase

from gradian_auth.drf import exception_handler
from gradian_testing.cases import FakeKeycloakMixin
from gradian_testing.covers import covers
from gradian_testing.settings import KEYCLOAK_TEST_SETTINGS
from gradian_testing.tokens import OTHER_PRIVATE_KEY, make_token, service_token

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["gradian_auth.drf.KeycloakBearerAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "gradian_auth.drf.exception_handler",
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}


@override_settings(
    ROOT_URLCONF="gradian_auth.tests.urls", REST_FRAMEWORK=REST_FRAMEWORK, **KEYCLOAK_TEST_SETTINGS
)
class DrfTestCase(FakeKeycloakMixin, APISimpleTestCase):
    def assert_error(self, response: Any, status: int, code: str) -> dict[str, Any]:
        body: dict[str, Any] = response.json()
        self.assertEqual(response.status_code, status, body)
        self.assertEqual(set(body), {"code", "message", "details"})
        self.assertEqual(body["code"], code)
        return body


@covers("SYS-ACC-01")
class AuthenticationTests(DrfTestCase):
    def test_a_valid_token_authenticates_the_person(self) -> None:
        response = self.get_as("/drf/who", roles=("professor",))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["panel"], "professor")

    def test_no_header_is_401_not_authenticated_with_the_challenge_header(self) -> None:
        response = self.client.get("/drf/who")
        self.assert_error(response, 401, "not_authenticated")
        self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_another_scheme_is_treated_as_anonymous(self) -> None:
        response = self.client.get("/drf/who", HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")
        self.assert_error(response, 401, "not_authenticated")

    def test_a_bad_token_is_401_invalid_token_with_the_challenge_header(self) -> None:
        for name, token in {
            "other key": make_token(key=OTHER_PRIVATE_KEY),
            "wrong audience": make_token(audience="group-9"),
            "not a jwt": "not-a-jwt",
        }.items():
            with self.subTest(name=name):
                response = self.client.get("/drf/who", **self.bearer(token))
                self.assert_error(response, 401, "invalid_token")
                self.assertIn("Bearer", response["WWW-Authenticate"])

    def test_malformed_bearer_headers_are_refused(self) -> None:
        for header in ("Bearer", "Bearer a b", "Bearer \u00e9"):
            with self.subTest(header=header):
                response = self.client.get("/drf/who", HTTP_AUTHORIZATION=header)
                self.assertEqual(response.status_code, 401)

    def test_an_ambiguous_role_is_403_with_the_roles_named(self) -> None:
        response = self.get_as("/drf/who", roles=("student", "admin"))
        body = self.assert_error(response, 403, "ambiguous_role")
        self.assertEqual(body["details"], {"roles": ["admin", "student"]})


@covers("SYS-ACC-02")
class PermissionTests(DrfTestCase):
    def test_a_panel_role_permission_allows_only_that_role(self) -> None:
        self.assertEqual(self.get_as("/drf/admin", roles=("admin",)).status_code, 200)
        self.assert_error(self.get_as("/drf/admin", roles=("student",)), 403, "permission_denied")
        self.assert_error(self.client.get("/drf/admin"), 401, "not_authenticated")

    def test_a_service_is_not_a_panel_user(self) -> None:
        response = self.client.get("/drf/who", **self.bearer(service_token()))
        self.assert_error(response, 403, "permission_denied")

    def test_the_platform_service_permission_allows_only_services(self) -> None:
        self.assertEqual(
            self.client.get("/drf/service", **self.bearer(service_token())).status_code, 200
        )
        self.assert_error(self.get_as("/drf/service", roles=("admin",)), 403, "permission_denied")
        self.assert_error(self.client.get("/drf/service"), 401, "not_authenticated")


@covers("SYS-NFR-05")
class ExceptionHandlerTests(DrfTestCase):
    def test_an_api_error_keeps_its_status_code_and_details(self) -> None:
        response = self.get_as("/drf/fails/api")
        body = self.assert_error(response, 418, "server_error")
        self.assertEqual(body["details"], {"why": "test"})

    def test_throttling_names_the_wait(self) -> None:
        body = self.assert_error(self.get_as("/drf/fails/throttled"), 429, "throttled")
        self.assertEqual(body["details"], {"retry_after_seconds": 7})

    def test_validation_errors_map_fields_to_problems(self) -> None:
        body = self.assert_error(self.get_as("/drf/fails/invalid"), 400, "validation_error")
        self.assertEqual(list(body["details"]), ["name"])

    def test_django_errors_raised_in_a_view_get_the_same_shape(self) -> None:
        cases: dict[str, tuple[Exception, int, str]] = {
            "404": (Http404(), 404, "not_found"),
            "permission": (DjangoPermissionDenied(), 403, "permission_denied"),
            "validation": (DjangoValidationError(["bad"]), 400, "validation_error"),
        }
        for name, (exc, status, code) in cases.items():
            with self.subTest(name=name):
                response = exception_handler(exc, {})
                assert response is not None
                self.assertEqual((response.status_code, response.data["code"]), (status, code))

    def test_an_unexpected_error_is_left_to_the_host(self) -> None:
        self.assertIsNone(exception_handler(RuntimeError("boom"), {}))

    def test_our_errors_roll_the_request_transaction_back_like_drfs_own(self) -> None:
        with patch("rest_framework.views.set_rollback") as rollback:
            self.get_as("/drf/fails/api")
        rollback.assert_called_once()
