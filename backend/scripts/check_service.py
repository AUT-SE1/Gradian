#!/usr/bin/env python3
"""Check that a group service follows the platform's integration rules (DES-REG-06, DES-REG-05).

    make check-service URL=http://team1:8001 \\
        ARGS="--group 1 --restricted-path /staff --allowed-roles professor,admin"

The URL is the one the tools container can reach, so a service in Compose is `http://teamN:800N`.
Tokens are real: a seeded user signs in through the test-only client, and the audience check uses
the service token of another group. The checks:

- the health endpoint answers 200 without a token;
- a protected endpoint answers 401 without a token, and 401 for a token that is not valid;
- it accepts a valid token of a signed-in person (2xx);
- with `--group N`: it refuses a token that was not meant for it, the service token of another
  group, with 401 (the audience check);
- with `--restricted-path`: it answers 403 to a person whose role is not allowed there, and
  accepts a person whose role is;
- with `--page-path` (and `--group N`), for a service whose pages people reach by redirect: a
  visitor who is not signed in is sent on to Keycloak's sign-in for the service's own client
  `group-N`, from where a person who is already signed in at the panel returns at once.

A check that cannot run is reported as skipped, never as passed. Exit status 0 means no check
failed, 1 means one did, 2 means the checks could not be set up.
"""

import argparse
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from envfile import setting as env_setting

ROOT = Path(__file__).resolve().parent.parent
ROLES = ("student", "consultant", "professor", "admin")
TIMEOUT_SECONDS = 10
GARBAGE_TOKEN = "not.a.token"  # noqa: S105  # a deliberately invalid value


class SetupError(Exception):
    """The checks cannot be run, for example because Keycloak is unreachable."""


class TokenSource(Protocol):
    def person(self, role: str) -> str: ...

    def other_group_service(self, group: int) -> str: ...


@dataclass(frozen=True)
class Result:
    name: str
    status: str
    detail: str = ""

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def http_get(url: str, token: str | None = None) -> int:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SetupError(f"cannot reach {url}: {exc}") from exc


