from typing import Any

from rest_framework import serializers

from registry.models import Mode, ServiceEntry


class ServiceEntrySerializer(serializers.ModelSerializer[ServiceEntry]):
    status = serializers.SerializerMethodField(
        help_text="`available`, or `unavailable` when the entry is disabled or has no target URL."
    )
    url = serializers.SerializerMethodField(
        help_text="Where to open the service. Null while it is unavailable."
    )
    mode = serializers.ChoiceField(
        choices=Mode.choices,
        help_text=(
            "`redirect`: go to the service, which signs the person in itself (single sign-on). "
            "`embed`: load it in the content area."
        ),
    )

    class Meta:
        model = ServiceEntry
        fields = (
            "key",
            "title_fa",
            "title_en",
            "description",
            "button_label",
            "icon",
            "order",
            "status",
            "mode",
            "url",
        )
        read_only_fields = fields

    def get_status(self, obj: ServiceEntry) -> str:
        return "available" if obj.available else "unavailable"

    def get_url(self, obj: ServiceEntry) -> Any:
        return obj.target_url if obj.available else None
