"""Reaching the repository's scripts, seed content and reference services from tests.

The Core code lives at /app in the `core` container and at /repo/core in the `tools` container,
while the repository itself is mounted read-only at /repo in both. So the repository is found,
in order, from `REPO_ROOT`, from the folder above `core/` when the tests run inside it, and at
/repo.
"""

import os
import sys
from pathlib import Path


def find_repo_root() -> Path:
    explicit = os.environ.get("REPO_ROOT")
    if explicit:
        return Path(explicit)
    above_core = Path(__file__).resolve().parents[3]
    if (above_core / "scripts").is_dir():
        return above_core
    return Path("/repo")


REPO_ROOT = find_repo_root()


def scripts_on_path() -> None:
    folder = str(REPO_ROOT / "scripts")
    if folder not in sys.path:
        sys.path.insert(0, folder)


def group_service_secret(group: int, password: str) -> str:
    """The Keycloak secret of `group-N`: derived from the seed password, as the realm file does."""
    scripts_on_path()
    import seed_generate

    return str(seed_generate.client_secret(password, f"group-{group}"))
