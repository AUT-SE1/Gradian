"""The shape of every content block (DES-DATA-04, SYS-PNL-04).

Content lives in the database as JSON, one row per block, so it can be changed in the Django
admin or by reloading a fixture without a deploy. The shapes here are checked when a block is
saved in the admin, when the seed generator writes a fixture, and in the tests, so the frontend
can rely on them.
"""

from collections.abc import Callable
from typing import Any

from rest_framework import serializers

Data = dict[str, Any]


class LinkSerializer(serializers.Serializer[Data]):
    label = serializers.CharField(max_length=60)  # type: ignore[assignment]  # shadows Field.label
    href = serializers.CharField(max_length=200)


class NavbarSerializer(serializers.Serializer[Data]):
    brand = serializers.CharField(max_length=60)
    links = LinkSerializer(many=True)
    login_label = serializers.CharField(max_length=40)
    register_label = serializers.CharField(max_length=40)


class HeroSerializer(serializers.Serializer[Data]):
    eyebrow = serializers.CharField(max_length=80, allow_blank=True)
    title = serializers.CharField(max_length=160)
    subtitle = serializers.CharField(max_length=400)
    primary_cta_label = serializers.CharField(max_length=40)
    secondary_cta_label = serializers.CharField(max_length=40)
    image_url = serializers.CharField(max_length=300, allow_blank=True)


class StatisticSerializer(serializers.Serializer[Data]):
    key = serializers.SlugField(max_length=40)
    value = serializers.CharField(max_length=30, help_text="Display text, e.g. ۱۲٬۰۰۰+.")
    label = serializers.CharField(max_length=80)  # type: ignore[assignment]  # shadows Field.label


class MissionSerializer(serializers.Serializer[Data]):
    title = serializers.CharField(max_length=80)
    description = serializers.CharField(max_length=300)
    icon = serializers.CharField(max_length=40, allow_blank=True)


class TeacherSerializer(serializers.Serializer[Data]):
    name = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=120)
    bio = serializers.CharField(max_length=300)
    avatar_url = serializers.CharField(max_length=300, allow_blank=True)


class RankerSerializer(serializers.Serializer[Data]):
    name = serializers.CharField(max_length=100)
    rank = serializers.CharField(max_length=40, help_text="Display text, e.g. رتبه ۱۲.")
    field = serializers.CharField(max_length=60)
    quote = serializers.CharField(max_length=300)
    avatar_url = serializers.CharField(max_length=300, allow_blank=True)


class TestimonialSerializer(serializers.Serializer[Data]):
    name = serializers.CharField(max_length=100)
    role = serializers.CharField(max_length=80)
    text = serializers.CharField(max_length=400)
    avatar_url = serializers.CharField(max_length=300, allow_blank=True)


class FooterSerializer(serializers.Serializer[Data]):
    description = serializers.CharField(max_length=300)
    links = LinkSerializer(many=True)
    copyright = serializers.CharField(max_length=200)


class WelcomeSerializer(serializers.Serializer[Data]):
    message = serializers.CharField(
        max_length=300, help_text="`{first_name}` and `{full_name}` are replaced per student."
    )
    tip = serializers.CharField(max_length=300, allow_blank=True)


class StreakDaySerializer(serializers.Serializer[Data]):
    day = serializers.CharField(max_length=20)
    done = serializers.BooleanField()


class StudyStreakSerializer(serializers.Serializer[Data]):
    current_days = serializers.IntegerField(min_value=0)
    best_days = serializers.IntegerField(min_value=0)
    message = serializers.CharField(max_length=200)
    week = StreakDaySerializer(many=True)


class FeedItemSerializer(serializers.Serializer[Data]):
    id = serializers.IntegerField(min_value=1)
    author = serializers.CharField(max_length=100)
    author_title = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=160)
    excerpt = serializers.CharField(max_length=400)
    likes = serializers.IntegerField(min_value=0)
    comments = serializers.IntegerField(min_value=0)


LANDING_SECTIONS: dict[str, Callable[[], serializers.BaseSerializer[Any]]] = {
    "navbar": NavbarSerializer,
    "hero": HeroSerializer,
    "statistics": lambda: StatisticSerializer(many=True),
    "missions": lambda: MissionSerializer(many=True),
    "teachers": lambda: TeacherSerializer(many=True),
    "rankers": lambda: RankerSerializer(many=True),
    "testimonials": lambda: TestimonialSerializer(many=True),
    "footer": FooterSerializer,
}

WIDGETS: dict[str, Callable[[], serializers.BaseSerializer[Any]]] = {
    "welcome": WelcomeSerializer,
    "study_streak": StudyStreakSerializer,
    "experience_feed": lambda: FeedItemSerializer(many=True),
}

SHAPES: dict[str, Callable[[], serializers.BaseSerializer[Any]]] = {
    **{f"landing.{name}": shape for name, shape in LANDING_SECTIONS.items()},
    **{f"widget.{name}": shape for name, shape in WIDGETS.items()},
}


def check_block(key: str, data: object) -> list[str]:
    """Problems with a block, as readable lines. Empty when the block is valid."""
    shape = SHAPES.get(key)
    if shape is None:
        return [f"unknown block {key!r}; known blocks: {', '.join(sorted(SHAPES))}"]
    serializer = shape()
    serializer.initial_data = data
    if serializer.is_valid():
        return []
    return [f"{field}: {problem}" for field, problem in _flatten(serializer.errors)]


def _flatten(errors: object, path: str = "") -> list[tuple[str, str]]:
    if isinstance(errors, dict):
        found: list[tuple[str, str]] = []
        for name, value in errors.items():
            found += _flatten(value, f"{path}.{name}" if path else str(name))
        return found
    if isinstance(errors, list):
        found = []
        for index, value in enumerate(errors):
            if isinstance(value, (dict, list)):
                found += _flatten(value, f"{path}[{index}]")
            else:
                found.append((path or "data", str(value)))
        return found
    return [(path or "data", str(errors))]
