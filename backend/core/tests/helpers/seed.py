"""The demo content of `seed/`, built in memory so fast tests need no generated fixture."""

import sys
from pathlib import Path

from django.core import serializers

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import seed_generate  # noqa: E402

__all__ = ["content", "load_blocks", "load_services", "seed_generate"]


def content() -> seed_generate.Content:
    return seed_generate.load_content(ROOT)


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
