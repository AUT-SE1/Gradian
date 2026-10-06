"""Role resolution (DES-AUTH-02, DES-IDP-03, DES-AUTH-06)."""

from collections.abc import Iterable

from accounts.errors import AmbiguousRoleError, RoleNotAssignedError

PANEL_ROLES: tuple[str, ...] = ("student", "consultant", "professor", "admin")
SERVICE_ROLE = "service"

HOME_PATHS: dict[str, str] = {role: f"/{role}" for role in PANEL_ROLES}


def resolve_panel(roles: Iterable[str]) -> str:
    """Return the single panel role, ignoring every other realm role (e.g. offline_access)."""
    panel_roles = sorted({role for role in roles if role in PANEL_ROLES})
    if not panel_roles:
        raise RoleNotAssignedError
    if len(panel_roles) > 1:
        raise AmbiguousRoleError(details={"roles": panel_roles})
    return panel_roles[0]
