from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.principals import CoreUserPrincipal
from common.schema import FORBIDDEN, UNAUTHENTICATED
from gradian_auth.drf import IsPanelUser
from registry.models import ServiceEntry
from registry.serializers import ServiceEntrySerializer


class PanelServicesView(ListAPIView[ServiceEntry]):
    """The services of the caller's own panel, in display order (DES-API-02)."""

    permission_classes = (IsPanelUser,)
    serializer_class = ServiceEntrySerializer

    def get_queryset(self) -> QuerySet[ServiceEntry]:
        request: Request = self.request
        user = request.user
        if not isinstance(user, CoreUserPrincipal):  # IsPanelUser makes this unreachable
            return ServiceEntry.objects.none()
        return ServiceEntry.objects.filter(panel=user.panel).order_by("order", "key")

    @extend_schema(
        tags=["Panels"],
        summary="Services of my panel",
        description=(
            "Every entry of the caller's panel, in display order. An entry that is disabled or has "
            "no target URL is still listed, with `status: unavailable` and `url: null`, so the "
            "panel can show it as not connected yet."
        ),
        responses={200: ServiceEntrySerializer(many=True), 401: UNAUTHENTICATED, 403: FORBIDDEN},
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)
