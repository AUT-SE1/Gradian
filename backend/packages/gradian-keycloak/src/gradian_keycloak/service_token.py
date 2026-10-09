"""The access token of this service's own Keycloak client (client-credentials grant)."""

import threading
import time
from collections.abc import Callable

import requests
from django.core.exceptions import ImproperlyConfigured

from gradian_keycloak.config import get_config
from gradian_keycloak.errors import KeycloakError

EXPIRY_MARGIN_SECONDS = 30.0


class ServiceTokenClient:
    """Fetches a token for `KEYCLOAK_CLIENT_ID` and reuses it until shortly before it expires.

    Safe to share between threads: one thread fetches while the others wait for the result.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._token = ""
        self._expires_at = 0.0

    def clear(self) -> None:
        with self._lock:
            self._token = ""
            self._expires_at = 0.0

    def access_token(self) -> str:
        with self._lock:
            if self._token and self._clock() < self._expires_at - EXPIRY_MARGIN_SECONDS:
                return self._token
            config = get_config()
            if not config.client_secret:
                raise ImproperlyConfigured(
                    "Missing setting KEYCLOAK_CLIENT_SECRET, needed to get a service token."
                )
            try:
                response = requests.post(
                    config.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                    },
                    timeout=config.timeout,
                )
                response.raise_for_status()
                body = response.json()
                self._token = str(body["access_token"])
                self._expires_at = self._clock() + float(body.get("expires_in", 60))
            except (requests.RequestException, ValueError, KeyError) as exc:
                self._token = ""
                raise KeycloakError("could not obtain a service token") from exc
            return self._token

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token()}"}
