"""Mapping token claims to an identity (DES-IDP-06, DES-ID-02)."""

import unicodedata
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from gradian_auth.errors import IncompleteIdentityError
from gradian_auth.mobile import InvalidMobileError, normalize_mobile
from gradian_auth.roles import CONSULTANT_ROLE, CONSULTANT_TYPES

NAME_MAX_LENGTH = 100


def is_valid_name(value: str) -> bool:
    """1 to 100 characters: Unicode letters and marks, spaces and ZWNJ (section 3.1)."""
    if not value or len(value) > NAME_MAX_LENGTH:
        return False
    return all(unicodedata.category(ch)[0] in {"L", "M"} or ch in {" ", "\u200c"} for ch in value)


@dataclass(frozen=True)
class Identity:
    sub: uuid.UUID
    mobile: str
    email: str
    first_name: str
    last_name: str
    role: str
    consultant_type: str


def extract_roles(claims: Mapping[str, Any]) -> list[str]:
    realm_access = claims.get("realm_access")
    if not isinstance(realm_access, Mapping):
        return []
    roles = realm_access.get("roles")
    if not isinstance(roles, list):
        return []
    return [role for role in roles if isinstance(role, str)]


def _text(claims: Mapping[str, Any], name: str) -> str:
    value = claims.get(name)
    if isinstance(value, list) and value:  # a multivalued attribute mapper yields a list
        value = value[0]
    return value.strip() if isinstance(value, str) else ""


def identity_from_claims(claims: Mapping[str, Any], role: str) -> Identity:
    """Build the identity or refuse with 403 `incomplete_identity` naming the bad fields."""
    problems: list[str] = []

    try:
        sub = uuid.UUID(_text(claims, "sub"))
    except ValueError:
        sub = uuid.UUID(int=0)
        problems.append("sub")

    mobile = ""
    try:
        mobile = normalize_mobile(_text(claims, "preferred_username"))
    except InvalidMobileError:
        problems.append("preferred_username")

    email = _text(claims, "email").lower()
    if "@" not in email:
        problems.append("email")

    first_name = _text(claims, "given_name")
    if not is_valid_name(first_name):
        problems.append("given_name")
    last_name = _text(claims, "family_name")
    if not is_valid_name(last_name):
        problems.append("family_name")

    consultant_type = ""
    if role == CONSULTANT_ROLE:
        consultant_type = _text(claims, "consultant_type")
        if consultant_type not in CONSULTANT_TYPES:
            problems.append("consultant_type")

    if problems:
        raise IncompleteIdentityError(details={"fields": sorted(problems)})
    return Identity(sub, mobile, email, first_name, last_name, role, consultant_type)
