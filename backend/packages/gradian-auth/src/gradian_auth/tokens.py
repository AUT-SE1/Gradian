"""Local validation of Keycloak access tokens (DES-AUTH-01)."""

from typing import Any

import jwt

from gradian_auth.errors import InvalidTokenError
from gradian_auth.jwks import jwks_cache
from gradian_keycloak.config import get_config

ALGORITHM = "RS256"


def validate_token(token: str, *, audience: str | None = None) -> dict[str, Any]:
    """Check signature, issuer, expiry and audience. Any failure is a 401 `invalid_token`.

    The audience defaults to this service's own client id (`KEYCLOAK_CLIENT_ID`), which is what
    DES-REG-05 requires of every service. Only RS256 is accepted, which rules out `alg: none`
    and key-confusion with HS256.
    """
    config = get_config()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise InvalidTokenError from None
    if header.get("alg") != ALGORITHM:
        raise InvalidTokenError
    key = jwks_cache.get_key(header.get("kid"))
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=[ALGORITHM],
            issuer=config.issuer,
            audience=audience or config.client_id,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError:
        raise InvalidTokenError from None
    return claims
