"""Real tokens and temporary users on the running Keycloak (integration tests, plan 2.3)."""

import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import requests
from django.conf import settings

from gradian_keycloak import admin_client
from gradian_keycloak.config import get_config
from gradian_keycloak.service_token import ServiceTokenClient

TEST_CLIENT_ID = "gradian-test"
TEMPORARY_KIND_CODE = "9"


def _token_url() -> str:
    return get_config().token_url


def password_token(mobile: str, password: str) -> str:
    """Sign in without a browser through the test-only client (DES-IDP-09). Returns the access
    token, whose issuer is the public address whichever address the request used (DEC-18)."""
    response = requests.post(
        _token_url(),
        data={
            "grant_type": "password",
            "client_id": TEST_CLIENT_ID,
            "username": mobile,
            "password": password,
        },
        timeout=settings.KEYCLOAK_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def service_token(client_id: str, client_secret: str) -> str:
    """A client-credentials token, as a group service would obtain it."""
    response = requests.post(
        _token_url(),
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=settings.KEYCLOAK_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


@dataclass(frozen=True)
class TemporaryUser:
    sub: str
    mobile: str
    email: str
    password: str


def unique_mobile() -> str:
    """09 + 0 + kind 9 + six random digits: outside the seeded range (data rules, section 5)."""
    return f"0900{TEMPORARY_KIND_CODE}{secrets.randbelow(10**6):06d}"


@contextmanager
def temporary_user(role: str = "student", consultant_type: str = "") -> Iterator[TemporaryUser]:
    """A throwaway user in Keycloak, deleted afterwards, so no test touches a seeded one."""
    mobile = unique_mobile()
    user = TemporaryUser(
        sub="",
        mobile=mobile,
        email=f"temp.{mobile}@gradian.test",
        password=secrets.token_urlsafe(12) + "aA1",
    )
    sub = admin_client.get_admin_client().create_user(
        admin_client.NewUser(
            mobile=mobile,
            email=user.email,
            first_name="موقت",
            last_name="آزمون",
            password=user.password,
            role=role,
            consultant_type=consultant_type,
        )
    )
    try:
        yield TemporaryUser(sub, mobile, user.email, user.password)
    finally:
        remove_user(sub)


def remove_user(sub: str) -> None:
    config = get_config()
    requests.delete(
        f"{config.admin_url}/users/{sub}",
        headers=ServiceTokenClient().auth_headers(),
        timeout=config.timeout,
    )
