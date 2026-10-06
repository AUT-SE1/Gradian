"""The one place environment variables are read.

Every setting goes through `require` or `get` with a literal name, so a missing required
variable fails at startup naming it (SYS-OPS-06) and `scripts/check_env_example.py` can verify
that `.env.example` lists every variable (SYS-OPS-05).
"""

import os
from collections.abc import MutableMapping
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

_TRUE = {"1", "true", "yes", "on"}


def load_dotenv(path: Path, environ: MutableMapping[str, str] | None = None) -> None:
    """Load `KEY=value` lines (no quotes). Variables already in the environment win."""
    target = os.environ if environ is None else environ
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        target.setdefault(key.strip(), value.strip())


def require(name: str, environ: MutableMapping[str, str] | None = None) -> str:
    """Return a required variable or fail with a message naming it."""
    source = os.environ if environ is None else environ
    value = source.get(name, "")
    if value == "":
        raise ImproperlyConfigured(
            f"Missing required environment variable {name}. "
            "Run `make env` to create .env from .env.example, then fill it in."
        )
    return value


def get(name: str, default: str, environ: MutableMapping[str, str] | None = None) -> str:
    source = os.environ if environ is None else environ
    return source.get(name, default)


def flag(name: str, default: bool, environ: MutableMapping[str, str] | None = None) -> bool:
    source = os.environ if environ is None else environ
    raw = source.get(name)
    return default if raw is None else raw.strip().lower() in _TRUE


def csv(name: str, default: str, environ: MutableMapping[str, str] | None = None) -> list[str]:
    source = os.environ if environ is None else environ
    return [item.strip() for item in source.get(name, default).split(",") if item.strip()]
