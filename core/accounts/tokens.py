"""Local validation of Keycloak access tokens (DES-AUTH-01)."""

from typing import Any

import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from accounts.jwks import jwks_cache

ALGORITHM = "RS256"


def validate_token(token: str) -> dict[str, Any]:
    """Check signature, issuer, expiry and audience. Any failure is a 401 `invalid_token`.

    Only RS256 is accepted, which rules out `alg: none` and key-confusion with HS256.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise AuthenticationFailed(code="invalid_token") from None
    if header.get("alg") != ALGORITHM:
        raise AuthenticationFailed(code="invalid_token")
    key = jwks_cache.get_key(header.get("kid"))
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=[ALGORITHM],
            issuer=settings.KEYCLOAK_ISSUER,
            audience=settings.KEYCLOAK_CORE_CLIENT_ID,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError:
        raise AuthenticationFailed(code="invalid_token") from None
    return claims
