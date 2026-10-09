"""Real tokens from the running Keycloak, for integration tests (test plan 2.3)."""

import requests
from django.conf import settings

TEST_CLIENT_ID = "gradian-test"


def password_token(mobile: str, password: str) -> str:
    """Sign in without a browser through the test-only client (DES-IDP-09). Returns the access
    token, whose issuer is the public address whichever address the request used (DEC-18)."""
    response = requests.post(
        f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
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
