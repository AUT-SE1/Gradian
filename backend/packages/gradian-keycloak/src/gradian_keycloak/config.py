"""Where Keycloak is and which client this service is, read from Django settings.

Settings are read on every call, never cached, so `override_settings` works in tests.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_REALM = "gradian"
DEFAULT_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class KeycloakConfig:
    realm: str
    public_url: str
    internal_url: str
    client_id: str
    client_secret: str
    timeout: float

    @property
    def issuer(self) -> str:
        """The `iss` of every token: Keycloak's public address, whatever address was called."""
        return f"{self.public_url}/realms/{self.realm}"

    @property
    def jwks_url(self) -> str:
        return f"{self.internal_url}/realms/{self.realm}/protocol/openid-connect/certs"

    @property
    def token_url(self) -> str:
        return f"{self.internal_url}/realms/{self.realm}/protocol/openid-connect/token"

    @property
    def admin_url(self) -> str:
        return f"{self.internal_url}/admin/realms/{self.realm}"


def _required(name: str) -> str:
    value = getattr(settings, name, "")
    if not value:
        raise ImproperlyConfigured(
            f"Missing setting {name}. See the gradian-keycloak README for the settings it reads."
        )
    return str(value)


def get_config() -> KeycloakConfig:
    return KeycloakConfig(
        realm=str(getattr(settings, "KEYCLOAK_REALM", DEFAULT_REALM)),
        public_url=_required("KEYCLOAK_PUBLIC_URL").rstrip("/"),
        internal_url=_required("KEYCLOAK_URL").rstrip("/"),
        client_id=_required("KEYCLOAK_CLIENT_ID"),
        client_secret=str(getattr(settings, "KEYCLOAK_CLIENT_SECRET", "")),
        timeout=float(getattr(settings, "KEYCLOAK_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
    )
