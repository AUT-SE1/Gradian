"""Static contract checks for R07 that do not require a running Django/Keycloak stack."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT / "core/accounts/authentication.py"
PROFILES = ROOT / "core/accounts/profiles.py"
ADMIN = ROOT / "packages/gradian-keycloak/src/gradian_keycloak/admin_client.py"
FAKE = ROOT / "packages/gradian-testing/src/gradian_testing/fakes.py"
TEST_AUTH = ROOT / "core/accounts/tests/test_authentication.py"
TEST_ME = ROOT / "core/accounts/tests/test_me.py"


class R07IdentityContractTests(unittest.TestCase):
    def test_roleless_token_retries_default_role_even_after_profile_exists(self) -> None:
        text = AUTH.read_text()
        self.assertIn("token_has_panel_role", text)
        self.assertIn("if not token_has_panel_role:\n        grant_default_role", text)
        self.assertNotIn("registered_just_now", text)

    def test_provider_failure_is_retryable_502_not_silently_swallowed(self) -> None:
        text = PROFILES.read_text()
        self.assertIn("ensure_role(sub, DEFAULT_PANEL)", text)
        self.assertIn("raise IdentityProviderUnavailableError from None", text)

    def test_role_ensure_is_idempotent_in_real_and_fake_admin_clients(self) -> None:
        admin = ADMIN.read_text()
        fake = FAKE.read_text()
        self.assertIn("def ensure_role(self, sub: str, role: str)", admin)
        self.assertIn('if any(item.get("name") == role for item in current)', admin)
        self.assertIn("def ensure_role(self, sub: str, role: str)", fake)
        self.assertIn("assigned_roles", fake)

    def test_fast_suite_contains_failure_retry_and_relogin_cases(self) -> None:
        text = TEST_AUTH.read_text()
        self.assertIn("test_roleless_grant_failure_is_502_and_the_next_request_retries", text)
        self.assertIn("test_existing_profile_with_a_roleless_token_still_ensures_student", text)
        self.assertIn("test_fresh_student_token_after_relogin_needs_no_default_role_write", text)

    def test_empty_field_of_study_is_explicitly_accepted(self) -> None:
        text = TEST_ME.read_text()
        self.assertIn("test_new_student_can_enter_with_an_empty_field_of_study", text)
        self.assertIn('self.assertEqual(body["field_of_study"], "")', text)


if __name__ == "__main__":
    unittest.main()
