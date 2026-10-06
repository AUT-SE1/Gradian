from django.http import JsonResponse

TEAM = 2
SERVICE = "assessment-exams"


def current_user(request):
    """(phone, role) of the caller. The core gateway authenticates with Keycloak and sets these headers."""
    return request.headers.get("X-User-Phone"), request.headers.get("X-User-Role")


def index(request):
    phone, role = current_user(request)
    return JsonResponse({"team": TEAM, "service": SERVICE, "phone": phone, "role": role})
