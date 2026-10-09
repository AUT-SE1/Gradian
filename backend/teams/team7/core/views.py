from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.html import format_html

from gradian_auth.decorators import current_principal, require_page_user, require_user
from gradian_auth.oidc import panel_url
from gradian_auth.principals import UserPrincipal

TEAM = 7
SERVICE = "analysis"


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


@require_user("professor", "admin")
def staff(request: HttpRequest) -> JsonResponse:
    """Example of an endpoint restricted to some roles: anyone else gets 403."""
    return JsonResponse({"team": TEAM, "area": "staff"})


@require_page_user()
def app(request: HttpRequest) -> HttpResponse:
    """A page of this service. A person who arrives from the panel without being signed in here is
    sent to Keycloak and comes straight back (single sign-on)."""
    principal = current_principal(request)
    if not isinstance(principal, UserPrincipal):
        raise PermissionDenied
    return HttpResponse(
        format_html(
            '<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><title>{}</title>'
            "<h1>{}</h1><p>سلام {}، نقش شما: {}.</p>"
            '<p><a href="{}">بازگشت به پنل</a> · <a href="/auth/logout">خروج</a></p></html>',
            SERVICE,
            f"سرویس گروه {TEAM}",
            principal.identity.first_name,
            principal.panel,
            panel_url(principal),
        )
    )
