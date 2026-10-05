"""Signing-key cache (DES-AUTH-01, SYS-NFR-03).

Keys are fetched on first use and refreshed when a token names an unknown `kid`. If a refresh
fails, keys already cached keep working, so a brief Keycloak outage does not log anyone out.
"""

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import jwt
from rest_framework.exceptions import AuthenticationFailed

from accounts import keycloak
from accounts.errors import IdentityProviderUnavailableError

logger = logging.getLogger("gradian.jwks")

MIN_REFRESH_INTERVAL_SECONDS = 10.0


class JwksCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._keys: dict[str, Any] = {}
        self._last_attempt: float | None = None

    def clear(self) -> None:
        with self._lock:
            self._keys = {}
            self._last_attempt = None

    def get_key(self, kid: str | None) -> Any:
        if not kid:
            raise AuthenticationFailed(code="invalid_token")
        with self._lock:
            key = self._keys.get(kid)
            if key is not None:
                return key
            now = self._clock()
            recently_tried = (
                self._last_attempt is not None
                and now - self._last_attempt < MIN_REFRESH_INTERVAL_SECONDS
            )
            if self._keys and recently_tried:
                # Unknown kid soon after a refresh: do not let random kids cause a fetch storm.
                raise AuthenticationFailed(code="invalid_token")
            self._last_attempt = now
            try:
                document = keycloak.fetch_jwks()
            except keycloak.KeycloakError:
                logger.warning("could not refresh the signing keys")
                raise IdentityProviderUnavailableError from None
            self._keys = {
                jwk.key_id: jwk.key
                for jwk in jwt.PyJWKSet.from_dict(document).keys
                if jwk.key_id and jwk.public_key_use in (None, "sig")
            }
            key = self._keys.get(kid)
            if key is None:
                raise AuthenticationFailed(code="invalid_token")
            return key


jwks_cache = JwksCache()
