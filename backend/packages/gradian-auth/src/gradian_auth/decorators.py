"""Access rules for plain Django views. They need `KeycloakAuthMiddleware`.

    @require_user("student", "professor")   # a person with one of these panel roles
    @require_user()                          # any signed-in person
    @require_service                         # a platform service (client-credentials token)

No token is answered 401 `not_authenticated`, the wrong kind of caller 403 `permission_denied`.
Without the middleware nobody is ever authenticated, so every view stays closed.
"""

import functools
from collections.abc import Callable
from typing import Concatenate, ParamSpec

from django.http import HttpRequest, HttpResponse

from gradian_auth.errors import ApiError, NotAuthenticatedError, PermissionDeniedError
from gradian_auth.middleware import error_response
from gradian_auth.oidc import login_redirect
from gradian_auth.principals import Principal, ServicePrincipal, UserPrincipal

_SAFE = {"GET", "HEAD"}
P = ParamSpec("P")
View = Callable[Concatenate[HttpRequest, P], HttpResponse]


def current_principal(request: HttpRequest) -> Principal | None:
    principal: Principal | None = getattr(request, "principal", None)
    return principal


def _check(request: HttpRequest, roles: tuple[str, ...], service: bool) -> ApiError | None:
    principal = current_principal(request)
    if principal is None:
        return NotAuthenticatedError()
    if service:
        return None if isinstance(principal, ServicePrincipal) else PermissionDeniedError()
    if not isinstance(principal, UserPrincipal):
        return PermissionDeniedError()
    if roles and principal.panel not in roles:
        return PermissionDeniedError()
    return None


def _guard(
    roles: tuple[str, ...], service: bool, page: bool = False
) -> Callable[[View[P]], View[P]]:
    def decorator(view: View[P]) -> View[P]:
        @functools.wraps(view)
        def wrapper(request: HttpRequest, /, *args: P.args, **kwargs: P.kwargs) -> HttpResponse:
            refusal = _check(request, roles, service)
            if refusal is not None:
                if page and isinstance(refusal, NotAuthenticatedError) and request.method in _SAFE:
                    return login_redirect(request)
                return error_response(refusal)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def require_user(*roles: str) -> Callable[[View[P]], View[P]]:
    if roles and callable(roles[0]):
        raise TypeError("use @require_user() with parentheses, or @require_user('student', ...)")
    return _guard(tuple(roles), service=False)


def require_page_user(*roles: str) -> Callable[[View[P]], View[P]]:
    """Like `require_user`, for a page: a visitor who is not signed in is sent to sign in (and
    comes back to the page) instead of getting a JSON 401. Needs `gradian_auth.oidc_urls`."""
    if roles and callable(roles[0]):
        raise TypeError("use @require_page_user() with parentheses")
    return _guard(tuple(roles), service=False, page=True)


def require_service[**Q](view: View[Q]) -> View[Q]:
    return _guard((), service=True)(view)


__all__ = ["current_principal", "require_page_user", "require_service", "require_user"]
