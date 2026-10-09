from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import Profile
from panels.content import SHAPES, check_block


class ContentBlock(models.Model):
    """One piece of display-only content: a landing section or a widget (SYS-PNL-04).

    `data` is checked against the shape in `panels.content` whenever a block is saved through
    a form, so a mistake in the admin cannot break the frontend.
    """

    key = models.CharField(
        max_length=64,
        primary_key=True,
        choices=[(key, key) for key in sorted(SHAPES)],
    )
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("key",)

    def __str__(self) -> str:
        return self.key

    def clean(self) -> None:
        super().clean()
        problems = check_block(self.key, self.data)
        if problems:
            raise ValidationError({"data": problems})


class Notification(models.Model):
    """A message for the bell. Empty by default; the bell is display-only (DES-API-05)."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = (models.Index(fields=["profile", "-created_at"]),)

    def __str__(self) -> str:
        return f"{self.title} ({self.profile_id})"
