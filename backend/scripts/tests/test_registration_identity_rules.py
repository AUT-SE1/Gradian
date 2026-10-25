import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RegistrationIdentityRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.realm = json.loads((ROOT / "keycloak" / "realm-template.json").read_text("utf-8"))
        cls.profile = json.loads((ROOT / "keycloak" / "user-profile.json").read_text("utf-8"))
        cls.attributes = {item["name"]: item for item in cls.profile["attributes"]}

    def test_password_policy_is_eight_characters(self) -> None:
        self.assertEqual(self.realm["passwordPolicy"], "length(8)")

    def test_mobile_and_email_identity_contract_is_provider_owned(self) -> None:
        self.assertEqual(
            self.attributes["username"]["validations"]["pattern"]["pattern"], r"^09\d{9}$"
        )
        self.assertFalse(self.realm["duplicateEmailsAllowed"])
        self.assertEqual(self.attributes["email"]["required"]["roles"], ["admin", "user"])
        self.assertIn("email", self.attributes["email"]["validations"])

    def test_names_require_a_real_unicode_letter_or_mark(self) -> None:
        expected = r"^(?=.*[\p{L}\p{M}])[\p{L}\p{M}\u200c ]+$"
        for field in ("firstName", "lastName"):
            with self.subTest(field=field):
                attribute = self.attributes[field]
                self.assertEqual(attribute["required"]["roles"], ["admin", "user"])
                self.assertEqual(attribute["validations"]["length"], {"min": 1, "max": 100})
                self.assertEqual(attribute["validations"]["pattern"]["pattern"], expected)

    def test_public_profile_cannot_assign_privileged_identity_attributes(self) -> None:
        self.assertEqual(self.attributes["mobile"]["permissions"]["edit"], ["admin"])
        self.assertEqual(self.attributes["consultant_type"]["permissions"]["edit"], ["admin"])


if __name__ == "__main__":
    unittest.main()
