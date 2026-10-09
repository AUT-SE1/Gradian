"""Role resolution (DES-AUTH-02, DES-IDP-03, DES-AUTH-06)."""

from collections.abc import Iterable

from gradian_auth.errors import AmbiguousRoleError
from gradian_keycloak.roles import DEFAULT_PANEL, PANEL_ROLES, SERVICE_ROLE

__all__ = [
    "CONSULTANT_ROLE",
    "CONSULTANT_TYPES",
    "DEFAULT_PANEL",
    "HOME_PATHS",
    "PANEL_ROLES",
    "SERVICE_ROLE",
    "resolve_panel",
]

CONSULTANT_ROLE = "consultant"
CONSULTANT_TYPES: tuple[str, ...] = ("consultant", "top_ranker")

HOME_PATHS: dict[str, str] = {role: f"/{role}" for role in PANEL_ROLES}


def resolve_panel(roles: Iterable[str]) -> str:
    """Return the single panel role, ignoring every other realm role (e.g. offline_access).

    A person with no panel role, such as someone who has just registered, is a student."""
    panel_roles = sorted({role for role in roles if role in PANEL_ROLES})
    if not panel_roles:
        return DEFAULT_PANEL
    if len(panel_roles) > 1:
        raise AmbiguousRoleError(details={"roles": panel_roles})
    return panel_roles[0]
