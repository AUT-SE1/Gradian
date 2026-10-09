from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse

from gradian_auth.decorators import current_principal, require_user
from gradian_auth.principals import UserPrincipal

TEAM = 5
SERVICE = "advising"


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_user()
def index(request: HttpRequest) -> JsonResponse:
    """Who is calling, from the validated Keycloak token. Authorize by `principal.panel`."""
    principal = current_principal(request)
    if not isinstance(principal, UserPrincipal):
        raise PermissionDenied
    return JsonResponse(
        {
            "team": TEAM,
            "service": SERVICE,
            "sub": principal.sub,
            "mobile": principal.identity.mobile,
            "role": principal.panel,
        }
    )
