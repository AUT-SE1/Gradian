"""Reaching the repository's scripts and reference services from integration tests.

Inside the `core` container the repository is mounted read-only at /repo; in the `tools`
container it is /repo too. `REPO_ROOT` overrides it, for running elsewhere.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("REPO_ROOT", "/repo"))


def scripts_on_path() -> None:
    folder = str(REPO_ROOT / "scripts")
    if folder not in sys.path:
        sys.path.insert(0, folder)


def group_service_secret(group: int, password: str) -> str:
    """The Keycloak secret of `group-N`: derived from the seed password, as the realm file does."""
    scripts_on_path()
    import seed_generate

    return str(seed_generate.client_secret(password, f"group-{group}"))
