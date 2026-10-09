"""What an administrator may do to accounts (DES-ADM-01 to DES-ADM-04).

Every change is written to Keycloak first and cached only after Keycloak accepts it, as in
`PATCH /me` (DEC-08). Role and name changes reach a person's already issued token only when it
expires; the cache is updated at once.
"""

import logging
import uuid
from collections.abc import Mapping
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts import keycloak
from accounts.errors import (
    IdentityConflictError,
    IdentityProviderUnavailableError,
    SelfModificationError,
)
from accounts.models import Profile, Role

logger = logging.getLogger("gradian.accounts")

SELF_PROTECTED = {"role", "consultant_type", "is_active"}


def _keycloak_failed(exc: keycloak.KeycloakError, event: str) -> Exception:
    logger.warning("user management failed", extra={"event": event, "status": exc.status})
    return IdentityConflictError() if exc.status == 409 else IdentityProviderUnavailableError()


def _consultant_type(role: str, requested: str, current: str) -> str:
    if role != Role.CONSULTANT:
        return ""
    chosen = requested or current
    if not chosen:
        raise ValidationError({"consultant_type": ["Required for consultants."]})
    return chosen


def create_user(data: Mapping[str, Any]) -> Profile:
    if Profile.objects.filter(Q(mobile=data["mobile"]) | Q(email=data["email"])).exists():
        raise IdentityConflictError
    consultant_type = _consultant_type(data["role"], data.get("consultant_type", ""), "")
    try:
        sub = keycloak.get_admin_client().create_user(
            keycloak.NewUser(
                mobile=data["mobile"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                password=data["password"],
                role=data["role"],
                consultant_type=consultant_type,
            )
        )
    except keycloak.KeycloakError as exc:
        raise _keycloak_failed(exc, "admin_create_failed") from None
    try:
        profile = Profile.objects.create(
            sub=uuid.UUID(sub),
            mobile=data["mobile"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data["role"],
            consultant_type=consultant_type,
            field_of_study=data.get("field_of_study", ""),
        )
    except IntegrityError:
        raise IdentityConflictError from None
    logger.info("user created by an administrator", extra={"event": "admin_user_created"})
    return profile


def update_user(profile: Profile, changes: Mapping[str, Any], actor_sub: str) -> Profile:
    if str(profile.sub) == actor_sub and SELF_PROTECTED & changes.keys():
        raise SelfModificationError

    role = changes.get("role", profile.role)
    consultant_type = _consultant_type(
        role, changes.get("consultant_type", ""), profile.consultant_type
    )
    names = {"email": "email", "first_name": "first_name", "last_name": "last_name"}
    identity = {f: changes[f] for f in names if f in changes and getattr(profile, f) != changes[f]}
    role_changed = role != profile.role or consultant_type != profile.consultant_type
    enabled_changed = "is_active" in changes and changes["is_active"] != profile.is_active

    admin = keycloak.get_admin_client()
    try:
        if identity:
            admin.update_user(str(profile.sub), identity)
        if role_changed:
            admin.set_panel_role(str(profile.sub), role, consultant_type)
        if enabled_changed:
            admin.set_enabled(str(profile.sub), changes["is_active"])
    except keycloak.KeycloakError as exc:
        raise _keycloak_failed(exc, "admin_update_failed") from None

    try:
        with transaction.atomic():
            for field in (*identity, "field_of_study", "is_active"):
                if field in changes:
                    setattr(profile, field, changes[field])
            profile.role, profile.consultant_type = role, consultant_type
            if identity or role_changed:
                profile.identity_synced_at = timezone.now()
            profile.save()
    except IntegrityError:
        raise IdentityConflictError from None
    logger.info(
        "user changed by an administrator",
        extra={"event": "admin_user_changed", "fields": sorted(changes)},
    )
    return profile
