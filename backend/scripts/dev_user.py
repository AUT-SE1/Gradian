#!/usr/bin/env python3
"""Create a demo user in Keycloak through the Admin API, for manual testing before the seed exists.

Run through `make dev-user MOBILE=09120000001 ROLES=student`. Refuses ENVIRONMENT=production.
An existing user with the same mobile number is left untouched.

ROLES is a comma-separated list of realm roles. Use `none` for a user without any role, or
`student,admin` for one with two, to see the 403 role errors. A consultant needs
CONSULTANT_TYPE=consultant or top_ranker.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
MOBILE = re.compile(r"^09\d{9}$")
KNOWN_ROLES = {"student", "consultant", "professor", "admin", "service"}
TIMEOUT_SECONDS = 10


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def parse_roles(raw: str) -> list[str]:
    if raw.strip().lower() == "none":
        return []
    roles = [part.strip() for part in raw.split(",") if part.strip()]
    unknown = sorted(set(roles) - KNOWN_ROLES)
    if unknown:
        raise ValueError(f"unknown role(s): {', '.join(unknown)}")
    return roles


def user_payload(
    *,
    mobile: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    consultant_type: str,
) -> dict[str, Any]:
    if not MOBILE.match(mobile):
        raise ValueError("MOBILE must look like 09123456789")
    attributes: dict[str, list[str]] = {"mobile": [mobile]}
    if consultant_type:
        attributes["consultant_type"] = [consultant_type]
    return {
        "username": mobile,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "attributes": attributes,
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    }


class Admin:
    def __init__(self, base_url: str, realm: str, user: str, password: str) -> None:
        self.base = base_url.rstrip("/")
        self.realm = realm
        response = requests.post(
            f"{self.base}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": user,
                "password": password,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        response = requests.request(
            method,
            f"{self.base}/admin/realms/{self.realm}{path}",
            headers=self.headers,
            timeout=TIMEOUT_SECONDS,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def find(self, username: str) -> str | None:
        found = self.call("GET", "/users", params={"username": username, "exact": "true"}).json()
        return str(found[0]["id"]) if found else None

    def create(self, payload: dict[str, Any], roles: list[str]) -> str:
        created = self.call("POST", "/users", json=payload)
        user_id = created.headers["Location"].rstrip("/").rsplit("/", 1)[-1]
        if roles:
            representations = [self.call("GET", f"/roles/{role}").json() for role in roles]
            self.call("POST", f"/users/{user_id}/role-mappings/realm", json=representations)
        return user_id


def main() -> int:
    dotenv = parse_dotenv(ROOT / ".env")

    def setting(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv.get(name, default)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mobile", required=True)
    parser.add_argument("--roles", default="student")
    parser.add_argument("--consultant-type", default="")
    parser.add_argument("--first-name", default="علی")
    parser.add_argument("--last-name", default="رضایی")
    parser.add_argument("--email", default="")
    parser.add_argument("--password", default="")
    args = parser.parse_args()

    if setting("ENVIRONMENT", "development") == "production":
        print("error: refusing to create demo users with ENVIRONMENT=production", file=sys.stderr)
        return 1
    password = args.password or setting("SEED_DEFAULT_PASSWORD")
    if not password:
        print("error: set SEED_DEFAULT_PASSWORD in .env or pass PASSWORD=...", file=sys.stderr)
        return 1

    try:
        roles = parse_roles(args.roles)
        payload = user_payload(
            mobile=args.mobile,
            email=args.email or f"dev.{args.mobile}@gradian.test",
            first_name=args.first_name,
            last_name=args.last_name,
            password=password,
            consultant_type=args.consultant_type,
        )
        admin = Admin(
            setting("KEYCLOAK_URL"),
            setting("KEYCLOAK_REALM"),
            setting("KEYCLOAK_ADMIN_USER"),
            setting("KEYCLOAK_ADMIN_PASSWORD"),
        )
        if admin.find(args.mobile):
            print(f"{args.mobile} already exists, left untouched")
            return 0
        admin.create(payload, roles)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(
            f"error: Keycloak request failed ({exc}). Is the stack up? make up bootstrap",
            file=sys.stderr,
        )
        return 1

    print(f"created {args.mobile} with roles: {', '.join(roles) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
