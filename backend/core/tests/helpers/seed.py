"""The demo content of `seed/`, built in memory so fast tests need no generated fixture."""

from django.core import serializers

from tests.helpers.repo import REPO_ROOT, scripts_on_path

scripts_on_path()

import seed_generate  # noqa: E402

__all__ = ["content", "load_blocks", "load_services", "seed_generate"]


def content() -> seed_generate.Content:
    return seed_generate.load_content(REPO_ROOT)


def _save(text: str) -> None:
    for entry in serializers.deserialize("json", text):
        entry.save()


def load_services() -> None:
    _save(seed_generate.dumps(seed_generate.service_fixture(content())))


def load_blocks() -> None:
    loaded = content()
    stamp = "2026-01-01T00:00:00Z"
    _save(seed_generate.dumps(seed_generate.block_fixture("landing", loaded.landing, stamp)))
    _save(seed_generate.dumps(seed_generate.block_fixture("widget", loaded.widgets, stamp)))
