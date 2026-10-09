"""Views the adapter tests call."""

from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import include, path
from rest_framework import serializers
from rest_framework.exceptions import Throttled
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from gradian_auth.decorators import (
    current_principal,
    require_page_user,
    require_service,
    require_user,
)
from gradian_auth.drf import (
    HasPanelRole,
    IsPanelUser,
    IsPlatformService,
    KeycloakBearerAuthentication,
)
from gradian_auth.errors import ApiError
from gradian_auth.principals import ServicePrincipal, UserPrincipal


def who(request: HttpRequest) -> dict[str, Any]:
    principal = current_principal(request)
    if isinstance(principal, UserPrincipal):
        return {"kind": "user", "sub": principal.sub, "panel": principal.panel}
    if isinstance(principal, ServicePrincipal):
        return {"kind": "service", "client_id": principal.client_id}
    return {"kind": "anonymous"}


def open_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(who(request))


@require_user()
def any_user(request: HttpRequest) -> JsonResponse:
    return JsonResponse(who(request))


@require_user("student", "professor")
def students_and_professors(request: HttpRequest, number: int) -> JsonResponse:
    return JsonResponse({**who(request), "number": number})


@require_service
def services_only(request: HttpRequest) -> JsonResponse:
    return JsonResponse(who(request))


@require_page_user("student")
def student_page(request: HttpRequest) -> JsonResponse:
    return JsonResponse(who(request))


def health(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


class Admins(HasPanelRole):
    allowed_roles = ("admin",)


class DrfWho(APIView):
    authentication_classes = (KeycloakBearerAuthentication,)
    permission_classes = (IsPanelUser,)

    def get(self, request: Request) -> Response:
        user = request.user
        assert isinstance(user, UserPrincipal)
        return Response({"sub": user.sub, "panel": user.panel})


class DrfAdmin(APIView):
    authentication_classes = (KeycloakBearerAuthentication,)
    permission_classes = (Admins,)

    def get(self, request: Request) -> Response:
        return Response({"ok": True})


class DrfService(APIView):
    authentication_classes = (KeycloakBearerAuthentication,)
    permission_classes = (IsPlatformService,)

    def get(self, request: Request) -> Response:
        return Response({"ok": True})


class TeapotError(ApiError):
    status_code = 418
    default_code = "server_error"


class Needs(serializers.Serializer[Any]):
    name = serializers.CharField()


class DrfFails(APIView):
    authentication_classes = (KeycloakBearerAuthentication,)
    permission_classes = (IsPanelUser,)

    def get(self, request: Request, kind: str) -> Response:
        if kind == "api":
            raise TeapotError(details={"why": "test"})
        if kind == "throttled":
            raise Throttled(wait=7)
        if kind == "invalid":
            Needs(data={}).is_valid(raise_exception=True)
        raise RuntimeError("boom")


urlpatterns = [
    path("open", open_view),
    path("any", any_user),
    path("classes/<int:number>", students_and_professors),
    path("service", services_only),
    path("page", student_page),
    path("auth/", include("gradian_auth.oidc_urls")),
    path("health", health),
    path("health/deep", health),
    path("drf/who", DrfWho.as_view()),
    path("drf/admin", DrfAdmin.as_view()),
    path("drf/service", DrfService.as_view()),
    path("drf/fails/<str:kind>", DrfFails.as_view()),
]
