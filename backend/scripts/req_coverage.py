#!/usr/bin/env python3
"""List requirements that no test claims (SYS-NFR-08).

Requirement ids come from docs/backend/01-requirements.md (table rows starting `| SYS-...`).
Claims come from `@covers("SYS-...")` in the test code. Prints a summary and the gaps.
Exit status is 0 unless --strict is given and a gap exists, so it can be used as a progress
report while the system is still being built, and as a gate once it is complete.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENT_ROW = re.compile(r"^\|\s*(SYS-[A-Z]+-\d{2})\s*\|", re.MULTILINE)
COVERS_CALL = re.compile(r"@covers\(([^)]*)\)", re.DOTALL)
ID = re.compile(r"SYS-[A-Z]+-\d{2}")
TEST_DIRS = ("core", "scripts", "tests")


def required_ids(document: Path) -> list[str]:
    return REQUIREMENT_ROW.findall(document.read_text(encoding="utf-8"))


def covered_ids(root: Path) -> set[str]:
    found: set[str] = set()
    for directory in TEST_DIRS:
        for path in (root / directory).rglob("test*.py"):
            for call in COVERS_CALL.findall(path.read_text(encoding="utf-8")):
                found |= set(ID.findall(call))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 if any requirement has no test"
    )
    args = parser.parse_args()

    required = required_ids(ROOT / "docs" / "backend" / "01-requirements.md")
    covered = covered_ids(ROOT)
    unknown = sorted(covered - set(required))
    gaps = [item for item in required if item not in covered]

    print(f"requirements with a test: {len(required) - len(gaps)} of {len(required)}")
    if unknown:
        print("tests name requirements that do not exist: " + ", ".join(unknown))
    if gaps:
        print("without a test: " + ", ".join(gaps))
    if unknown or (args.strict and gaps):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
