from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from accounts.models import Role

KEY_PATTERN = r"^(student|consultant|professor|admin)\.[a-z0-9]+(-[a-z0-9]+)*$"


class Mode(models.TextChoices):
    REDIRECT = "redirect"
    EMBED = "embed"


class ServiceEntry(models.Model):
    """One service in one panel's menu (DES-REG-01).

    A service offered in several panels is several independent rows (DES-REG-03). The projects
    are not tables (DEC-14), so the owner is only the group's number.
    """

    key = models.CharField(
        max_length=64,
        primary_key=True,
        validators=[RegexValidator(KEY_PATTERN, "Use <panel>.<name-with-dashes>.")],
        help_text="Stable identifier, <panel>.<name>. Never change it once groups use it.",
    )
    panel = models.CharField(max_length=20, choices=Role.choices)
    title_fa = models.CharField("title (Persian)", max_length=120)
    title_en = models.CharField("title (English)", max_length=120)
    description = models.CharField(max_length=300, blank=True)
    button_label = models.CharField(max_length=60, default="ورود به سرویس")
    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(help_text="Position in the panel, smallest first.")
    target_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Where the service lives. Empty means it is not connected yet.",
    )
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.REDIRECT)
    enabled = models.BooleanField(default=True)
    owner_group = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)], help_text="Group number."
    )

    class Meta:
        ordering = ("panel", "order", "key")
        verbose_name_plural = "service entries"
        indexes = (models.Index(fields=["panel", "order"]),)

    def __str__(self) -> str:
        return f"{self.key}: {self.title_en}"

    @property
    def available(self) -> bool:
        return self.enabled and bool(self.target_url)

    def clean(self) -> None:
        super().clean()
        if self.key and self.panel and not self.key.startswith(f"{self.panel}."):
            message = f"The key of a {self.panel} entry starts with {self.panel}."
            raise ValidationError({"key": message})
        if self.target_url and not self.target_url.startswith(("http://", "https://")):
            raise ValidationError({"target_url": "Use an http or https address."})
