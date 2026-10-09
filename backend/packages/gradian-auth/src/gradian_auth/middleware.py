"""Authentication for plain Django views (no Django REST Framework needed).

    MIDDLEWARE = [..., "gradian_auth.middleware.KeycloakAuthMiddleware"]

Every request gets `request.principal` (the caller, or None) and `request.claims`. A bad token is
answered with 401 here; a missing token is left to the decorators in `gradian_auth.decorators`.
"""

from collections.abc import Callable
from typing import Any, cast

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from gradian_auth import context
from gradian_auth.authenticate import AUTHENTICATE_HEADER, authenticate_token, parse_bearer
from gradian_auth.errors import ApiError
from gradian_auth.principals import Principal

DEFAULT_PUBLIC_PATHS = ("/health",)


class AuthenticatedRequest(HttpRequest):
    """What `request` looks like after the middleware ran."""

    principal: Principal | None
    claims: dict[str, Any] | None


def error_response(exc: ApiError) -> JsonResponse:
    response = JsonResponse(
        exc.body(), status=exc.status_code, json_dumps_params={"ensure_ascii": False}
    )
    if exc.status_code == 401:
        response["WWW-Authenticate"] = AUTHENTICATE_HEADER
    return response


def _is_public(path: str) -> bool:
    prefixes = getattr(settings, "GRADIAN_PUBLIC_PATHS", DEFAULT_PUBLIC_PATHS)
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


class KeycloakAuthMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        authenticated = cast(AuthenticatedRequest, request)
        authenticated.principal = None
        authenticated.claims = None
        reset = context.user_sub.set("-")
        try:
            if not _is_public(request.path):
                header = request.META.get("HTTP_AUTHORIZATION", "").encode("latin-1", "replace")
                try:
                    token = parse_bearer(header)
                    if token is not None:
                        authenticated.principal, authenticated.claims = authenticate_token(token)
                except ApiError as exc:
                    return error_response(exc)
            return self.get_response(request)
        finally:
            context.user_sub.reset(reset)
