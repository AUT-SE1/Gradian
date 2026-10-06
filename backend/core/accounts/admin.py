from django.contrib import admin
from django.http import HttpRequest

from accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin[Profile]):
    """Identity fields are owned by Keycloak, so they are read-only here (DES-ID-01).
    Profiles appear on first sign-in or through `sync_keycloak_users`, never by hand, and are
    deactivated rather than deleted."""

    list_display = ("mobile", "full_name", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("mobile", "email", "first_name", "last_name")
    readonly_fields = ("sub", *Profile.IDENTITY_FIELDS, "created_at", "updated_at")
    fields = (
        "sub",
        *Profile.IDENTITY_FIELDS,
        "is_active",
        "field_of_study",
        "avatar_url",
        "bio",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Profile | None = None) -> bool:
        return False
