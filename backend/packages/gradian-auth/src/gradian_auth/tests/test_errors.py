"""One error shape, English codes, Persian messages (DES-API-01, DES-XC-03)."""

from django.test import SimpleTestCase

from gradian_auth.errors import (
    MESSAGES,
    AmbiguousRoleError,
    ApiError,
    InvalidTokenError,
    error_body,
    message_for,
    register_messages,
)
from gradian_testing.covers import covers


class ConflictError(ApiError):
    status_code = 409
    default_code = "test_conflict"


@covers("SYS-NFR-05")
class ErrorShapeTests(SimpleTestCase):
    def tearDown(self) -> None:
        MESSAGES.pop("test_conflict", None)
        super().tearDown()

    def test_body_has_code_message_and_details(self) -> None:
        body = AmbiguousRoleError(details={"roles": ["admin", "student"]}).body()
        self.assertEqual(set(body), {"code", "message", "details"})
        self.assertEqual(body["code"], "ambiguous_role")
        self.assertEqual(body["details"], {"roles": ["admin", "student"]})

    def test_details_default_to_an_empty_object(self) -> None:
        self.assertEqual(InvalidTokenError().body()["details"], {})
        self.assertEqual(error_body("not_found")["details"], {})

    def test_every_code_is_english_and_every_message_is_persian_text(self) -> None:
        for code, message in MESSAGES.items():
            with self.subTest(code=code):
                self.assertRegex(code, r"^[a-z_]+$")
                self.assertTrue(any("\u0600" <= ch <= "\u06ff" for ch in message))

    def test_an_unknown_code_falls_back_to_the_server_error_message(self) -> None:
        self.assertEqual(message_for("never_registered"), MESSAGES["server_error"])

    def test_a_service_registers_its_own_codes(self) -> None:
        register_messages({"test_conflict": "این مورد تکراری است."})
        self.assertEqual(ConflictError().body()["message"], "این مورد تکراری است.")
        self.assertEqual(ConflictError.status_code, 409)

    def test_registering_the_same_text_twice_is_harmless(self) -> None:
        register_messages({"test_conflict": "متن"})
        register_messages({"test_conflict": "متن"})

    def test_a_different_text_for_an_existing_code_is_refused(self) -> None:
        register_messages({"test_conflict": "متن"})
        with self.assertRaises(ValueError):
            register_messages({"test_conflict": "متن دیگر"})
        with self.assertRaises(ValueError):
            register_messages({"invalid_token": "something else"})
