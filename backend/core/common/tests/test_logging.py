"""Structured logs, request ids, and no secrets in logs (DES-XC-01)."""

import json
import logging
from typing import Any

from django.test import SimpleTestCase

from common import context
from common.logging import JsonFormatter, RequestContextFilter
from tests.helpers.base import ApiTestCase
from tests.helpers.covers import covers
from tests.helpers.tokens import make_token

FORMATTER = JsonFormatter()


def render(record: logging.LogRecord) -> dict[str, Any]:
    RequestContextFilter().filter(record)
    parsed: dict[str, Any] = json.loads(FORMATTER.format(record))
    return parsed


def record(message: str, **extra: Any) -> logging.LogRecord:
    rec = logging.LogRecord("gradian.test", logging.INFO, __file__, 1, message, (), None)
    rec.__dict__.update(extra)
    return rec


@covers("SYS-NFR-01")
class RedactionTests(SimpleTestCase):
    def test_bearer_tokens_and_jwts_are_scrubbed_from_messages(self) -> None:
        token = make_token()
        out = render(record(f"header was Bearer {token} and raw {token}"))
        self.assertNotIn(token, json.dumps(out))
        self.assertNotIn("eyJ", json.dumps(out))

    def test_sensitive_extra_keys_are_redacted(self) -> None:
        out = render(record("x", password="hunter2", client_secret="s3cret", note="fine"))
        self.assertEqual(
            (out["password"], out["client_secret"], out["note"]),
            ("[redacted]", "[redacted]", "fine"),
        )


@covers("SYS-NFR-06")
class JsonFormatTests(SimpleTestCase):
    def test_lines_are_json_with_request_id_and_sub(self) -> None:
        rid = context.request_id.set("req-123")
        sub = context.user_sub.set("sub-456")
        try:
            out = render(record("hello", event="demo"))
        finally:
            context.request_id.reset(rid)
            context.user_sub.reset(sub)
        self.assertEqual(
            (out["message"], out["request_id"], out["sub"], out["event"], out["level"]),
            ("hello", "req-123", "sub-456", "demo", "INFO"),
        )


class RequestLoggingTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        # In production the handler's filter runs while the request is still in flight; assertLogs
        # has its own handler, so attach the same filter to the logger instead.
        log_filter = RequestContextFilter()
        for name in ("gradian.access", "gradian.accounts"):
            logging.getLogger(name).addFilter(log_filter)
            self.addCleanup(logging.getLogger(name).removeFilter, log_filter)

    @covers("SYS-NFR-06", "SYS-NFR-01")
    def test_profile_creation_and_access_are_logged_without_credentials(self) -> None:
        token = make_token()
        with self.assertLogs(level="INFO") as logs:
            response = self.client.get(
                "/api/v1/me", HTTP_X_REQUEST_ID="abc-123", **self.bearer(token)
            )
        events = [getattr(r, "event", None) for r in logs.records]
        self.assertIn("profile_created", events)
        access = next(r for r in logs.records if r.name == "gradian.access")
        self.assertEqual((access.status, access.path, access.method), (200, "/api/v1/me", "GET"))  # type: ignore[attr-defined]
        self.assertEqual(response["X-Request-ID"], "abc-123")
        self.assertEqual(access.sub, "00000000-0000-4000-8000-000000000001")  # type: ignore[attr-defined]
        self.assertEqual(access.request_id, "abc-123")  # type: ignore[attr-defined]
        self.assertNotIn(token, json.dumps([render(r) for r in logs.records]))

    @covers("SYS-NFR-06")
    def test_role_failure_is_logged(self) -> None:
        with self.assertLogs("gradian.accounts", level="WARNING") as logs:
            self.get_as("/api/v1/me", roles=())
        self.assertEqual(getattr(logs.records[0], "event", None), "role_failure")
        self.assertEqual(getattr(logs.records[0], "reason", None), "role_not_assigned")

    @covers("SYS-NFR-06")
    def test_profile_refresh_is_logged_with_field_names_only(self) -> None:
        self.get_as("/api/v1/me")
        with self.assertLogs("gradian.accounts", level="INFO") as logs:
            self.get_as("/api/v1/me", email="other@gradian.test")
        updated = next(r for r in logs.records if getattr(r, "event", "") == "profile_updated")
        self.assertEqual(updated.fields, ["email"])  # type: ignore[attr-defined]
        self.assertNotIn("other@gradian.test", json.dumps(render(updated)))

    @covers("SYS-NFR-01")
    def test_error_bodies_never_echo_the_token(self) -> None:
        token = make_token(audience="wrong")
        response = self.client.get("/api/v1/me", **self.bearer(token))
        self.assertNotIn(token, response.content.decode())

    def test_unsafe_request_ids_are_replaced(self) -> None:
        response = self.client.get("/health/live", HTTP_X_REQUEST_ID="bad id\nwith newline")
        self.assertRegex(response["X-Request-ID"], r"^[0-9a-f]{32}$")
