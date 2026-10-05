from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from accounts.mobile import MOBILE_PATTERN
from accounts.roles import HOME_PATHS


class Role(models.TextChoices):
    STUDENT = "student"
    CONSULTANT = "consultant"
    PROFESSOR = "professor"
    ADMIN = "admin"


class ConsultantType(models.TextChoices):
    CONSULTANT = "consultant"
    TOP_RANKER = "top_ranker"


class FieldOfStudy(models.TextChoices):
    EXPERIMENTAL = "experimental"
    MATHEMATICS = "mathematics"
    HUMANITIES = "humanities"


class Profile(models.Model):
    """Read cache of a Keycloak user plus the attributes only Core owns (DES-ID-01).

    Identity fields (mobile, email, names, role, consultant type) are owned by Keycloak and
    are refreshed from token claims; nothing edits them here except the sync paths.
    """

    IDENTITY_FIELDS = ("mobile", "email", "first_name", "last_name", "role", "consultant_type")

    sub = models.UUIDField(primary_key=True, editable=False)
    mobile = models.CharField(
        max_length=11, unique=True, validators=[RegexValidator(MOBILE_PATTERN)]
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices)
    consultant_type = models.CharField(max_length=20, choices=ConsultantType.choices, blank=True)
    is_active = models.BooleanField(default=True)
    # When the identity fields were last written (token refresh, write-through, sync). A token
    # issued before this moment cannot hold newer identity data than the cache does.
    identity_synced_at = models.DateTimeField(default=timezone.now)

    field_of_study = models.CharField(max_length=20, choices=FieldOfStudy.choices, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self) -> str:
        return f"{self.full_name} ({self.mobile})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def home_path(self) -> str:
        return HOME_PATHS[self.role]
