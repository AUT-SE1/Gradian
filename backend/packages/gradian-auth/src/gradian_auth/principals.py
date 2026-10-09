"""Who is calling: a signed-in person, or a platform service with its own credential."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from gradian_auth.claims import Identity, extract_roles, identity_from_claims
from gradian_auth.errors import AmbiguousRoleError
from gradian_auth.roles import PANEL_ROLES, SERVICE_ROLE, resolve_panel

logger = logging.getLogger("gradian.auth")


@dataclass(frozen=True)
class UserPrincipal:
    identity: Identity
    panel: str

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def sub(self) -> str:
        return str(self.identity.sub)


@dataclass(frozen=True)
class ServicePrincipal:
    sub: str
    client_id: str

    @property
    def is_authenticated(self) -> bool:
        return True


Principal = UserPrincipal | ServicePrincipal


def build_principal(claims: Mapping[str, Any]) -> Principal:
    """The default builder: the caller as the token describes it, with nothing stored.

    A service has the `service` role and no panel role; a person has exactly one panel role
    (none means student). Core replaces this with a builder that also keeps a profile cache
    (`GRADIAN_PRINCIPAL_BUILDER`).
    """
    roles = extract_roles(claims)
    if SERVICE_ROLE in roles:
        if any(role in PANEL_ROLES for role in roles):
            logger.warning(
                "role resolution failed",
                extra={"event": "role_failure", "reason": "service_and_panel"},
            )
            raise AmbiguousRoleError(
                details={"roles": sorted(set(roles) & {SERVICE_ROLE, *PANEL_ROLES})}
            )
        return ServicePrincipal(sub=str(claims["sub"]), client_id=str(claims.get("azp", "")))

    try:
        panel = resolve_panel(roles)
    except AmbiguousRoleError as exc:
        logger.warning(
            "role resolution failed", extra={"event": "role_failure", "reason": exc.default_code}
        )
        raise
    return UserPrincipal(identity=identity_from_claims(claims, panel), panel=panel)
