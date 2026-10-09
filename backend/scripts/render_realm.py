#!/usr/bin/env python3
"""Render the Keycloak realm file that docker-compose imports (DES-IDP-01, DES-DATA-05).

Takes `keycloak/realm-template.json`, embeds the user-profile definition
(`keycloak/user-profile.json`), adds the seeded users with the password `SEED_DEFAULT_PASSWORD`,
the service client of every group, and, for non-production environments only, the test client
`gradian-test` that allows direct password grants so tests can get tokens without a browser.
The `${VAR}` placeholders in the template are filled in by Keycloak itself at import time,
from the container's environment.

The output holds passwords and client secrets. It goes to the git-ignored `build/` folder, and
this script refuses ENVIRONMENT=production. Run through `make realm`.
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from envfile import is_production
from envfile import setting as env_setting
from seed_generate import (
    Seed,
    SeedError,
    load_seed,
    realm_users,
    service_clients,
    web_audience_mappers,
)

ROOT = Path(__file__).resolve().parent.parent
USER_PROFILE_PROVIDER = "org.keycloak.userprofile.UserProfileProvider"


def render(
    template: dict[str, Any],
    user_profile: dict[str, Any],
    *,
    production: bool,
    seed: Seed | None = None,
    password: str = "",
) -> dict[str, Any]:
    realm = copy.deepcopy(template)
    realm.setdefault("components", {})[USER_PROFILE_PROVIDER] = [
        {
            "providerId": "declarative-user-profile",
            "subComponents": {},
            "config": {"kc.user.profile.config": [json.dumps(user_profile, ensure_ascii=False)]},
        }
    ]
    web = next(c for c in realm["clients"] if c["clientId"] == "gradian-web")
    if seed is not None:
        if not password:
            raise ValueError("a password is needed to render the seeded users")
        realm.setdefault("users", []).extend(realm_users(seed, password))
        realm["clients"].extend(service_clients(seed, password))
        web["protocolMappers"].extend(web_audience_mappers(seed))
    if not production:
        test_client = copy.deepcopy(web)
        test_client.update(
            clientId="gradian-test",
            name="Gradian tests (never in production)",
            directAccessGrantsEnabled=True,
            standardFlowEnabled=False,
        )
        test_client.pop("redirectUris", None)
        test_client["webOrigins"] = ["${CORE_ORIGIN}"]
        realm["clients"].append(test_client)
    return realm


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=ROOT / "keycloak" / "realm-template.json")
    parser.add_argument(
        "--user-profile", type=Path, default=ROOT / "keycloak" / "user-profile.json"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "realm-gradian.json")
    args = parser.parse_args()

    if is_production(ROOT):
        print("error: refusing to render a realm file with ENVIRONMENT=production", file=sys.stderr)
        return 1

    password = env_setting(ROOT, "SEED_DEFAULT_PASSWORD")
    if not password:
        print("error: set SEED_DEFAULT_PASSWORD in .env", file=sys.stderr)
        return 1
    try:
        seed = load_seed(ROOT)
    except SeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    realm = render(
        json.loads(args.template.read_text(encoding="utf-8")),
        json.loads(args.user_profile.read_text(encoding="utf-8")),
        production=False,
        seed=seed,
        password=password,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(realm, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
