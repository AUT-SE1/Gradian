"""Fake Keycloak key set and token factory for fast tests (test plan 2.2)."""

import time
import uuid
from collections.abc import Iterable
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from django.conf import settings

KEY_ID = "test-key-1"
PRIVATE_KEY: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_PRIVATE_KEY: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwks_document(*keys: tuple[str, RSAPrivateKey]) -> dict[str, Any]:
    """The JWKS Keycloak would publish. Defaults to the one test key."""
    pairs = keys or ((KEY_ID, PRIVATE_KEY),)
    documents = []
    for kid, private in pairs:
        jwk: dict[str, Any] = jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key(), as_dict=True)
        documents.append({**jwk, "kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": documents}


def make_token(
    *,
    sub: str | uuid.UUID = "00000000-0000-4000-8000-000000000001",
    roles: Iterable[str] = ("student",),
    mobile: str | None = "09120000001",
    email: str | None = "student.1.1@gradian.test",
    first_name: str | None = "علی",
    last_name: str | None = "رضایی",
    consultant_type: str | None = None,
    issuer: str | None = None,
    audience: str | list[str] | None = None,
    expires_in: int = 600,
    issued_at: int | None = None,
    key: RSAPrivateKey = PRIVATE_KEY,
    kid: str | None = KEY_ID,
    algorithm: str = "RS256",
    extra: dict[str, Any] | None = None,
    omit: Iterable[str] = (),
) -> str:
    """Sign exactly the token a test needs. `omit` drops claims by name."""
    now = int(time.time()) if issued_at is None else issued_at
    claims: dict[str, Any] = {
        "sub": str(sub),
        "iss": issuer or settings.KEYCLOAK_ISSUER,
        "aud": audience or settings.KEYCLOAK_CORE_CLIENT_ID,
        "iat": now,
        "exp": now + expires_in,
        "preferred_username": mobile,
        "email": email,
        "given_name": first_name,
        "family_name": last_name,
        "realm_access": {"roles": ["offline_access", *roles]},
    }
    if consultant_type is not None:
        claims["consultant_type"] = consultant_type
    claims.update(extra or {})
    for name in omit:
        claims.pop(name, None)
    claims = {name: value for name, value in claims.items() if value is not None}
    headers = {"kid": kid} if kid else {}
    signing_key: Any = None if algorithm == "none" else key
    return jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)


def service_token(**kwargs: Any) -> str:
    """A client-credentials token: the `service` role and no person's identity."""
    return make_token(
        roles=("service",),
        mobile=None,
        email=None,
        first_name=None,
        last_name=None,
        extra={"azp": "group-service-1"},
        **kwargs,
    )
