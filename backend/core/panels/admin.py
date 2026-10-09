import json

from django.contrib import admin

from panels.models import ContentBlock, Notification


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin[ContentBlock]):
    """Edit the landing page and the widgets; the shape is checked on save."""

    list_display = ("key", "preview", "updated_at")
    ordering = ("key",)

    @admin.display(description="content")
    def preview(self, obj: ContentBlock) -> str:
        return json.dumps(obj.data, ensure_ascii=False)[:80]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin[Notification]):
    list_display = ("title", "profile", "created_at", "read_at")
    list_filter = ("read_at",)
    search_fields = ("title", "profile__mobile", "profile__last_name")
    autocomplete_fields = ()
    raw_id_fields = ("profile",)
