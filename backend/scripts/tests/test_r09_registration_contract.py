"""R09 static registration integration checks; no live Keycloak/Core claims are made here."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "core" / "accounts"
AUTH_PKG = ROOT / "packages" / "gradian-auth" / "src" / "gradian_auth"
THEME = ROOT / "keycloak" / "themes" / "gradian" / "login"
REALM = ROOT / "keycloak" / "realm-template.json"


class R09RegistrationContractTests(unittest.TestCase):
    def test_public_config_owns_registration_endpoint_and_no_parallel_public_create_route(self) -> None:
        views = (CORE / "views.py").read_text(encoding="utf-8")
        urls = (CORE / "urls.py").read_text(encoding="utf-8")
        self.assertIn('"registration_endpoint": (f"{issuer}/protocol/openid-connect/registrations")', views)
        self.assertNotIn('path("register"', urls)
        self.assertNotIn('path("auth/register"', urls)

    def test_provider_form_owns_password_and_has_no_public_role_escalation_fields(self) -> None:
        register = (THEME / "register.ftl").read_text(encoding="utf-8")
        self.assertIn('action="${url.registrationAction}"', register)
        self.assertIn('name="password"', register)
        self.assertIn('name="password-confirm"', register)
        self.assertNotIn('name="role"', register)
        self.assertNotIn('name="consultant_type"', register)

    def test_realm_baseline_matches_registration_contract(self) -> None:
        realm = json.loads(REALM.read_text(encoding="utf-8"))
        self.assertIs(realm.get("registrationAllowed"), True)
        self.assertIs(realm.get("duplicateEmailsAllowed"), False)
        self.assertEqual(realm.get("passwordPolicy"), "length(8)")

    def test_roleless_self_registration_resolves_to_student_only(self) -> None:
        roles = (AUTH_PKG / "roles.py").read_text(encoding="utf-8")
        self.assertIn("if not panel_roles:\n        return DEFAULT_PANEL", roles)
        self.assertIn("if len(panel_roles) > 1:\n        raise AmbiguousRoleError", roles)

    def test_core_requires_durable_default_role_before_me_succeeds(self) -> None:
        auth = (CORE / "authentication.py").read_text(encoding="utf-8")
        profiles = (CORE / "profiles.py").read_text(encoding="utf-8")
        self.assertIn("if not token_has_panel_role:\n        grant_default_role", auth)
        self.assertIn("ensure_role(sub, DEFAULT_PANEL)", profiles)
        self.assertIn("raise IdentityProviderUnavailableError from None", profiles)


if __name__ == "__main__":
    unittest.main()
