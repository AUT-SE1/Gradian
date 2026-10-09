"""The cookie that carries the access token on the pages of a group service (see `oidc`)."""

from django.conf import settings
from django.http import HttpRequest

TOKEN_COOKIE = "gradian_token"  # noqa: S105  # the cookie's name, not a secret


def cookie_token(request: HttpRequest) -> str | None:
    """The token in the cookie, if `GRADIAN_COOKIE_AUTH` is switched on."""
    if not getattr(settings, "GRADIAN_COOKIE_AUTH", False):
        return None
    return request.COOKIES.get(TOKEN_COOKIE)
