from typing import Any

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FieldOfStudy, Profile, Role
from accounts.permissions import IsStudentPanelUser
from accounts.principals import CoreUserPrincipal
from common.pagination import LimitOffsetPagination
from common.schema import FORBIDDEN, UNAUTHENTICATED, error
from common.throttling import PublicRateThrottle
from gradian_auth.drf import IsPanelUser
from panels.content import LANDING_SECTIONS, WIDGETS
from panels.countdown import countdown
from panels.models import ContentBlock, Notification
from panels.serializers import (
    DashboardSerializer,
    LandingSerializer,
    NotificationSerializer,
    PanelSerializer,
)

FIELD_OF_STUDY_LABELS = {
    FieldOfStudy.EXPERIMENTAL: "علوم تجربی",
    FieldOfStudy.MATHEMATICS: "ریاضی و فیزیک",
    FieldOfStudy.HUMANITIES: "علوم انسانی",
}


def konkur_countdown() -> dict[str, Any]:
    return countdown(settings.KONKUR_DATE, timezone.localdate())


def blocks(prefix: str, names: tuple[str, ...]) -> dict[str, Any]:
    """The content of `prefix.<name>` for each name, null for a block that is missing."""
    stored = {
        block.key: block.data
        for block in ContentBlock.objects.filter(key__in=[f"{prefix}.{name}" for name in names])
    }
    return {name: stored.get(f"{prefix}.{name}") for name in names}


def profile_of(request: Request) -> Profile:
    user = request.user
    if not isinstance(user, CoreUserPrincipal):  # the permission classes make this unreachable
        raise PermissionDenied
    return user.profile


class LandingView(APIView):
    """What an anonymous visitor sees (SYS-ACC-01, SYS-PNL-04)."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (PublicRateThrottle,)

    @extend_schema(
        tags=["Panels"],
        summary="Landing page content",
        description=(
            "Public. Navbar, hero, statistics, mission cards, teacher and top-ranker showcase, "
            "testimonials and footer. Demo content that can be changed in the Django admin."
        ),
        responses={
            200: LandingSerializer,
            429: error("`throttled`: too many requests; see `details.retry_after_seconds`."),
        },
    )
    def get(self, request: Request) -> Response:
        return Response(blocks("landing", tuple(LANDING_SECTIONS)))


class PanelView(APIView):
    permission_classes = (IsPanelUser,)

    @extend_schema(
        tags=["Panels"],
        summary="Header and countdown of my panel",
        description=(
            "The full name for the panel header, the field of study for a student, and the "
            "Konkur countdown for the sidebar."
        ),
        responses={200: PanelSerializer, 401: UNAUTHENTICATED, 403: FORBIDDEN},
    )
    def get(self, request: Request) -> Response:
        profile = profile_of(request)
        student = profile.role == Role.STUDENT
        field = profile.field_of_study
        label = FIELD_OF_STUDY_LABELS.get(FieldOfStudy(field)) if student and field else None
        return Response(
            {
                "panel": profile.role,
                "home_path": profile.home_path,
                "header": {
                    "full_name": profile.full_name,
                    "avatar_url": profile.avatar_url,
                    "consultant_type": profile.consultant_type or None,
                    "field_of_study": field if student else None,
                    "field_of_study_label": label,
                },
                "countdown": konkur_countdown(),
            }
        )


class StudentDashboardView(APIView):
    permission_classes = (IsStudentPanelUser,)

    @extend_schema(
        tags=["Panels"],
        summary="Student dashboard widgets",
        description=(
            "Student panel only. The welcome message for this student, the countdown, the study "
            "streak and a preview of the experience feed. The streak and the feed are demo content."
        ),
        responses={200: DashboardSerializer, 401: UNAUTHENTICATED, 403: FORBIDDEN},
    )
    def get(self, request: Request) -> Response:
        profile = profile_of(request)
        widgets = blocks("widget", tuple(WIDGETS))
        welcome = widgets["welcome"]
        if welcome is not None:
            message = str(welcome["message"])
            message = message.replace("{first_name}", profile.first_name)
            message = message.replace("{full_name}", profile.full_name)
            welcome = {**welcome, "message": message}
        return Response(
            {
                "welcome": welcome,
                "countdown": konkur_countdown(),
                "study_streak": widgets["study_streak"],
                "experience_feed": widgets["experience_feed"],
            }
        )


class UnreadCountPagination(LimitOffsetPagination):
    """The usual envelope plus how many notifications are unread."""

    unread_count = 0

    def get_paginated_response(self, data: Any) -> Response:
        response = super().get_paginated_response(data)
        response.data = {"unread_count": self.unread_count, **response.data}
        return response

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        described = super().get_paginated_response_schema(schema)
        properties = {"unread_count": {"type": "integer", "example": 0}, **described["properties"]}
        return {
            **described,
            "properties": properties,
            "required": ["unread_count", *described.get("required", [])],
        }


class NotificationListView(ListAPIView[Notification]):
    """The bell. Display-only and empty unless someone creates notifications (DES-API-05)."""

    permission_classes = (IsPanelUser,)
    serializer_class = NotificationSerializer
    pagination_class = UnreadCountPagination

    def get_queryset(self) -> Any:
        return Notification.objects.filter(profile=profile_of(self.request))

    def paginate_queryset(self, queryset: Any) -> Any:
        self.paginator.unread_count = queryset.filter(read_at__isnull=True).count()  # type: ignore[union-attr]
        return super().paginate_queryset(queryset)

    @extend_schema(
        tags=["Panels"],
        summary="Notifications for the bell",
        description="Newest first, with the number of unread ones. Empty by default.",
        responses={200: NotificationSerializer(many=True), 401: UNAUTHENTICATED, 403: FORBIDDEN},
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)
