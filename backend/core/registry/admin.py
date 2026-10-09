from django.contrib import admin
from django.http import HttpRequest

from registry.models import ServiceEntry


@admin.register(ServiceEntry)
class ServiceEntryAdmin(admin.ModelAdmin[ServiceEntry]):
    """Connecting a group's service is editing `target_url` and `mode` here (SYS-INT-01)."""

    list_display = (
        "key",
        "title_en",
        "panel",
        "order",
        "target_url",
        "mode",
        "enabled",
        "owner_group",
    )
    list_editable = ("target_url", "mode", "enabled")
    list_filter = ("panel", "mode", "enabled", "owner_group")
    search_fields = ("key", "title_fa", "title_en")
    ordering = ("panel", "order")

    def get_readonly_fields(
        self, request: HttpRequest, obj: ServiceEntry | None = None
    ) -> tuple[str, ...]:
        """The key is how groups and the frontend refer to an entry, so it never changes."""
        return ("key", "panel") if obj else ()
