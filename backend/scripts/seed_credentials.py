#!/usr/bin/env python3
"""Write the sign-in details of the seeded users (DES-DATA-08, SYS-DATA-05).

`build/credentials/users.csv` lists every seeded user (role, name, mobile, password); the users
are one pool shared by all groups. `services.csv` lists the client id and secret each group's
service uses to call the Core Service. The files hold passwords, so they are written only to the
git-ignored `build/` folder, readable by the owner alone, and the script refuses
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
    """Replace this script's own files, and the per-group files an earlier version wrote."""
    directory.mkdir(parents=True, exist_ok=True)
    for stale in [
        *directory.glob("group-*.csv"),
        directory / "ta.csv",
        *map(directory.joinpath, files),
    ]:
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
