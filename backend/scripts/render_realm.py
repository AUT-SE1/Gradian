#!/usr/bin/env python3
"""Render the Keycloak realm file that docker-compose imports (DES-IDP-01, DES-IDP-09).

Takes `keycloak/realm-template.json`, embeds the user-profile definition
(`keycloak/user-profile.json`) and, for non-production environments only, adds the test client
`gradian-test` that allows direct password grants so tests can get tokens without a browser.
The `${VAR}` placeholders in the template are filled in by Keycloak itself at import time,
from the container's environment, so no secret is written to the output file.

Run through `make seed-render`, which refuses ENVIRONMENT=production first. Seeded users are
added to this file by the seed generator in a later step.
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from envfile import is_production

ROOT = Path(__file__).resolve().parent.parent
USER_PROFILE_PROVIDER = "org.keycloak.userprofile.UserProfileProvider"


def render(
    template: dict[str, Any], user_profile: dict[str, Any], *, production: bool
) -> dict[str, Any]:
    realm = copy.deepcopy(template)
    realm.setdefault("components", {})[USER_PROFILE_PROVIDER] = [
        {
            "providerId": "declarative-user-profile",
            "subComponents": {},
            "config": {"kc.user.profile.config": [json.dumps(user_profile, ensure_ascii=False)]},
        }
    ]
    if not production:
        web = next(c for c in realm["clients"] if c["clientId"] == "gradian-web")
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

    realm = render(
        json.loads(args.template.read_text(encoding="utf-8")),
        json.loads(args.user_profile.read_text(encoding="utf-8")),
        production=False,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(realm, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
