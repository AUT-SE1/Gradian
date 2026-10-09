import logging
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.errors import IdentityConflictError
from accounts.principals import CoreUserPrincipal
from accounts.serializers import AuthConfigSerializer, MeSerializer, MeUpdateSerializer
from common.schema import CONFLICT, FORBIDDEN, PROVIDER_DOWN, UNAUTHENTICATED, error
from common.throttling import PublicRateThrottle
from gradian_auth.drf import IsPanelUser
from gradian_auth.errors import IdentityProviderUnavailableError
from gradian_keycloak import admin_client
from gradian_keycloak.config import get_config
from gradian_keycloak.errors import KeycloakError

logger = logging.getLogger("gradian.accounts")


class AuthConfigView(APIView):
    """What the frontend needs to start the Authorization Code + PKCE flow (DES-AUTH-05)."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (PublicRateThrottle,)

    @extend_schema(
        tags=["Auth"],
        summary="Sign-in settings for the frontend",
        description="Public. The issuer, client id and URLs the frontend needs to sign in and out.",
        responses={
            200: AuthConfigSerializer,
            429: error("`throttled`: too many requests; see `details.retry_after_seconds`."),
        },
    )
    def get(self, request: Request) -> Response:
        issuer = get_config().issuer
        data = {
            "issuer": issuer,
            "registration_endpoint": (f"{issuer}/protocol/openid-connect/registrations"),
            "realm": settings.KEYCLOAK_REALM,
            "client_id": settings.KEYCLOAK_WEB_CLIENT_ID,
            "end_session_url": f"{issuer}/protocol/openid-connect/logout",
            "landing_url": settings.FRONTEND_URL + "/",
        }
        return Response(AuthConfigSerializer(data).data)


class MeView(APIView):
    permission_classes = (IsPanelUser,)

    def _profile(self, request: Request) -> Any:
        user = request.user
        if not isinstance(user, CoreUserPrincipal):  # IsPanelUser makes this unreachable
            raise PermissionDenied
        return user.profile

    @extend_schema(
        tags=["Identity"],
        summary="Who am I",
        description=(
            "Identity, display name, `panel` and `home_path` of the caller. The profile is created "
            "on the first call and refreshed from the token when its claims changed."
        ),
        responses={
            200: MeSerializer,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            409: CONFLICT,
            502: PROVIDER_DOWN,
        },
    )
    def get(self, request: Request) -> Response:
        return Response(MeSerializer(self._profile(request)).data)

    @extend_schema(
        tags=["Identity"],
        summary="Change my profile",
        description=(
            "Email and names are written to Keycloak first and cached only if Keycloak accepts "
            "them. Field of study, avatar and bio are stored here. Mobile number and role cannot "
            "be changed."
        ),
        request=MeUpdateSerializer,
        examples=[
            OpenApiExample(
                "Change the name and bio",
                value={"first_name": "محمد", "bio": "دانشجوی سال اول"},
                request_only=True,
            )
        ],
        responses={
            200: MeSerializer,
            400: error("`validation_error`: `details` maps each invalid field to its problems."),
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            409: CONFLICT,
            502: PROVIDER_DOWN,
        },
    )
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
                admin_client.get_admin_client().update_user(str(profile.sub), identity_changes)
            except KeycloakError as exc:
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
