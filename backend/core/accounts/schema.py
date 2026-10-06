"""Describes bearer-token authentication in the generated OpenAPI schema (DES-API-03)."""

from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema


class KeycloakBearerScheme(OpenApiAuthenticationExtension):  # type: ignore[no-untyped-call]  # base registers subclasses through an untyped hook
    target_class = "accounts.authentication.KeycloakBearerAuthentication"
    name = "keycloakBearer"

    def get_security_definition(self, auto_schema: AutoSchema) -> dict[str, Any]:
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
