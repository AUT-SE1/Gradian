from typing import Any

from rest_framework import serializers

from accounts.claims import is_valid_name
from accounts.models import FieldOfStudy, Profile


class MeSerializer(serializers.ModelSerializer[Profile]):
    """Identity, display name, panel and home path. Identity fields are read-only (DES-ID-01)."""

    full_name = serializers.CharField(read_only=True)
    panel = serializers.CharField(source="role", read_only=True)
    home_path = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "sub",
            "mobile",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "consultant_type",
            "panel",
            "home_path",
            "field_of_study",
            "avatar_url",
            "bio",
        )
        read_only_fields = fields


class MeUpdateSerializer(serializers.Serializer[Profile]):
    """Fields a person may change through PATCH /me. Role and mobile number cannot be changed
    here: the role is assigned by an administrator, and the mobile number is the login."""

    email = serializers.EmailField(required=False, max_length=254)
    first_name = serializers.CharField(required=False, max_length=100)
    last_name = serializers.CharField(required=False, max_length=100)
    field_of_study = serializers.ChoiceField(required=False, choices=FieldOfStudy.choices)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)

    IDENTITY_FIELDS = ("email", "first_name", "last_name")

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def _validate_name(self, value: str) -> str:
        value = value.strip()
        if not is_valid_name(value):
            raise serializers.ValidationError("Invalid name.", code="invalid_name")
        return value

    def validate_first_name(self, value: str) -> str:
        return self._validate_name(value)

    def validate_last_name(self, value: str) -> str:
        return self._validate_name(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs:
            raise serializers.ValidationError("No changes were sent.", code="empty")
        return attrs


class AuthConfigSerializer(serializers.Serializer[dict[str, str]]):
    issuer = serializers.CharField()
    realm = serializers.CharField()
    client_id = serializers.CharField()
    end_session_url = serializers.CharField()
    landing_url = serializers.CharField()
