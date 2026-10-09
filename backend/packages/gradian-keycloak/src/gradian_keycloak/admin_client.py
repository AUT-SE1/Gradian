"""The Keycloak Admin API as Core uses it, through the service account of this service's client.

Only a service whose client has the realm-management roles (Core, `gradian-core`) can use this.
Group services have no such rights and must not call it.
"""

import contextlib
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import requests

from gradian_keycloak.config import get_config
from gradian_keycloak.errors import KeycloakError
from gradian_keycloak.roles import PANEL_ROLES
from gradian_keycloak.service_token import ServiceTokenClient

logger = logging.getLogger("gradian.keycloak")

PAGE_SIZE = 200


@dataclass(frozen=True)
class KeycloakUser:
    sub: str
    username: str
    email: str
    first_name: str
    last_name: str
    enabled: bool
    roles: tuple[str, ...]
    consultant_type: str


@dataclass(frozen=True)
class NewUser:
    mobile: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    consultant_type: str


class IdentityAdmin(Protocol):
    """The part of the Keycloak Admin API Core uses (DES-ID-04, DES-ID-05, DES-ADM-01)."""

    def update_user(self, sub: str, changes: Mapping[str, str]) -> None: ...

    def list_panel_users(self) -> list[KeycloakUser]: ...

    def create_user(self, user: NewUser) -> str: ...

    def set_panel_role(self, sub: str, role: str, consultant_type: str) -> None: ...

    def set_enabled(self, sub: str, enabled: bool) -> None: ...

    def grant_role(self, sub: str, role: str) -> None: ...


class KeycloakAdminClient:
    def __init__(self, tokens: ServiceTokenClient | None = None) -> None:
        self._tokens = tokens or ServiceTokenClient()

    def _call(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._request(method, path, **kwargs)
        return response.json() if response.content else None

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        config = get_config()
        try:
            response = requests.request(
                method,
                f"{config.admin_url}{path}",
                headers=self._tokens.auth_headers(),
                timeout=config.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise KeycloakError(f"{method} {path} failed") from exc
        if response.status_code >= 400:
            raise KeycloakError(
                f"{method} {path} returned {response.status_code}", response.status_code
            )
        return response

    def update_user(self, sub: str, changes: Mapping[str, str]) -> None:
        """Apply `email`, `first_name`, `last_name` changes (read, merge, write back)."""
        representation: dict[str, Any] = self._call("GET", f"/users/{sub}")
        names = {"email": "email", "first_name": "firstName", "last_name": "lastName"}
        for field, value in changes.items():
            representation[names[field]] = value
        self._call("PUT", f"/users/{sub}", json=representation)

    def grant_role(self, sub: str, role: str) -> None:
        representation = self._call("GET", f"/roles/{role}")
        self._call("POST", f"/users/{sub}/role-mappings/realm", json=[representation])

    def create_user(self, user: NewUser) -> str:
        """Create the account with its role. If the role cannot be assigned the account is
        removed again, so a failure leaves nothing behind (DES-ID-05)."""
        attributes = {"mobile": [user.mobile]}
        if user.consultant_type:
            attributes["consultant_type"] = [user.consultant_type]
        response = self._request(
            "POST",
            "/users",
            json={
                "username": user.mobile,
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "enabled": True,
                "emailVerified": True,
                "attributes": attributes,
                "credentials": [{"type": "password", "value": user.password, "temporary": False}],
            },
        )
        sub = response.headers["Location"].rstrip("/").rsplit("/", 1)[-1]
        try:
            self.grant_role(sub, user.role)
        except KeycloakError:
            with contextlib.suppress(KeycloakError):
                self._request("DELETE", f"/users/{sub}")
            raise
        return sub

    def set_panel_role(self, sub: str, role: str, consultant_type: str) -> None:
        """Make `role` the user's only panel role. The attribute goes first: it is only read for
        consultants, so it is harmless if the role change then fails."""
        representation: dict[str, Any] = self._call("GET", f"/users/{sub}")
        attributes: dict[str, Any] = representation.get("attributes") or {}
        if consultant_type:
            attributes["consultant_type"] = [consultant_type]
        else:
            attributes.pop("consultant_type", None)
        representation["attributes"] = attributes
        self._call("PUT", f"/users/{sub}", json=representation)

        current: list[dict[str, Any]] = self._call("GET", f"/users/{sub}/role-mappings/realm")
        stale = [r for r in current if r["name"] in PANEL_ROLES and r["name"] != role]
        if stale:
            self._call("DELETE", f"/users/{sub}/role-mappings/realm", json=stale)
        if not any(r["name"] == role for r in current):
            self.grant_role(sub, role)

    def set_enabled(self, sub: str, enabled: bool) -> None:
        representation: dict[str, Any] = self._call("GET", f"/users/{sub}")
        representation["enabled"] = enabled
        self._call("PUT", f"/users/{sub}", json=representation)

    def list_panel_users(self) -> list[KeycloakUser]:
        """Every user holding at least one panel role, with all their panel roles."""
        found: dict[str, dict[str, Any]] = {}
        roles: dict[str, set[str]] = {}
        for role in PANEL_ROLES:
            first = 0
            while True:
                page: list[dict[str, Any]] = self._call(
                    "GET",
                    f"/roles/{role}/users",
                    params={"first": first, "max": PAGE_SIZE, "briefRepresentation": "false"},
                )
                for user in page:
                    found[user["id"]] = user
                    roles.setdefault(user["id"], set()).add(role)
                if len(page) < PAGE_SIZE:
                    break
                first += PAGE_SIZE
        first = 0
        while True:  # people who have not been given a role yet are students
            page = self._call(
                "GET",
                "/users",
                params={"first": first, "max": PAGE_SIZE, "briefRepresentation": "false"},
            )
            for user in page:
                if user["id"] not in found and not user.get("serviceAccountClientId"):
                    found[user["id"]] = user
                    roles[user["id"]] = set()
            if len(page) < PAGE_SIZE:
                break
            first += PAGE_SIZE
        return [
            KeycloakUser(
                sub=sub,
                username=str(user.get("username", "")),
                email=str(user.get("email", "")),
                first_name=str(user.get("firstName", "")),
                last_name=str(user.get("lastName", "")),
                enabled=bool(user.get("enabled", False)),
                roles=tuple(sorted(roles[sub])),
                consultant_type=_first(user.get("attributes", {}).get("consultant_type")),
            )
            for sub, user in found.items()
        ]


def _first(value: object) -> str:
    if isinstance(value, list) and value:
        value = value[0]
    return value if isinstance(value, str) else ""


_admin_client = KeycloakAdminClient()


def get_admin_client() -> IdentityAdmin:
    return _admin_client
