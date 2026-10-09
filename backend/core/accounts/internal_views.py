"""What group services may ask the Core Service (DES-REG-07). They call with the client-credentials
token of their own Keycloak client, which carries the `service` role."""

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView, RetrieveAPIView

from accounts.models import Profile
from accounts.permissions import IsPlatformService
from accounts.serializers import ServiceUserSerializer, UserFilterSerializer
from accounts.user_views import filtered_users
from common.schema import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED, error

NOTE = (
    "Only people the Core Service already knows are found: seeded users, people who have "
    "signed in or registered, and people added by `sync_keycloak_users`."
)


@extend_schema_view(
    get=extend_schema(
        tags=["Internal"],
        operation_id="internal_users_list",
        summary="List users",
        description=f"Every person is valid for every group. Paginated. {NOTE}",
        parameters=[UserFilterSerializer],
        responses={
            200: ServiceUserSerializer,
            400: error("`validation_error`: a filter is not valid."),
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
        },
    )
)
class InternalUserListView(ListAPIView[Profile]):
    permission_classes = (IsPlatformService,)
    serializer_class = ServiceUserSerializer

    def get_queryset(self) -> QuerySet[Profile]:
        if getattr(self, "swagger_fake_view", False):
            return Profile.objects.none()
        return filtered_users(self.request.query_params)


@extend_schema_view(
    get=extend_schema(
        tags=["Internal"],
        operation_id="internal_users_retrieve",
        summary="Look up one user",
        description=NOTE,
        responses={
            200: ServiceUserSerializer,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
)
class InternalUserView(RetrieveAPIView[Profile]):
    permission_classes = (IsPlatformService,)
    serializer_class = ServiceUserSerializer
    queryset = Profile.objects.all()
    lookup_field = "sub"
