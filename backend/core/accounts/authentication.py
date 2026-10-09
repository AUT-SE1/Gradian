"""The Core Service's principal builder, plugged into `gradian_auth` through
`GRADIAN_PRINCIPAL_BUILDER`. Token validation itself lives in the package (DES-AUTH-01 to 04)."""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from accounts.errors import AccountDisabledError
from accounts.models import Profile
from accounts.principals import CoreUserPrincipal
from accounts.profiles import grant_default_role, sync_profile
from gradian_auth.claims import extract_roles
from gradian_auth.principals import Principal, UserPrincipal
from gradian_auth.principals import build_principal as build_token_principal
from gradian_auth.roles import PANEL_ROLES

logger = logging.getLogger("gradian.accounts")


def build_principal(claims: Mapping[str, Any]) -> Principal:
    principal = build_token_principal(claims)
    if not isinstance(principal, UserPrincipal):
        return principal

    identity = principal.identity
    registered_just_now = not any(role in PANEL_ROLES for role in extract_roles(claims)) and not (
        Profile.objects.filter(sub=identity.sub).exists()
    )
    iat = claims.get("iat")
    issued_at = datetime.fromtimestamp(iat, UTC) if isinstance(iat, int | float) else None
    profile = sync_profile(identity, issued_at)
    if registered_just_now:
        grant_default_role(str(identity.sub))
    if not profile.is_active:
        logger.info("disabled account refused", extra={"event": "account_disabled"})
        raise AccountDisabledError
    return CoreUserPrincipal(identity=identity, panel=principal.panel, profile=profile)
