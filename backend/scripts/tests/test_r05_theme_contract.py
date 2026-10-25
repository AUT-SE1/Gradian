from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "keycloak" / "themes" / "gradian" / "login"
REGISTER = (THEME / "register.ftl").read_text(encoding="utf-8")
LOGIN = (THEME / "login.ftl").read_text(encoding="utf-8")
TEMPLATE = (THEME / "template.ftl").read_text(encoding="utf-8")
CSS = (THEME / "resources" / "css" / "gradian.css").read_text(encoding="utf-8")


class R05ThemeContractTests(unittest.TestCase):
    def test_registration_keeps_keycloak_action_and_six_base_fields(self):
        self.assertIn('action="${url.registrationAction}"', REGISTER)
        for name in ("firstName", "lastName", "username", "email", "password", "password-confirm"):
            self.assertIn(f'name="{name}"', REGISTER)

    def test_passwords_are_never_repopulated(self):
        self.assertIn('<#if type != "password">value="${(register.formData[name]!', REGISTER)
        self.assertIn('name="password" label="رمز عبور" type="password"', REGISTER)
        self.assertIn('name="password-confirm" label="تکرار رمز عبور" type="password"', REGISTER)
        self.assertEqual(REGISTER.count('autocomplete="new-password"'), 2)

    def test_non_sensitive_retry_values_and_accessible_field_errors_remain(self):
        self.assertIn('register.formData[name]', REGISTER)
        self.assertIn('aria-invalid=', REGISTER)
        self.assertIn('aria-describedby="${name}-error"', REGISTER)
        self.assertIn('kcSanitize(messagesPerField.get(name))?no_esc', REGISTER)
        self.assertIn('role="alert"', REGISTER)

    def test_login_registration_link_is_conditional_and_uses_keycloak_url(self):
        condition = 'realm.password && realm.registrationAllowed && !registrationDisabled??'
        self.assertIn(f'displayInfo={condition}', LOGIN)
        self.assertIn(f'<#if {condition}>', LOGIN)
        self.assertIn('href="${url.registrationUrl}"', LOGIN)
        self.assertNotIn('/protocol/openid-connect/registrations', LOGIN)

    def test_registration_back_link_and_general_message_are_provider_owned(self):
        self.assertIn('href="${url.loginUrl}"', REGISTER)
        self.assertIn("displayMessage=messagesPerField.exists('global')", REGISTER)
        self.assertIn('kcSanitize(message.summary)?no_esc', TEMPLATE)
        self.assertIn('aria-live="polite"', TEMPLATE)

    def test_keyboard_and_mobile_contract(self):
        for value in ('autocomplete="given-name"', 'autocomplete="family-name"', 'autocomplete="username"', 'autocomplete="email"'):
            self.assertIn(value, REGISTER)
        self.assertIn('inputmode="numeric"', REGISTER)
        self.assertIn(':focus-visible', CSS)
        self.assertIn('@media (max-width: 620px)', CSS)
        self.assertIn('font-size: 16px', CSS)


if __name__ == "__main__":
    unittest.main()
