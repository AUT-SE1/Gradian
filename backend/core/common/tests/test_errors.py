"""One error shape, Persian messages, English codes (DES-API-01, DES-XC-03)."""

import re
from typing import Any
from unittest.mock import patch

from django.test import Client, SimpleTestCase

from common.exceptions import MESSAGES
from tests.helpers.base import ApiTestCase
from tests.helpers.covers import covers
from tests.helpers.tokens import make_token

PERSIAN = re.compile(r"[\u0600-\u06FF]")


@covers("SYS-NFR-05")
class ErrorShapeTests(ApiTestCase):
    def assert_shape(self, response: Any, status: int, code: str) -> dict[str, Any]:
        body: dict[str, Any] = response.json()
        self.assertEqual(response.status_code, status)
        self.assertEqual(set(body), {"code", "message", "details"})
        self.assertEqual(body["code"], code)
        self.assertRegex(code, r"^[a-z_]+$")  # codes are English
        self.assertRegex(str(body["message"]), PERSIAN)  # messages are Persian
        return body

    def test_unauthenticated(self) -> None:
        self.assert_shape(self.client.get("/api/v1/me"), 401, "not_authenticated")

    def test_forbidden(self) -> None:
        self.get_as("/api/v1/me", roles=())
        response = self.get_as("/api/v1/me", roles=())
        self.assert_shape(response, 403, "role_not_assigned")

    def test_unknown_url_is_json_404(self) -> None:
        self.assert_shape(self.client.get("/api/v1/nothing-here"), 404, "not_found")

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


@covers("SYS-NFR-05")
class MessagesTests(SimpleTestCase):
    def test_every_message_is_persian(self) -> None:
        for code, message in MESSAGES.items():
            with self.subTest(code=code):
                self.assertRegex(message, PERSIAN)
