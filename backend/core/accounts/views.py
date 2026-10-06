import logging
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import keycloak
from accounts.errors import IdentityConflictError, IdentityProviderUnavailableError
from accounts.permissions import IsPanelUser
from accounts.principals import UserPrincipal
from accounts.serializers import AuthConfigSerializer, MeSerializer, MeUpdateSerializer
from common.throttling import PublicRateThrottle

logger = logging.getLogger("gradian.accounts")


class AuthConfigView(APIView):
    """What the frontend needs to start the Authorization Code + PKCE flow (DES-AUTH-05)."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (PublicRateThrottle,)

    @extend_schema(responses=AuthConfigSerializer)
    def get(self, request: Request) -> Response:
        data = {
            "issuer": settings.KEYCLOAK_ISSUER,
            "realm": settings.KEYCLOAK_REALM,
            "client_id": settings.KEYCLOAK_WEB_CLIENT_ID,
            "end_session_url": f"{settings.KEYCLOAK_ISSUER}/protocol/openid-connect/logout",
            "landing_url": settings.FRONTEND_URL + "/",
        }
        return Response(AuthConfigSerializer(data).data)


class MeView(APIView):
    permission_classes = (IsPanelUser,)

    def _profile(self, request: Request) -> Any:
        user = request.user
        if not isinstance(user, UserPrincipal):  # IsPanelUser makes this unreachable
            raise PermissionDenied
        return user.profile

    @extend_schema(responses=MeSerializer)
    def get(self, request: Request) -> Response:
        return Response(MeSerializer(self._profile(request)).data)

    @extend_schema(request=MeUpdateSerializer, responses=MeSerializer)
    def patch(self, request: Request) -> Response:
        """Identity changes go to Keycloak first; the cache changes only if Keycloak accepts
        them (DES-ID-05)."""
        profile = self._profile(request)
        serializer = MeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        identity_changes = {
            field: data[field]
            for field in MeUpdateSerializer.IDENTITY_FIELDS
            if field in data and getattr(profile, field) != data[field]
        }
        if identity_changes:
            try:
                keycloak.get_admin_client().update_user(str(profile.sub), identity_changes)
            except keycloak.KeycloakError as exc:
                logger.warning(
                    "identity write-through failed",
                    extra={"event": "write_through_failed", "status": exc.status},
                )
                if exc.status == 409:
                    raise IdentityConflictError from None
                raise IdentityProviderUnavailableError from None

        try:
            with transaction.atomic():
                for field, value in data.items():
                    setattr(profile, field, value)
                fields = [*data, "updated_at"]
                if identity_changes:
                    profile.identity_synced_at = timezone.now()
                    fields.append("identity_synced_at")
                profile.save(update_fields=fields)
        except IntegrityError:
            raise IdentityConflictError from None
        return Response(MeSerializer(profile).data)
