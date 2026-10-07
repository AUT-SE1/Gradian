#!/usr/bin/env python3
"""Fail if `.env.example` is missing a variable the settings read (SYS-OPS-05).

Scans the Django project for literal `env.require("NAME")`, `env.get("NAME", ...)`,
`env.flag(...)` and `env.csv(...)` calls, and compares the names with `.env.example`.
Also fails if `.env.example` lists a variable nothing reads, so the file cannot go stale.
Variables read only by docker-compose or Keycloak are listed in EXTERNAL.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READ = re.compile(r"""\benv\.(?:require|get|flag|csv)\(\s*["']([A-Z][A-Z0-9_]*)["']""")
ASSIGNED = re.compile(r"^#?\s*([A-Z][A-Z0-9_]*)=", re.MULTILINE)

# Read by docker-compose.yml, Keycloak or the Makefile rather than by Django.
EXTERNAL = {
    "KEYCLOAK_PORT",
    "POSTGRES_HOST_PORT",
    "KEYCLOAK_ADMIN_USER",
    "KEYCLOAK_ADMIN_PASSWORD",
    "CORE_PORT",
    "SEED_DEFAULT_PASSWORD",
}


def variables_read(source_dir: Path) -> set[str]:
    names: set[str] = set()
    for path in source_dir.rglob("*.py"):
        if "/tests/" in path.as_posix() or path.name == "settings_test.py":
            continue
        names |= set(READ.findall(path.read_text(encoding="utf-8")))
    return names


def variables_documented(example: Path) -> set[str]:
    return set(ASSIGNED.findall(example.read_text(encoding="utf-8")))


def main() -> int:
    read = variables_read(ROOT / "core")
    documented = variables_documented(ROOT / ".env.example")
    missing = sorted(read - documented)
    unused = sorted(documented - read - EXTERNAL)
    for name in missing:
        print(f"{name} is read by the settings but missing from .env.example")
    for name in unused:
        print(f"{name} is in .env.example but nothing reads it")
    if missing or unused:
        return 1
    print(f".env.example lists all {len(read)} variables the settings read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
