"""Authentication schemes shown in the API docs (DES-API-03).

Every environment offers `keycloakBearer`: paste an access token. Outside production the docs
also offer `keycloakPassword`, which signs in with a mobile number and password through the
test-only client `gradian-test`, so each role can be tried without a browser login.
"""

from typing import Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema

BEARER = "keycloakBearer"
PASSWORD = "keycloakPassword"  # noqa: S105  # name of a security scheme, not a secret


class KeycloakBearerScheme(OpenApiAuthenticationExtension):  # type: ignore[no-untyped-call]  # base registers subclasses through an untyped hook
    target_class = "gradian_auth.drf.KeycloakBearerAuthentication"
    name: str | list[str] = BEARER if settings.IS_PRODUCTION else [BEARER, PASSWORD]

    def get_security_requirement(self, auto_schema: AutoSchema) -> Any:
        if settings.IS_PRODUCTION:
            return {BEARER: []}
        return [{PASSWORD: []}, {BEARER: []}]

    def get_security_definition(self, auto_schema: AutoSchema) -> Any:
        bearer = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "An access token issued by Keycloak for the audience `gradian-core`.",
        }
        if settings.IS_PRODUCTION:
            return bearer
        token_url = (
            f"{settings.KEYCLOAK_PUBLIC_URL}/realms/{settings.KEYCLOAK_REALM}"
            "/protocol/openid-connect/token"
        )
        password = {
            "type": "oauth2",
            "description": (
                "Development only. Enter a mobile number as the username, its password, and "
                "leave the client id as it is."
            ),
            "flows": {"password": {"tokenUrl": token_url, "scopes": {}}},
        }
        return [bearer, password]
