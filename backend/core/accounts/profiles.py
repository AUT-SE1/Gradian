"""Keeping the Profile cache in step with Keycloak (DES-ID-01 to DES-ID-03)."""

import logging
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.claims import Identity
from accounts.errors import IdentityConflictError
from accounts.models import Profile

logger = logging.getLogger("gradian.accounts")


def differences(profile: Profile, identity: Identity) -> list[str]:
    """Names of the identity fields whose cached value differs from `identity`."""
    return [
        field
        for field in Profile.IDENTITY_FIELDS
        if getattr(profile, field) != getattr(identity, field)
    ]


def apply_identity(profile: Profile, identity: Identity, fields: list[str]) -> None:
    for field in fields:
        setattr(profile, field, getattr(identity, field))
    profile.identity_synced_at = timezone.now()


def token_is_stale(profile: Profile, issued_at: datetime | None) -> bool:
    """True if the token was issued before the cache was last written, so refreshing from it
    could undo a newer change (for example a PATCH /me still unseen by the user's old token)."""
    if issued_at is None:
        return False
    return issued_at < profile.identity_synced_at.replace(microsecond=0)


def sync_profile(identity: Identity, issued_at: datetime | None = None) -> Profile:
    """Create the profile on first sight, or refresh it in the same request when claims differ.

    Log lines carry field names only, never values.
    """
    try:
        with transaction.atomic():
            profile, created = Profile.objects.select_for_update().get_or_create(
                sub=identity.sub,
                defaults={field: getattr(identity, field) for field in Profile.IDENTITY_FIELDS},
            )
            if created:
                logger.info("profile created", extra={"event": "profile_created"})
                return profile
            changed = [] if token_is_stale(profile, issued_at) else differences(profile, identity)
            if changed:
                apply_identity(profile, identity, changed)
                profile.save(update_fields=[*changed, "identity_synced_at", "updated_at"])
                logger.info(
                    "profile refreshed from token",
                    extra={"event": "profile_updated", "fields": changed},
                )
            return profile
    except IntegrityError:
        # The mobile number or email already belongs to a different Keycloak user.
        logger.warning("identity conflict", extra={"event": "identity_conflict"})
        raise IdentityConflictError from None
