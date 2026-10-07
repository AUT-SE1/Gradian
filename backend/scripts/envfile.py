"""Reading the environment the way the Core Service does: the process first, then `.env`."""

import os
from collections.abc import Mapping
from pathlib import Path


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def setting(
    root: Path, name: str, default: str = "", environ: Mapping[str, str] | None = None
) -> str:
    source = os.environ if environ is None else environ
    return source.get(name) or parse_dotenv(root / ".env").get(name, default)


def is_production(root: Path, environ: Mapping[str, str] | None = None) -> bool:
    return setting(root, "ENVIRONMENT", "development", environ) == "production"
