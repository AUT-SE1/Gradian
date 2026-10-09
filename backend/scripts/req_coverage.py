#!/usr/bin/env python3
"""List requirements that have neither a test nor an external-implementation mark (SYS-NFR-08).

Requirement ids come from docs/backend/01-requirements.md (table rows starting `| SYS-...`).
Claims come from `@covers("SYS-...")` in the test code. A requirement whose row in the test
plan lists the level `EXT` relies on an external implementation (DEC-17) and counts as covered.
Prints a summary and the gaps. Exit status is 0 unless --strict is given and a gap exists, so it
can be used as a progress report while the system is still being built, and as a gate once it
is complete.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENT_ROW = re.compile(r"^\|\s*(SYS-[A-Z]+-\d{2})\s*\|", re.MULTILINE)
TABLE_ROW = re.compile(r"^\|\s*(SYS-[A-Z]+-\d{2})\s*\|([^|]*)\|", re.MULTILINE)
COVERS_CALL = re.compile(r"@covers\(([^)]*)\)", re.DOTALL)
ID = re.compile(r"SYS-[A-Z]+-\d{2}")
TEST_DIRS = ("core", "scripts", "tests")


def required_ids(document: Path) -> list[str]:
    return REQUIREMENT_ROW.findall(document.read_text(encoding="utf-8"))


def external_ids(test_plan: Path) -> set[str]:
    """Requirements whose level column in the test plan contains EXT."""
    found: set[str] = set()
    for row in TABLE_ROW.finditer(test_plan.read_text(encoding="utf-8")):
        requirement, levels = row.group(1), row.group(2)
        if re.search(r"\bEXT\b", levels):
            found.add(requirement)
    return found


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

    docs = ROOT / "docs"
    required = required_ids(docs / "01-requirements.md")
    covered = covered_ids(ROOT)
    external = external_ids(docs / "04-test-plan.md")
    unknown = sorted((covered | external) - set(required))
    external_only = [item for item in required if item in external and item not in covered]
    gaps = [item for item in required if item not in covered and item not in external]

    print(
        f"requirements with a test: {len([r for r in required if r in covered])} of {len(required)}"
    )
    if external_only:
        print("relied on externally, no test: " + ", ".join(external_only))
    if unknown:
        print("tests or the test plan name requirements that do not exist: " + ", ".join(unknown))
    if gaps:
        print("neither a test nor an EXT mark: " + ", ".join(gaps))
    if unknown or (args.strict and gaps):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
