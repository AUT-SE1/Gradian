"""From an Authorization header to a caller. Every web-framework adapter goes through here."""

from collections.abc import Callable, Mapping
from typing import Any

from django.conf import settings
from django.utils.module_loading import import_string

from gradian_auth import context
from gradian_auth.errors import InvalidTokenError
from gradian_auth.principals import Principal
from gradian_auth.tokens import validate_token

AUTHENTICATE_HEADER = 'Bearer realm="gradian"'
DEFAULT_PRINCIPAL_BUILDER = "gradian_auth.principals.build_principal"

PrincipalBuilder = Callable[[Mapping[str, Any]], Principal]


def parse_bearer(header: bytes) -> str | None:
    """The token in `Authorization: Bearer <token>`.

    No header, or another scheme, is None: the caller is anonymous and the permission layer
    answers 401. A Bearer header that cannot hold a token is refused here with 401.
    """
    parts = header.split()
    if not parts or parts[0].lower() != b"bearer":
        return None
    if len(parts) != 2:
        raise InvalidTokenError
    try:
        return parts[1].decode("ascii")
    except UnicodeDecodeError:
        raise InvalidTokenError from None


def principal_builder() -> PrincipalBuilder:
    path = getattr(settings, "GRADIAN_PRINCIPAL_BUILDER", DEFAULT_PRINCIPAL_BUILDER)
    builder: PrincipalBuilder = import_string(path)
    return builder


def authenticate_token(token: str) -> tuple[Principal, dict[str, Any]]:
    """Validate the token, build the caller, and note who it is for the log lines."""
    claims = validate_token(token)
    principal = principal_builder()(claims)
    context.user_sub.set(principal.sub)
    return principal, claims
