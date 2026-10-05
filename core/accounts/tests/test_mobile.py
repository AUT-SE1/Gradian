from django.test import SimpleTestCase

from accounts.mobile import InvalidMobileError, normalize_mobile
from tests.helpers.covers import covers


@covers("SYS-ID-04")
class NormalizeMobileTests(SimpleTestCase):
    def test_accepted_forms_all_normalize_to_the_plain_form(self) -> None:
        cases = {
            "09121234567": "09121234567",
            "+989121234567": "09121234567",
            "00989121234567": "09121234567",
            "۰۹۱۲۱۲۳۴۵۶۷": "09121234567",  # Persian digits
            "٠٩١٢١٢٣٤٥٦٧": "09121234567",  # Arabic-Indic digits
            "+98۹۱۲۱۲۳۴۵۶۷": "09121234567",  # mixed digits and prefix
            "  09121234567 ": "09121234567",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_mobile(raw), expected)

    def test_rejected_values(self) -> None:
        for raw in [
            "",
            "0912123456",
            "091212345678",
            "08121234567",
            "9121234567",
            "abc",
            "+98 912",
        ]:
            with self.subTest(raw=raw), self.assertRaises(InvalidMobileError):
                normalize_mobile(raw)

    def test_normalizing_is_idempotent(self) -> None:
        once = normalize_mobile("+989121234567")
        self.assertEqual(normalize_mobile(once), once)
