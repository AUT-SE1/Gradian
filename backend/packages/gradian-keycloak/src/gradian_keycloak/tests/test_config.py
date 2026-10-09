from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from gradian_keycloak.config import get_config
from gradian_keycloak.tests.base import KEYCLOAK_SETTINGS, KeycloakSettingsTestCase


class ConfigTests(KeycloakSettingsTestCase):
    def test_urls_are_derived_from_the_public_and_internal_addresses(self) -> None:
        config = get_config()
        self.assertEqual(config.issuer, "http://keycloak.public.test/realms/gradian")
        self.assertEqual(
            config.jwks_url,
            "http://keycloak.internal.test/realms/gradian/protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.token_url,
            "http://keycloak.internal.test/realms/gradian/protocol/openid-connect/token",
        )
        self.assertEqual(config.admin_url, "http://keycloak.internal.test/admin/realms/gradian")

    def test_defaults_and_trailing_slashes(self) -> None:
        with override_settings(KEYCLOAK_PUBLIC_URL="http://a.test/", KEYCLOAK_REALM="other"):
            config = get_config()
        self.assertEqual(config.issuer, "http://a.test/realms/other")
        self.assertEqual(config.timeout, 5.0)

    def test_settings_are_read_on_every_call(self) -> None:
        with override_settings(KEYCLOAK_CLIENT_ID="group-3"):
            self.assertEqual(get_config().client_id, "group-3")
        self.assertEqual(get_config().client_id, "svc-client")


class MissingSettingTests(SimpleTestCase):
    def test_a_missing_required_setting_is_named(self) -> None:
        for name in ("KEYCLOAK_PUBLIC_URL", "KEYCLOAK_URL", "KEYCLOAK_CLIENT_ID"):
            with self.subTest(name=name):
                values = {k: v for k, v in KEYCLOAK_SETTINGS.items() if k != name}
                with (
                    override_settings(**values),
                    self.assertRaisesMessage(ImproperlyConfigured, name),
                ):
                    get_config()

    def test_the_client_secret_is_optional_here(self) -> None:
        values = {k: v for k, v in KEYCLOAK_SETTINGS.items() if k != "KEYCLOAK_CLIENT_SECRET"}
        with override_settings(**values):
            self.assertEqual(get_config().client_secret, "")
