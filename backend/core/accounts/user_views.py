"""Account management for administrators (DES-ADM-01 to DES-ADM-04)."""

from collections.abc import Mapping
from typing import Any

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import user_management
from accounts.models import Profile
from accounts.permissions import IsAdminPanelUser
from accounts.serializers import (
    UserCreateSerializer,
    UserFilterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from common.schema import CONFLICT, FORBIDDEN, NOT_FOUND, PROVIDER_DOWN, UNAUTHENTICATED, error
from gradian_auth.principals import UserPrincipal

VALIDATION = error("`validation_error`: `details` maps each invalid field to its problems.")


def filtered_users(params: Mapping[str, Any]) -> QuerySet[Profile]:
    """Accounts matching the `role`, `is_active` and `q` query parameters, in a stable order."""
    query = UserFilterSerializer(data=params)
    query.is_valid(raise_exception=True)
    filters = query.validated_data
    users = Profile.objects.order_by("last_name", "first_name", "mobile")
    if "role" in filters:
        users = users.filter(role=filters["role"])
    if filters.get("is_active") is not None:
        users = users.filter(is_active=filters["is_active"])
    if text := filters.get("q"):
        users = users.filter(
            Q(mobile__contains=text)
            | Q(email__icontains=text)
            | Q(first_name__icontains=text)
            | Q(last_name__icontains=text)
        )
    return users


class UserListCreateView(GenericAPIView[Profile]):
    permission_classes = (IsAdminPanelUser,)
    serializer_class = UserSerializer

    def get_queryset(self) -> QuerySet[Profile]:
        if getattr(self, "swagger_fake_view", False):
            return Profile.objects.none()
        return filtered_users(self.request.query_params)

    @extend_schema(
        tags=["Admin users"],
        operation_id="admin_users_list",
        summary="List accounts",
        description="Admin panel only. Paginated with `limit` and `offset`.",
        parameters=[UserFilterSerializer],
        responses={
            200: UserSerializer(many=True),
            400: VALIDATION,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
        },
    )
    def get(self, request: Request) -> Response:
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(UserSerializer(page, many=True).data)

    @extend_schema(
        tags=["Admin users"],
        summary="Create an account of any role",
        description=(
            "Admin panel only. The account is created in Keycloak with its role and password and "
            "can sign in at once. A consultant needs `consultant_type`."
        ),
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: VALIDATION,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            409: CONFLICT,
            502: PROVIDER_DOWN,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = user_management.create_user(serializer.validated_data)
        return Response(UserSerializer(profile).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = (IsAdminPanelUser,)

    @extend_schema(
        tags=["Admin users"],
        operation_id="admin_users_retrieve",
        summary="One account",
        responses={
            200: UserSerializer,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def get(self, request: Request, sub: str) -> Response:
        return Response(UserSerializer(get_object_or_404(Profile, sub=sub)).data)

    @extend_schema(
        tags=["Admin users"],
        summary="Change an account, including its role",
        description=(
            "Admin panel only. Changing `role` makes it the person's only panel role; a "
            "consultant keeps or needs a `consultant_type`. `is_active: false` blocks sign-in. "
            "The new role reaches a token that is already issued only when it expires. "
            "Administrators cannot change their own role or status."
        ),
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: VALIDATION,
            401: UNAUTHENTICATED,
            403: FORBIDDEN,
            404: NOT_FOUND,
            409: CONFLICT,
            502: PROVIDER_DOWN,
        },
    )
    def patch(self, request: Request, sub: str) -> Response:
        profile = get_object_or_404(Profile, sub=sub)
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        actor = request.user
        actor_sub: Any = actor.sub if isinstance(actor, UserPrincipal) else ""
        profile = user_management.update_user(profile, serializer.validated_data, actor_sub)
        return Response(UserSerializer(profile).data)
