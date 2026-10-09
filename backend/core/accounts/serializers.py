from typing import Any

from rest_framework import serializers

from accounts.models import ConsultantType, FieldOfStudy, Profile, Role
from gradian_auth.claims import is_valid_name
from gradian_auth.mobile import InvalidMobileError, normalize_mobile

ME_FIELDS: tuple[str, ...] = (
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


class MeSerializer(serializers.ModelSerializer[Profile]):
    """Identity, display name, panel and home path. Identity fields are read-only (DES-ID-01)."""

    full_name = serializers.CharField(read_only=True)
    panel = serializers.CharField(source="role", read_only=True)
    home_path = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = ME_FIELDS
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
    registration_endpoint = serializers.CharField()
    realm = serializers.CharField()
    client_id = serializers.CharField()
    end_session_url = serializers.CharField()
    landing_url = serializers.CharField()


def _clean_name(value: str) -> str:
    value = value.strip()
    if not is_valid_name(value):
        raise serializers.ValidationError("Invalid name.", code="invalid_name")
    return value


class UserSerializer(MeSerializer):
    """An account as an administrator sees it."""

    class Meta(MeSerializer.Meta):
        fields = (*ME_FIELDS, "is_active")
        read_only_fields = fields


class UserFilterSerializer(serializers.Serializer[dict[str, str]]):
    role = serializers.ChoiceField(choices=Role.choices, required=False)
    is_active = serializers.BooleanField(required=False, allow_null=True)
    q = serializers.CharField(required=False, help_text="Part of the mobile number, email or name.")


class UserCreateSerializer(serializers.Serializer[Profile]):
    mobile = serializers.CharField(help_text="09123456789; Persian digits and +98 are accepted.")
    email = serializers.EmailField(max_length=254)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(
        write_only=True, min_length=8, max_length=128, trim_whitespace=False
    )
    role = serializers.ChoiceField(choices=Role.choices)
    consultant_type = serializers.ChoiceField(
        choices=ConsultantType.choices, required=False, help_text="Required for consultants."
    )
    field_of_study = serializers.ChoiceField(choices=FieldOfStudy.choices, required=False)

    def validate_mobile(self, value: str) -> str:
        try:
            return normalize_mobile(value)
        except InvalidMobileError:
            raise serializers.ValidationError(
                "Invalid mobile number.", code="invalid_mobile"
            ) from None

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_first_name(self, value: str) -> str:
        return _clean_name(value)

    def validate_last_name(self, value: str) -> str:
        return _clean_name(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["role"] == Role.CONSULTANT and "consultant_type" not in attrs:
            raise serializers.ValidationError({"consultant_type": "Required for consultants."})
        if attrs["role"] != Role.CONSULTANT and "consultant_type" in attrs:
            raise serializers.ValidationError({"consultant_type": "Only for consultants."})
        return attrs


class UserUpdateSerializer(serializers.Serializer[Profile]):
    """The mobile number is the login and cannot be changed."""

    email = serializers.EmailField(required=False, max_length=254)
    first_name = serializers.CharField(required=False, max_length=100)
    last_name = serializers.CharField(required=False, max_length=100)
    role = serializers.ChoiceField(choices=Role.choices, required=False)
    consultant_type = serializers.ChoiceField(choices=ConsultantType.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    field_of_study = serializers.ChoiceField(choices=FieldOfStudy.choices, required=False)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_first_name(self, value: str) -> str:
        return _clean_name(value)

    def validate_last_name(self, value: str) -> str:
        return _clean_name(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs:
            raise serializers.ValidationError("No changes were sent.", code="empty")
        return attrs


class ServiceUserSerializer(serializers.ModelSerializer[Profile]):
    """A person's identity as a group service sees it."""

    full_name = serializers.CharField(read_only=True)

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
            "field_of_study",
            "is_active",
            "avatar_url",
            "bio",
        )
        read_only_fields = fields
