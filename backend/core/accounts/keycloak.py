"""Everything that talks to Keycloak over HTTP. Tests replace `fetch_jwks` and
`get_admin_client`; nothing else in the code base makes a network call to Keycloak."""

import contextlib
import logging
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import requests
from django.conf import settings

from accounts.roles import PANEL_ROLES

logger = logging.getLogger("gradian.keycloak")


class KeycloakError(Exception):
    """A Keycloak call failed. `status` is the HTTP status, or None if it was unreachable."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


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


def fetch_jwks() -> dict[str, Any]:
    try:
        response = requests.get(
            settings.KEYCLOAK_JWKS_URL, timeout=settings.KEYCLOAK_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        document = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise KeycloakError("could not fetch the signing keys") from exc
    if not isinstance(document, dict):
        raise KeycloakError("signing keys have an unexpected shape")
    return document


def check_reachable() -> None:
    """Readiness probe: the realm's public keys can be fetched."""
    fetch_jwks()


class KeycloakAdminClient:
    """Admin API client using the `gradian-core` service account (client credentials)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token = ""
        self._expires_at = 0.0

    @property
    def _admin_base(self) -> str:
        return f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}"

    def _access_token(self) -> str:
        with self._lock:
            if self._token and time.monotonic() < self._expires_at - 30:
                return self._token
            url = (
                f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
                "/protocol/openid-connect/token"
            )
            try:
                response = requests.post(
                    url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.KEYCLOAK_CORE_CLIENT_ID,
                        "client_secret": settings.KEYCLOAK_CORE_CLIENT_SECRET,
                    },
                    timeout=settings.KEYCLOAK_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                body = response.json()
                self._token = str(body["access_token"])
                self._expires_at = time.monotonic() + float(body.get("expires_in", 60))
            except (requests.RequestException, ValueError, KeyError) as exc:
                raise KeycloakError("could not obtain an admin token") from exc
            return self._token

    def _call(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._request(method, path, **kwargs)
        return response.json() if response.content else None

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        try:
            response = requests.request(
                method,
                f"{self._admin_base}{path}",
                headers=headers,
                timeout=settings.KEYCLOAK_TIMEOUT_SECONDS,
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
                    params={"first": first, "max": 200, "briefRepresentation": "false"},
                )
                for user in page:
                    found[user["id"]] = user
                    roles.setdefault(user["id"], set()).add(role)
                if len(page) < 200:
                    break
                first += 200
        first = 0
        while True:  # people who have not been given a role yet are students
            page = self._call(
                "GET", "/users", params={"first": first, "max": 200, "briefRepresentation": "false"}
            )
            for user in page:
                if user["id"] not in found and not user.get("serviceAccountClientId"):
                    found[user["id"]] = user
                    roles[user["id"]] = set()
            if len(page) < 200:
                break
            first += 200
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
