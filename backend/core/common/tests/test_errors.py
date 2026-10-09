"""One error shape, English codes (DES-API-01, DES-XC-03)."""

from typing import Any
from unittest.mock import patch

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from django.test import Client

from gradian_auth.drf import exception_handler
from gradian_testing.covers import covers
from gradian_testing.tokens import make_token
from tests.helpers.base import ApiTestCase


@covers("SYS-NFR-05")
class ErrorShapeTests(ApiTestCase):
    def assert_shape(self, response: Any, status: int, code: str) -> dict[str, Any]:
        body: dict[str, Any] = response.json()
        self.assertEqual(response.status_code, status)
        self.assertEqual(set(body), {"code", "message", "details"})
        self.assertEqual(body["code"], code)
        self.assertRegex(code, r"^[a-z_]+$")  # codes are English
        return body

    def test_unauthenticated(self) -> None:
        self.assert_shape(self.client.get("/api/v1/me"), 401, "not_authenticated")

    def test_forbidden(self) -> None:
        response = self.get_as("/api/v1/me", roles=("student", "admin"))
        self.assert_shape(response, 403, "ambiguous_role")

    def test_unknown_url_is_json_404(self) -> None:
        self.assert_shape(self.client.get("/api/v1/nothing-here"), 404, "not_found")

    def test_django_404_and_permission_errors_keep_their_own_code(self) -> None:
        """Raised by `get_object_or_404` or Django code inside a view, not by DRF."""
        missing = exception_handler(Http404(), {})
        denied = exception_handler(DjangoPermissionDenied(), {})
        assert missing is not None and denied is not None
        self.assertEqual((missing.status_code, missing.data["code"]), (404, "not_found"))
        self.assertEqual((denied.status_code, denied.data["code"]), (403, "permission_denied"))

    def test_method_not_allowed(self) -> None:
        self.assert_shape(self.client.post("/api/v1/auth/config"), 405, "method_not_allowed")

    def test_bad_json_body(self) -> None:
        response = self.client.patch(
            "/api/v1/me",
            "{not json",
            content_type="application/json",
            **self.bearer(make_token()),
        )
        self.assert_shape(response, 400, "parse_error")

    def test_unexpected_error_is_json_500(self) -> None:
        client = Client(raise_request_exception=False)
        with patch("accounts.views.AuthConfigView.get", side_effect=RuntimeError("boom")):
            response = client.get("/api/v1/auth/config")
        self.assert_shape(response, 500, "server_error")
        self.assertNotIn("boom", response.content.decode())
