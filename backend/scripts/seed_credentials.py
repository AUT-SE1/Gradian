#!/usr/bin/env python3
"""Write the sign-in details of the seeded users, one CSV per group (DES-DATA-08, SYS-DATA-05).

`build/credentials/group-N.csv` lists the users of group N (role, name, mobile, password),
`group-N-service.csv` the client id and secret its service uses to call the Core Service, and
`ta.csv` the TA admin, who belongs to no group. The files hold passwords, so they are written
only to the git-ignored `build/` folder, readable by the owner alone, and the script refuses
ENVIRONMENT=production. The files are UTF-8 with a byte order mark so that Excel shows Persian.

Run through `make users`.
"""

import argparse
import sys
from pathlib import Path

from envfile import is_production
from envfile import setting as env_setting
from seed_generate import SeedError, credential_files, load_seed

ROOT = Path(__file__).resolve().parent.parent


def write_files(directory: Path, files: dict[str, str]) -> None:
    """Replace this script's own files, so a group that no longer exists leaves nothing behind."""
    directory.mkdir(parents=True, exist_ok=True)
    for stale in [directory / "ta.csv", *directory.glob("group-*.csv")]:
        stale.unlink(missing_ok=True)
    for name, text in files.items():
        path = directory / name
        path.write_text(text, encoding="utf-8-sig")
        path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "credentials")
    args = parser.parse_args()

    if is_production(ROOT):
        print("error: refusing to write credentials with ENVIRONMENT=production", file=sys.stderr)
        return 1
    password = env_setting(ROOT, "SEED_DEFAULT_PASSWORD")
    if not password:
        print("error: set SEED_DEFAULT_PASSWORD in .env", file=sys.stderr)
        return 1
    try:
        files = credential_files(load_seed(ROOT), password)
    except SeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_files(args.out, files)
    print(f"wrote {len(files)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
