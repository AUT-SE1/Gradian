"""Safety net for the profile cache (DES-ID-04): reconcile every profile with Keycloak.

Creates missing profiles, updates changed ones, deactivates profiles whose user was deleted,
disabled or lost its panel role. Never hard-deletes. `--dry-run` lists what would change and
writes nothing. Output names fields, never values.
"""

import logging
import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from accounts import keycloak
from accounts.claims import Identity, is_valid_name
from accounts.mobile import InvalidMobileError, normalize_mobile
from accounts.models import ConsultantType, Profile, Role
from accounts.profiles import apply_identity, differences

logger = logging.getLogger("gradian.accounts")


def _identity(user: keycloak.KeycloakUser) -> Identity | None:
    """The identity for a Keycloak user, or None if it is not usable (reported, not synced)."""
    if len(user.roles) != 1:
        return None
    try:
        mobile = normalize_mobile(user.username)
        sub = uuid.UUID(user.sub)
    except (InvalidMobileError, ValueError):
        return None
    role = user.roles[0]
    if (
        "@" not in user.email
        or not is_valid_name(user.first_name)
        or not is_valid_name(user.last_name)
    ):
        return None
    if role == Role.CONSULTANT and user.consultant_type not in ConsultantType.values:
        return None
    return Identity(
        sub=sub,
        mobile=mobile,
        email=user.email.lower(),
        first_name=user.first_name,
        last_name=user.last_name,
        role=role,
        consultant_type=user.consultant_type if role == Role.CONSULTANT else "",
    )


class Command(BaseCommand):
    help = "Reconcile Profile rows with Keycloak users (create, update, deactivate)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run", action="store_true", help="List mismatches and write nothing."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        try:
            users = keycloak.get_admin_client().list_panel_users()
        except keycloak.KeycloakError as exc:
            raise CommandError(f"Keycloak Admin API failed: {exc}") from exc

        profiles = {profile.sub: profile for profile in Profile.objects.all()}
        listed = {user.sub for user in users}  # unusable users stay untouched, not deactivated
        counts = {"created": 0, "updated": 0, "deactivated": 0, "reactivated": 0, "skipped": 0}

        with transaction.atomic():
            for user in users:
                identity = _identity(user)
                if identity is None:
                    counts["skipped"] += 1
                    self.stdout.write(f"skip {user.sub}: unusable identity or role")
                    continue
                profile = profiles.get(identity.sub)
                if profile is None:
                    counts["created"] += 1
                    self.stdout.write(f"create {identity.sub}")
                    if not dry_run:
                        Profile.objects.create(
                            **{f: getattr(identity, f) for f in ("sub", *Profile.IDENTITY_FIELDS)},
                            is_active=user.enabled,
                        )
                    continue
                changed = differences(profile, identity)
                if changed:
                    counts["updated"] += 1
                    self.stdout.write(f"update {identity.sub}: {', '.join(changed)}")
                if profile.is_active != user.enabled:
                    counts["reactivated" if user.enabled else "deactivated"] += 1
                    self.stdout.write(
                        f"{'reactivate' if user.enabled else 'deactivate'} {identity.sub}"
                    )
                if not dry_run and (changed or profile.is_active != user.enabled):
                    apply_identity(profile, identity, changed)
                    profile.is_active = user.enabled
                    profile.identity_synced_at = timezone.now()
                    profile.save()

            for sub, profile in profiles.items():
                if str(sub) not in listed and profile.is_active:
                    counts["deactivated"] += 1
                    self.stdout.write(f"deactivate {sub}: no longer in Keycloak")
                    if not dry_run:
                        profile.is_active = False
                        profile.save(update_fields=["is_active", "updated_at"])

        logger.info(
            "keycloak sync finished", extra={"event": "sync", "dry_run": dry_run, "counts": counts}
        )
        prefix = "dry run, nothing written: " if dry_run else ""
        self.stdout.write(prefix + ", ".join(f"{n} {k}" for k, n in counts.items()))
