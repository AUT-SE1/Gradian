import urllib.error
import urllib.request

from django.conf import settings
from django.http import HttpResponse, JsonResponse

from .auth import role_required

HOME = {
    "admin": "/api/admin-panel/",
    "candidate": "/api/candidate/",
    "advisor": "/api/advisor/",
    "instructor": "/api/instructor/",  # TODO: instructor features TBD
}

ADMIN_FEATURES = ["question-bank", "adviser-meetings", "shop-items"]
ADVISOR_FEATURES = [
    "profile", "student-reports", "academic-tutoring",
    "experiences", "online-meetings", "resource-hub",
]


@role_required()
def me(request):
    """Call right after Keycloak login: tells the client where this user belongs."""
    return JsonResponse({"phone": request.phone, "role": request.role, "redirect": HOME[request.role]})


@role_required("admin")
def admin_panel(request):
    return JsonResponse({"features": [f"/api/admin-panel/{f}/" for f in ADMIN_FEATURES]})


@role_required("advisor")
def advisor_page(request):
    return JsonResponse({"features": [f"/api/advisor/{f}/" for f in ADVISOR_FEATURES]})


@role_required("candidate")
def candidate_landing(request):
    return JsonResponse({"services": [
        {"team": i + 1, "slug": slug, "title": title,
         "url": f"/api/teams/{i + 1}/", "port": settings.TEAM_BASE_PORT + i}
        for i, (slug, title) in enumerate(settings.TEAM_SERVICES)
    ]})


def feature(role, name):
    """Placeholder GET endpoint. Students replace this with the real implementation."""
    @role_required(role)
    def view(request):
        if request.method != "GET":
            return JsonResponse({"error": "method not allowed"}, status=405)
        return JsonResponse({"feature": name, "items": []})
    return view


@role_required()
def team_proxy(request, team, path):
    """Gateway: /api/teams/<n>/<path> -> team n service /<path>, with the authenticated user in headers."""
    team = int(team)
    if not 1 <= team <= len(settings.TEAM_SERVICES):
        return JsonResponse({"error": "unknown team"}, status=404)
    url = settings.TEAM_URL.format(n=team, port=settings.TEAM_BASE_PORT + team - 1) + "/" + path
    if request.META.get("QUERY_STRING"):
        url += "?" + request.META["QUERY_STRING"]
    # Built from scratch, so a client can't smuggle its own X-User-* headers through.
    headers = {"X-User-Phone": request.phone, "X-User-Role": request.role,
               "Authorization": request.headers["Authorization"]}
    if request.content_type:
        headers["Content-Type"] = request.META.get("CONTENT_TYPE")
    req = urllib.request.Request(url, data=request.body or None, method=request.method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return HttpResponse(r.read(), status=r.status, content_type=r.headers.get("Content-Type"))
    except urllib.error.HTTPError as e:  # team answered with 4xx/5xx: pass it through
        return HttpResponse(e.read(), status=e.code, content_type=e.headers.get("Content-Type"))
    except (urllib.error.URLError, TimeoutError):
        return JsonResponse({"error": f"team {team} service is not running"}, status=502)
