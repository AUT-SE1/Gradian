#!/usr/bin/env python3
"""Build a wheel of every package in `packages/` into `build/wheels/`.

A service in another repository installs them together, offline:

    pip install --no-index --find-links wheels gradian-auth

Run through `make packages`.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def package_dirs(packages: Path) -> list[Path]:
    return sorted(path.parent for path in packages.glob("*/pyproject.toml"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "wheels")
    args = parser.parse_args()

    directories = package_dirs(ROOT / "packages")
    if not directories:
        print("error: no packages found in packages/", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.whl"):
        old.unlink()
    for directory in directories:
        command = [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "-w",
            str(args.out),
            str(directory),
        ]
        if subprocess.run(command, check=False).returncode != 0:  # fixed arguments
            print(f"error: could not build {directory.name}", file=sys.stderr)
            return 1
    print(f"wrote {len(directories)} wheels to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
