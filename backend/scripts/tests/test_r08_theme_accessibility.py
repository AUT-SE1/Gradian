from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / 'keycloak' / 'themes' / 'gradian' / 'login'
REGISTER = (THEME / 'register.ftl').read_text(encoding='utf-8')
TEMPLATE = (THEME / 'template.ftl').read_text(encoding='utf-8')
CSS = (THEME / 'resources' / 'css' / 'gradian.css').read_text(encoding='utf-8')
MESSAGES = (THEME / 'messages' / 'messages_fa.properties').read_text(encoding='utf-8')
PROPS = (THEME / 'theme.properties').read_text(encoding='utf-8')


class R08ThemeAccessibilityTests(unittest.TestCase):
    def test_sensitive_passwords_are_never_repopulated(self):
        self.assertIn('<#if type != "password">value=', REGISTER)
        password_fragments = re.findall(r'<@field name="(?:password|password-confirm)"[^>]*>', REGISTER)
        self.assertEqual(len(password_fragments), 2)
        for fragment in password_fragments:
            self.assertNotIn('value=', fragment)
            self.assertIn('autocomplete="new-password"', fragment)

    def test_registration_fields_expose_server_errors(self):
        self.assertIn('aria-invalid=', REGISTER)
        self.assertIn('aria-describedby="${name}-error"', REGISTER)
        self.assertIn('aria-errormessage="${name}-error"', REGISTER)
        self.assertIn('role="alert" aria-live="assertive"', REGISTER)
        self.assertIn('firstInvalid.focus()', REGISTER)

    def test_mobile_and_email_are_ltr_in_persian_form(self):
        self.assertRegex(REGISTER, r'name="username"[^\n]*dir="ltr"')
        self.assertRegex(REGISTER, r'name="email"[^\n]*dir="ltr"')
        self.assertIn('unicode-bidi: plaintext', CSS)

    def test_general_messages_use_error_vs_status_semantics(self):
        self.assertIn('message.type == "error"', TEMPLATE)
        self.assertIn('role="alert" aria-live="assertive"', TEMPLATE)
        self.assertIn('role="status" aria-live="polite"', TEMPLATE)
        self.assertIn('aria-atomic="true"', TEMPLATE)

    def test_common_registration_errors_have_actionable_persian_copy(self):
        for key in [
            'usernameExistsMessage', 'emailExistsMessage', 'invalidEmailMessage',
            'missingPasswordMessage', 'notMatchPasswordMessage',
            'invalidPasswordMinLengthMessage', 'error-user-attribute-required',
            'error-invalid-value',
        ]:
            self.assertRegex(MESSAGES, rf'(?m)^{re.escape(key)}=.+$')
        self.assertNotIn('Exception', MESSAGES)
        self.assertNotIn('HTTP', MESSAGES)

    def test_small_screen_and_keyboard_guards_exist(self):
        self.assertIn('overflow-x: hidden', CSS)
        self.assertIn('@media (max-width: 360px)', CSS)
        self.assertIn('overflow-wrap: anywhere', CSS)
        self.assertIn('button:focus-visible', CSS)
        self.assertIn('input:focus-visible', CSS)

    def test_keycloak_locale_claim_is_limited_to_verified_scope(self):
        self.assertRegex(PROPS, r'(?m)^locales=fa\s*$')
        self.assertNotRegex(PROPS, r'(?m)^locales=.*\ben\b')


if __name__ == '__main__':
    unittest.main()
