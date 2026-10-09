"""Sign-in for the pages of a group service that people reach by redirect (DEC-26).

The person is already signed in at Keycloak, so a group's page sends them there and they come
straight back, with no second login (single sign-on). The service signs them in with its own
confidential client (`KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`) through the Authorization
Code flow, then keeps the access token in an HttpOnly cookie. The middleware reads that cookie as
it reads a Bearer header, so the token is validated the same way on every request and the cookie
never outlives the token: when it expires, the next visit signs in again, which also picks up a
changed role.

    # urls.py
    path("auth/", include("gradian_auth.oidc_urls")),

    # settings.py
    GRADIAN_SERVICE_URL = "http://localhost:8001"     # this service, as the browser reaches it
    GRADIAN_FRONTEND_URL = "http://localhost:5173"    # where the panel lives
    GRADIAN_COOKIE_AUTH = True
    GRADIAN_PUBLIC_PATHS = ("/health", "/auth")
"""

import base64
import hashlib
import json
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.signing import BadSignature
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from gradian_auth.authenticate import authenticate_token
from gradian_auth.cookies import TOKEN_COOKIE
from gradian_auth.errors import (
    ApiError,
    IdentityProviderUnavailableError,
    InvalidLoginError,
)
from gradian_auth.middleware import error_response
from gradian_auth.principals import Principal, UserPrincipal
from gradian_auth.roles import HOME_PATHS
from gradian_keycloak.config import get_config

STATE_COOKIE = "gradian_oidc"
STATE_MAX_AGE_SECONDS = 600
CALLBACK_PATH = "/auth/callback"
LOGIN_PATH = "/auth/login"
TIMEOUT_SECONDS = 10


def _setting(name: str) -> str:
    value = getattr(settings, name, "")
    if not value:
        raise ImproperlyConfigured(f"Missing setting {name}. See the gradian-auth README.")
    return str(value).rstrip("/")


def service_url() -> str:
    return _setting("GRADIAN_SERVICE_URL")


def frontend_url() -> str:
    return _setting("GRADIAN_FRONTEND_URL")


def redirect_uri() -> str:
    return service_url() + CALLBACK_PATH


def panel_url(principal: Principal | None) -> str:
    """Where the person's own panel is, for the link back from a redirected page."""
    path = HOME_PATHS[principal.panel] if isinstance(principal, UserPrincipal) else "/"
    return frontend_url() + path


def safe_next(value: str | None) -> str:
    """A path on this service, or `/`. Anything that could leave the site is refused."""
    if not value or not value.startswith("/") or value.startswith(("//", "/\\")):
        return "/"
    if any(ord(char) < 32 for char in value):
        return "/"
    return value


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def authorization_url(state: str, challenge: str) -> str:
    config = get_config()
    query = urlencode(
        {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri(),
            "response_type": "code",
            "scope": "openid",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{config.issuer}/protocol/openid-connect/auth?{query}"


def _secure_cookies() -> bool:
    return service_url().startswith("https://")


def _pack(values: dict[str, str]) -> str:
    """Plain letters and digits only: quotes and commas in a cookie value do not survive every
    client."""
    return base64.urlsafe_b64encode(json.dumps(values).encode()).decode("ascii")


def _unpack(text: str) -> dict[str, Any]:
    decoded = json.loads(base64.urlsafe_b64decode(text.encode("ascii")))
    if not isinstance(decoded, dict):
        raise ValueError("not an object")
    return decoded


def login(request: HttpRequest) -> HttpResponse:
    """Send the browser to Keycloak. With a session there it returns at once."""
    state = secrets.token_urlsafe(24)
    verifier, challenge = pkce_pair()
    remembered = {"state": state, "verifier": verifier, "next": safe_next(request.GET.get("next"))}
    response = HttpResponseRedirect(authorization_url(state, challenge))
    response.set_signed_cookie(
        STATE_COOKIE,
        _pack(remembered),
        max_age=STATE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="Lax",
        secure=_secure_cookies(),
    )
    return response


def _exchange(code: str, verifier: str) -> str:
    config = get_config()
    if not config.client_secret:
        raise ImproperlyConfigured(
            "Missing setting KEYCLOAK_CLIENT_SECRET, needed to sign people in."
        )
    try:
        reply = requests.post(
            config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri(),
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code_verifier": verifier,
            },
            timeout=config.timeout,
        )
    except requests.RequestException:
        raise IdentityProviderUnavailableError from None
    if reply.status_code >= 500:
        raise IdentityProviderUnavailableError
    if reply.status_code != 200:
        raise InvalidLoginError
    try:
        return str(reply.json()["access_token"])
    except (ValueError, KeyError):
        raise InvalidLoginError from None


def callback(request: HttpRequest) -> HttpResponse:
    """Finish the sign-in: check `state`, trade the code for a token, keep it in a cookie."""
    try:
        raw = request.get_signed_cookie(STATE_COOKIE, max_age=STATE_MAX_AGE_SECONDS)
        remembered = _unpack(str(raw))
    except (KeyError, BadSignature, ValueError):
        return error_response(InvalidLoginError())
    code = request.GET.get("code", "")
    got_state = request.GET.get("state", "")
    if (
        "error" in request.GET
        or not code
        or not secrets.compare_digest(got_state, str(remembered.get("state", "")))
    ):
        return error_response(InvalidLoginError())
    try:
        token = _exchange(code, str(remembered.get("verifier", "")))
        _, claims = authenticate_token(token)
    except ApiError as exc:
        return error_response(exc)
    response = HttpResponseRedirect(safe_next(str(remembered.get("next", "/"))))
    remaining = max(int(claims["exp"]) - int(time.time()), 1)
    response.set_cookie(
        TOKEN_COOKIE,
        token,
        max_age=remaining,
        httponly=True,
        samesite="Lax",
        secure=_secure_cookies(),
    )
    response.delete_cookie(STATE_COOKIE)
    return response


def logout(request: HttpRequest) -> HttpResponse:
    """End the session here and at Keycloak, then go back to the panel's landing page."""
    config = get_config()
    query = urlencode(
        {"client_id": config.client_id, "post_logout_redirect_uri": frontend_url() + "/"}
    )
    response = HttpResponseRedirect(f"{config.issuer}/protocol/openid-connect/logout?{query}")
    response.delete_cookie(TOKEN_COOKIE)
    return response


def login_redirect(request: HttpRequest) -> HttpResponse:
    """Where an anonymous visitor of a page goes: the sign-in, then back to the page."""
    return HttpResponseRedirect(f"{LOGIN_PATH}?{urlencode({'next': request.get_full_path()})}")
