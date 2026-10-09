"""The realm's public endpoints. Tests replace `fetch_jwks`; nothing else here is public."""

from typing import Any

import requests

from gradian_keycloak.config import get_config
from gradian_keycloak.errors import KeycloakError


def fetch_jwks() -> dict[str, Any]:
    config = get_config()
    try:
        response = requests.get(config.jwks_url, timeout=config.timeout)
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
