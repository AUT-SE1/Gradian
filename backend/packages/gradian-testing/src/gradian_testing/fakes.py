"""A stand-in for the Keycloak Admin API client (DES-ID-05, DES-ID-04 without Keycloak)."""

import uuid
from collections.abc import Mapping

from gradian_keycloak.admin_client import KeycloakUser, NewUser
from gradian_keycloak.errors import KeycloakError


class FakeIdentityAdmin:
    """Records calls, and can be told to fail by setting `fail_with`."""

    def __init__(self) -> None:
        self.updates: list[tuple[str, dict[str, str]]] = []
        self.users: list[KeycloakUser] = []
        self.fail_with: KeycloakError | None = None
        self.created: list[NewUser] = []
        self.roles: list[tuple[str, str, str]] = []
        self.enabled: list[tuple[str, bool]] = []
        self.granted: list[tuple[str, str]] = []

    def update_user(self, sub: str, changes: Mapping[str, str]) -> None:
        if self.fail_with:
            raise self.fail_with
        self.updates.append((sub, dict(changes)))

    def create_user(self, user: NewUser) -> str:
        if self.fail_with:
            raise self.fail_with
        self.created.append(user)
        return str(uuid.uuid4())

    def set_panel_role(self, sub: str, role: str, consultant_type: str) -> None:
        if self.fail_with:
            raise self.fail_with
        self.roles.append((sub, role, consultant_type))

    def set_enabled(self, sub: str, enabled: bool) -> None:
        if self.fail_with:
            raise self.fail_with
        self.enabled.append((sub, enabled))

    def grant_role(self, sub: str, role: str) -> None:
        if self.fail_with:
            raise self.fail_with
        self.granted.append((sub, role))

    def list_panel_users(self) -> list[KeycloakUser]:
        if self.fail_with:
            raise self.fail_with
        return list(self.users)