def http_redirect(url: str) -> tuple[int, str | None]:
    """The status and `Location` of one request, without following the redirect."""
    try:
        reply = requests.get(url, allow_redirects=False, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise SetupError(f"cannot reach {url}: {exc}") from exc
    return reply.status_code, reply.headers.get("Location")


Redirector = Callable[[str], tuple[int, str | None]]


def reaches_sign_in(start: str, auth_endpoint: str, client_id: str, redirect: Redirector) -> Result:
    name = f"a visitor who is not signed in is sent to Keycloak as {client_id}"
    url = start
    for _ in range(4):
        status, location = redirect(url)
        if status // 100 != 3 or not location:
            return Result(name, "FAIL", f"{url} answered {status}, not a redirect")
        url = urljoin(url, location)
        if url.startswith(auth_endpoint):
            asked_for = parse_qs(urlsplit(url).query).get("client_id", [])
            if asked_for == [client_id]:
                return Result(name, "PASS")
            return Result(name, "FAIL", f"it asked Keycloak for {asked_for}, not {client_id}")
    return Result(name, "FAIL", "it never reached Keycloak's sign-in")


def _expect(name: str, got: int, wanted: str) -> Result:
    ok = got // 100 == 2 if wanted == "2xx" else str(got) == wanted
    return Result(name, "PASS" if ok else "FAIL", "" if ok else f"expected {wanted}, got {got}")


def run_checks(
    base: str,
    tokens: TokenSource,
    *,
    path: str = "/",
    health: str = "/health",
    group: int | None = None,
    restricted_path: str | None = None,
    allowed_roles: tuple[str, ...] = (),
    page_path: str | None = None,
    auth_endpoint: str = "",
    fetch: Callable[..., int] = http_get,
    redirect: Redirector = http_redirect,
) -> list[Result]:
    base = base.rstrip("/")
    protected = base + path
    results = [
        _expect(f"health: GET {health} needs no token", fetch(base + health), "200"),
        _expect(f"GET {path} without a token is refused", fetch(protected), "401"),
        _expect(
            f"GET {path} with an invalid token is refused", fetch(protected, GARBAGE_TOKEN), "401"
        ),
    ]
    person = tokens.person(allowed_roles[0] if allowed_roles else "student")
    results.append(
        _expect(f"GET {path} accepts a signed-in person", fetch(protected, person), "2xx")
    )

    if group is None:
        results.append(Result("a token for another service is refused", "SKIP", "give --group N"))
    else:
        foreign = tokens.other_group_service(group)
        results.append(
            _expect(
                "a token meant for another service is refused (audience)",
                fetch(protected, foreign),
                "401",
            )
        )

    if restricted_path is None or not allowed_roles:
        results.append(
            Result(
                "a person of the wrong role is refused",
                "SKIP",
                "give --restricted-path and --allowed-roles",
            )
        )
    else:
        restricted = base + restricted_path
        wrong = next(role for role in ROLES if role not in allowed_roles)
        results.append(
            _expect(
                f"GET {restricted_path} refuses a {wrong} with 403",
                fetch(restricted, tokens.person(wrong)),
                "403",
            )
        )
        right = allowed_roles[0]
        results.append(
            _expect(
                f"GET {restricted_path} accepts a {right}",
                fetch(restricted, tokens.person(right)),
                "2xx",
            )
        )
    if page_path is None or group is None:
        results.append(
            Result(
                "a visitor who is not signed in is sent to Keycloak",
                "SKIP",
                "give --page-path and --group",
            )
        )
    else:
        results.append(reaches_sign_in(base + page_path, auth_endpoint, f"group-{group}", redirect))
    return results


class KeycloakTokens:
    """Real tokens: a seeded user per role (test-only client), and another group's service."""

    def __init__(self, keycloak_url: str, realm: str, password: str, secrets: dict[int, str]):
        self._url = f"{keycloak_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
        self._password = password
        self._secrets = secrets
        self._mobiles = self._seeded_mobiles()

    @staticmethod
    def _seeded_mobiles() -> dict[str, str]:
        import seed_generate

        seed = seed_generate.load_seed(ROOT)
        found: dict[str, str] = {}
        for person in sorted(seed.people, key=lambda p: p.mobile):
            found.setdefault(person.role, person.mobile)
        return found

    def _post(self, data: dict[str, str]) -> str:
        try:
            response = requests.post(self._url, data=data, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise SetupError(f"cannot reach Keycloak at {self._url}: {exc}") from exc
        if response.status_code != 200:
            raise SetupError(f"Keycloak refused the token request ({response.status_code})")
        return str(response.json()["access_token"])

    def person(self, role: str) -> str:
        return self._post(
            {
                "grant_type": "password",
                "client_id": "gradian-test",
                "username": self._mobiles[role],
                "password": self._password,
            }
        )

    def other_group_service(self, group: int) -> str:
        other = next(number for number in sorted(self._secrets) if number != group)
        return self._post(
            {
                "grant_type": "client_credentials",
                "client_id": f"group-{other}",
                "client_secret": self._secrets[other],
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--url", required=True, help="base URL of the service")
    parser.add_argument("--path", default="/", help="an endpoint any signed-in person may call")
    parser.add_argument("--health", default="/health")
    parser.add_argument("--group", type=int, help="the group number, for the audience check")
    parser.add_argument("--page-path", help="a page of the service that needs a signed-in person")
    parser.add_argument("--restricted-path", help="an endpoint only some roles may call")
    parser.add_argument("--allowed-roles", default="", help="comma-separated roles for it")
    args = parser.parse_args()

    from seed_generate import client_secret, load_seed

    password = env_setting(ROOT, "SEED_DEFAULT_PASSWORD")
    if not password:
        print("error: SEED_DEFAULT_PASSWORD is not set (see .env)", file=sys.stderr)
        return 2
    allowed = tuple(role for role in args.allowed_roles.split(",") if role)
    unknown = [role for role in allowed if role not in ROLES]
    if unknown:
        print(f"error: unknown role(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    public = env_setting(ROOT, "KEYCLOAK_PUBLIC_URL", "http://localhost:8080").rstrip("/")
    realm = env_setting(ROOT, "KEYCLOAK_REALM", "gradian")
    auth_endpoint = f"{public}/realms/{realm}/protocol/openid-connect/auth"
    seed = load_seed(ROOT)
    secrets = {group.number: client_secret(password, group.client_id) for group in seed.groups}
    tokens = KeycloakTokens(
        env_setting(ROOT, "KEYCLOAK_URL", "http://keycloak:8080"),
        env_setting(ROOT, "KEYCLOAK_REALM", "gradian"),
        password,
        secrets,
    )
    try:
        results = run_checks(
            args.url,
            tokens,
            path=args.path,
            health=args.health,
            group=args.group,
            restricted_path=args.restricted_path,
            allowed_roles=allowed,
            page_path=args.page_path,
            auth_endpoint=auth_endpoint,
        )
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for result in results:
        detail = f"  ({result.detail})" if result.detail else ""
        print(f"{result.status:4} {result.name}{detail}")
    failed = [result for result in results if result.failed]
    print(f"\n{len(failed)} failed" if failed else "\nthe service follows the integration rules")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
