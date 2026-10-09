"""Authentication, permissions and error handling for Django REST Framework services.

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": ["gradian_auth.drf.KeycloakBearerAuthentication"],
        "EXCEPTION_HANDLER": "gradian_auth.drf.exception_handler",
        "UNAUTHENTICATED_USER": None,
        "UNAUTHENTICATED_TOKEN": None,
    }

Needs the `drf` extra: `pip install gradian-auth[drf]`.
"""

from typing import TYPE_CHECKING, Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from gradian_auth.authenticate import AUTHENTICATE_HEADER, authenticate_token, parse_bearer
from gradian_auth.errors import MESSAGES, ApiError, error_body
from gradian_auth.principals import Principal, ServicePrincipal, UserPrincipal

if TYPE_CHECKING:
    from rest_framework.views import APIView


class KeycloakBearerAuthentication(BaseAuthentication):
    """`Authorization: Bearer <access token>`. No header means anonymous (the permission
    class then answers 401); a bad token is refused here with 401."""

    def authenticate(self, request: Request) -> tuple[Principal, dict[str, Any]] | None:
        token = parse_bearer(get_authorization_header(request))
        if token is None:
            return None
        return authenticate_token(token)

    def authenticate_header(self, request: Request) -> str:
        return AUTHENTICATE_HEADER


class IsPanelUser(BasePermission):
    """Any signed-in person with a panel role."""

    def has_permission(self, request: Request, view: "APIView") -> bool:
        return isinstance(request.user, UserPrincipal)


class HasPanelRole(BasePermission):
    """Subclass and set `allowed_roles` to restrict an endpoint to given panel roles."""

    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request: Request, view: "APIView") -> bool:
        user = request.user
        return isinstance(user, UserPrincipal) and user.panel in self.allowed_roles


class IsPlatformService(BasePermission):
    """A machine client holding the `service` role (client-credentials token)."""

    def has_permission(self, request: Request, view: "APIView") -> bool:
        return isinstance(request.user, ServicePrincipal)


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Every error in the shape `{"code", "message", "details"}` (DES-API-01)."""
    # Imported here: rest_framework.views resolves the default authentication class at import
    # time, which would import this module again while it is half loaded.
    from rest_framework.views import exception_handler as drf_exception_handler
    from rest_framework.views import set_rollback

    if isinstance(exc, ApiError):
        set_rollback()  # as DRF does for its own errors, for services with ATOMIC_REQUESTS
        error = Response(exc.body(), status=exc.status_code)
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error["WWW-Authenticate"] = AUTHENTICATE_HEADER
        return error

    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.messages)
    elif isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: the host's 500 handler renders the same shape

    details: Any = {}
    if isinstance(exc, ValidationError):
        code, details = "validation_error", response.data
    elif isinstance(exc, APIException):
        codes = exc.get_codes()
        code = codes if isinstance(codes, str) else exc.default_code
        wait = getattr(exc, "wait", None)
        if wait is not None:
            details = {"retry_after_seconds": int(wait)}
    else:  # pragma: no cover - every exception drf_exception_handler answers is one of the above
        code = "server_error"
    if code not in MESSAGES:
        code = {
            status.HTTP_401_UNAUTHORIZED: "authentication_failed",
            status.HTTP_403_FORBIDDEN: "permission_denied",
        }.get(response.status_code, "server_error")
    response.data = error_body(code, details)
    return response
