from typing import Any

from rest_framework import serializers

from panels import content
from panels.models import Notification

Data = dict[str, Any]


class LandingSerializer(serializers.Serializer[Data]):
    """Documents the landing response. A section whose block was deleted is null."""

    navbar = content.NavbarSerializer(allow_null=True)
    hero = content.HeroSerializer(allow_null=True)
    statistics = content.StatisticSerializer(many=True, allow_null=True)
    missions = content.MissionSerializer(many=True, allow_null=True)
    teachers = content.TeacherSerializer(many=True, allow_null=True)
    rankers = content.RankerSerializer(many=True, allow_null=True)
    testimonials = content.TestimonialSerializer(many=True, allow_null=True)
    footer = content.FooterSerializer(allow_null=True)


class CountdownSerializer(serializers.Serializer[Data]):
    date = serializers.DateField(help_text="The Konkur day.")
    state = serializers.ChoiceField(choices=["upcoming", "today", "past"])
    days_remaining = serializers.IntegerField(help_text="0 on the day and after it.")
    label = serializers.CharField(  # type: ignore[assignment]  # shadows Field.label
        help_text="Persian text for the countdown widget."
    )


class PanelHeaderSerializer(serializers.Serializer[Data]):
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True)
    consultant_type = serializers.CharField(
        allow_null=True, help_text="`consultant` or `top_ranker` for a consultant, otherwise null."
    )
    field_of_study = serializers.CharField(
        allow_null=True,
        help_text="Students only: the value, empty until set. Null in every other panel.",
    )
    field_of_study_label = serializers.CharField(
        allow_null=True, help_text="Persian text for the field of study, null when there is none."
    )


class PanelSerializer(serializers.Serializer[Data]):
    panel = serializers.CharField()
    home_path = serializers.CharField()
    header = PanelHeaderSerializer()
    countdown = CountdownSerializer()


class DashboardSerializer(serializers.Serializer[Data]):
    welcome = content.WelcomeSerializer(allow_null=True)
    countdown = CountdownSerializer()
    study_streak = content.StudyStreakSerializer(allow_null=True)
    experience_feed = content.FeedItemSerializer(many=True, allow_null=True)


class NotificationSerializer(serializers.ModelSerializer[Notification]):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("id", "title", "body", "created_at", "is_read")
        read_only_fields = fields

    def get_is_read(self, obj: Notification) -> bool:
        return obj.read_at is not None
