import tempfile
import unittest
from pathlib import Path

import dev_user
from covers import covers


@covers("SYS-DATA-01")
class DevUserTests(unittest.TestCase):
    def test_roles(self) -> None:
        self.assertEqual(dev_user.parse_roles("student"), ["student"])
        self.assertEqual(dev_user.parse_roles("student, admin"), ["student", "admin"])
        self.assertEqual(dev_user.parse_roles("none"), [])

    def test_unknown_role_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            dev_user.parse_roles("student,wizard")

    def test_payload_is_a_complete_enabled_user_with_a_permanent_password(self) -> None:
        payload = dev_user.user_payload(
            mobile="09120000001",
            email="a@gradian.test",
            first_name="علی",
            last_name="رضایی",
            password="pw",
            consultant_type="",
        )
        self.assertEqual(payload["username"], "09120000001")
        self.assertEqual(payload["attributes"], {"mobile": ["09120000001"]})
        self.assertTrue(payload["enabled"])
        self.assertFalse(payload["credentials"][0]["temporary"])

    def test_consultant_type_becomes_an_attribute(self) -> None:
        payload = dev_user.user_payload(
            mobile="09120000001",
            email="a@gradian.test",
            first_name="علی",
            last_name="رضایی",
            password="pw",
            consultant_type="top_ranker",
        )
        self.assertEqual(payload["attributes"]["consultant_type"], ["top_ranker"])

    def test_bad_mobile_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            dev_user.user_payload(
                mobile="9120000001",
                email="a@gradian.test",
                first_name="علی",
                last_name="رضایی",
                password="pw",
                consultant_type="",
            )

    def test_dotenv_parsing_ignores_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("# note\n\nA=1\nB = two\nbroken\n", encoding="utf-8")
            self.assertEqual(dev_user.parse_dotenv(path), {"A": "1", "B": "two"})
        self.assertEqual(dev_user.parse_dotenv(Path(tmp) / "missing"), {})
