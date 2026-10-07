"""Pieces shared by the API documentation of every endpoint."""

from typing import Any

from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers


class ErrorSerializer(serializers.Serializer[dict[str, Any]]):
    """The one error shape of every endpoint (DES-API-01)."""

    code = serializers.CharField(
        help_text="Stable English identifier, for example `invalid_token`."
    )
    message = serializers.CharField(help_text="Persian text for the user.")
    details = serializers.DictField(help_text="Extra data, such as the invalid fields.")


def error(description: str) -> OpenApiResponse:
    return OpenApiResponse(ErrorSerializer, description=description)


UNAUTHENTICATED = error(
    "`not_authenticated` (no token) or `invalid_token` (bad, expired or wrong audience)."
)
FORBIDDEN = error(
    "`role_not_assigned`, `ambiguous_role`, `account_disabled`, `incomplete_identity` or "
    "`permission_denied`."
)
CONFLICT = error("`identity_conflict`: the mobile number or email belongs to another account.")
PROVIDER_DOWN = error("`identity_provider_unavailable`: Keycloak could not be reached.")
