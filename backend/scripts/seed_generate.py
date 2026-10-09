#!/usr/bin/env python3
"""Generate the seed data from `seed/` (DES-DATA-01 to DES-DATA-03).

The same input always gives byte-identical output. A user's id is `uuid5(namespace, mobile)`, so
the Django fixture and the Keycloak realm file agree without a lookup and `loaddata` can be
repeated. The fixture, `core/accounts/fixtures/profiles.json`, is a build artifact: it is
git-ignored and written again by `make seed`. Project groups are not modelled in the system; they
only decide which seeded users and which service client a team is given. This module is also the
library that `render_realm.py` and `seed_credentials.py` use.
"""

import argparse
import base64
import csv
import hashlib
import hmac
import io
import json
import sys
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "core"))

from accounts.mobile import InvalidMobileError, normalize_mobile  # noqa: E402

KINDS = ("student", "consultant", "top_ranker", "professor", "admin")
ROLE_OF_KIND = {
    "student": "student",
    "consultant": "consultant",
    "top_ranker": "consultant",
    "professor": "professor",
    "admin": "admin",
}
CONSULTANT_TYPE_OF_KIND = {"consultant": "consultant", "top_ranker": "top_ranker"}
MOBILE_LENGTH = 11
NO_GROUP = 0

PROFILES_FIXTURE = "core/accounts/fixtures/profiles.json"


class SeedError(ValueError):
    """The seed sources cannot produce a valid seed."""


@dataclass(frozen=True)
class Group:
    number: int
    slug: str
    name: str

    @property
    def client_id(self) -> str:
        return self.slug


@dataclass(frozen=True)
class Person:
    sub: uuid.UUID
    mobile: str
    email: str
    first_name: str
    last_name: str
    kind: str
    field_of_study: str
    group: int

    @property
    def role(self) -> str:
        return ROLE_OF_KIND[self.kind]

    @property
    def consultant_type(self) -> str:
        return CONSULTANT_TYPE_OF_KIND.get(self.kind, "")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True)
class Seed:
    groups: tuple[Group, ...]
    people: tuple[Person, ...]
    timestamp: str

    def members(self, group: Group) -> tuple[Person, ...]:
        return tuple(person for person in self.people if person.group == group.number)

    @property
    def ungrouped(self) -> tuple[Person, ...]:
        return tuple(person for person in self.people if person.group == NO_GROUP)


def _get[T](source: Mapping[str, Any], key: str, kind: type[T], where: str) -> T:
    value = source.get(key)
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        raise SeedError(f"{where}{key} must be a {kind.__name__}")
    return value


def _section(source: Mapping[str, Any], key: str, where: str) -> Mapping[str, Any]:
    value = source.get(key)
    if not isinstance(value, Mapping):
        raise SeedError(f"{where}{key} must be a mapping")
    return value


def _strings(source: Mapping[str, Any], key: str, where: str) -> list[str]:
    value = source.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
        raise SeedError(f"{where}{key} must be a non-empty list of strings")
    return list(value)


def _digest(*parts: str) -> int:
    return int.from_bytes(hashlib.sha256(":".join(parts).encode()).digest()[:8], "big")


def _pick_name(
    mobile: str,
    first_names: Mapping[str, Sequence[str]],
    last_names: Sequence[str],
    taken: set[tuple[str, str]],
) -> tuple[str, str]:
    """Deterministic in the mobile number; probes on until the full name is unused."""
    genders = sorted(first_names)
    firsts = first_names[genders[_digest(mobile, "gender") % len(genders)]]
    first_start = _digest(mobile, "first") % len(firsts)
    last_start = _digest(mobile, "last") % len(last_names)
    for attempt in range(len(firsts) * len(last_names)):
        name = (
            firsts[(first_start + attempt) % len(firsts)],
            last_names[(last_start + attempt // len(firsts)) % len(last_names)],
        )
        if name not in taken:
            taken.add(name)
            return name
    raise SeedError("the name pools are too small for this many users")


def build_seed(people: Mapping[str, Any], names: Mapping[str, Any]) -> Seed:
    group_count = _get(people, "groups", int, "")
    per_group = _section(people, "per_group", "")
    counts = {kind: _get(per_group, kind, int, "per_group.") for kind in KINDS}
    mobile = _section(people, "mobile", "")
    prefix = _get(mobile, "prefix", str, "mobile.")
    group_digits = _get(mobile, "group_digits", int, "mobile.")
    index_digits = _get(mobile, "index_digits", int, "mobile.")
    temporary_group = _get(mobile, "temporary_group_number", int, "mobile.")
    codes_source = _section(mobile, "kind_codes", "mobile.")
    codes = {kind: _get(codes_source, kind, int, "mobile.kind_codes.") for kind in KINDS}
    domain = _get(people, "email_domain", str, "")
    labels_source = _section(people, "email_labels", "")
    labels = {kind: _get(labels_source, kind, str, "email_labels.") for kind in KINDS}
    ta = _section(people, "ta_admin", "")
    group_name = _get(people, "group_name", str, "")
    fields_of_study = _strings(people, "fields_of_study", "")
    timestamp = _get(people, "fixture_timestamp", str, "")
    try:
        namespace = uuid.UUID(_get(people, "id_namespace", str, ""))
    except ValueError:
        raise SeedError("id_namespace must be a UUID") from None

    if len(prefix) + group_digits + 1 + index_digits != MOBILE_LENGTH:
        raise SeedError(f"the mobile scheme must add up to {MOBILE_LENGTH} digits")
    if not 1 <= group_count < min(temporary_group, 10**group_digits):
        raise SeedError("groups must be at least 1 and below the temporary group number")
    if len(set(codes.values())) != len(KINDS) or not all(0 <= c <= 9 for c in codes.values()):
        raise SeedError("kind_codes must be distinct single digits")
    for kind, count in counts.items():
        if not 1 <= count < 10**index_digits:
            raise SeedError(f"per_group.{kind} must be at least 1 and fit the index digits")

    first_names_source = _section(names, "first_names", "")
    first_names = {
        gender: _strings(first_names_source, gender, "first_names.")
        for gender in sorted(first_names_source)
    }
    last_names = _strings(names, "last_names", "")
    if not first_names:
        raise SeedError("first_names needs at least one list")

    taken: set[tuple[str, str]] = set()
    students_made = 0
    members: list[Person] = []

    def make(kind: str, group: int, index: int, name: tuple[str, str] | None) -> Person:
        number = f"{prefix}{group:0{group_digits}d}{codes[kind]}{index:0{index_digits}d}"
        try:
            if normalize_mobile(number) != number:
                raise SeedError(f"{number} is not in canonical form")
        except InvalidMobileError:
            raise SeedError(f"{number} is not a valid mobile number") from None
        first, last = name or _pick_name(number, first_names, last_names, taken)
        return Person(
            sub=uuid.uuid5(namespace, number),
            mobile=number,
            email=f"{labels[kind]}.{group}.{index}@{domain}",
            first_name=first,
            last_name=last,
            kind=kind,
            field_of_study=fields_of_study[students_made % len(fields_of_study)]
            if kind == "student"
            else "",
            group=group,
        )

    groups = tuple(
        Group(n, f"group-{n}", group_name.format(number=n)) for n in range(1, group_count + 1)
    )
    for group in groups:
        for kind in KINDS:
            for index in range(1, counts[kind] + 1):
                members.append(make(kind, group.number, index, None))
                students_made += kind == "student"
    ta_name = (_get(ta, "first_name", str, "ta_admin."), _get(ta, "last_name", str, "ta_admin."))
    taken.add(ta_name)
    members.append(make("admin", NO_GROUP, 1, ta_name))

    for attribute in ("mobile", "email", "sub"):
        values = [getattr(person, attribute) for person in members]
        if len(values) != len(set(values)):
            raise SeedError(f"the scheme produces duplicate {attribute} values")
    return Seed(groups=groups, people=tuple(members), timestamp=timestamp)


def _load(path: Path) -> Mapping[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise SeedError(f"{path.name} must contain a mapping")
    return document


def load_sources(root: Path = ROOT) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    return _load(root / "seed" / "people.yaml"), _load(root / "seed" / "names.yaml")


def load_seed(root: Path = ROOT) -> Seed:
    return build_seed(*load_sources(root))


def dumps(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def profile_fixture(seed: Seed) -> list[dict[str, Any]]:
    return [
        {
            "model": "accounts.profile",
            "pk": str(person.sub),
            "fields": {
                "mobile": person.mobile,
                "email": person.email,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "role": person.role,
                "consultant_type": person.consultant_type,
                "is_active": True,
                "identity_synced_at": seed.timestamp,
                "field_of_study": person.field_of_study,
                "avatar_url": "",
                "bio": "",
                "created_at": seed.timestamp,
                "updated_at": seed.timestamp,
            },
        }
        for person in sorted(seed.people, key=lambda person: person.mobile)
    ]


def fixture_files(seed: Seed) -> dict[str, str]:
    """Fixture text by path relative to the backend folder."""
    return {PROFILES_FIXTURE: dumps(profile_fixture(seed))}


def client_secret(password: str, client_id: str) -> str:
    """Derived, not stored, so the realm file and the credential files agree after any reset."""
    digest = hmac.new(
        password.encode(), f"gradian-seed-client:{client_id}".encode(), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _audience_mapper(name: str, audience: str) -> dict[str, Any]:
    return {
        "name": name,
        "protocol": "openid-connect",
        "protocolMapper": "oidc-audience-mapper",
        "consentRequired": False,
        "config": {
            "included.client.audience": audience,
            "id.token.claim": "false",
            "access.token.claim": "true",
            "introspection.token.claim": "true",
        },
    }


def realm_users(seed: Seed, password: str) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    for person in seed.people:
        attributes = {"mobile": [person.mobile]}
        if person.consultant_type:
            attributes["consultant_type"] = [person.consultant_type]
        users.append(
            {
                "id": str(person.sub),
                "username": person.mobile,
                "email": person.email,
                "emailVerified": True,
                "enabled": True,
                "firstName": person.first_name,
                "lastName": person.last_name,
                "attributes": attributes,
                "credentials": [{"type": "password", "value": password, "temporary": False}],
                "realmRoles": [person.role],
            }
        )
    for group in seed.groups:
        users.append(
            {
                "username": f"service-account-{group.client_id}",
                "enabled": True,
                "serviceAccountClientId": group.client_id,
                "realmRoles": ["service"],
            }
        )
    return users


def service_clients(seed: Seed, password: str) -> list[dict[str, Any]]:
    """One confidential client per group (DEC-20). Its service account holds the `service` role
    and its tokens carry the audience `gradian-core`, so it can call the Core Service."""
    return [
        {
            "clientId": group.client_id,
            "name": f"Service of {group.name}",
            "enabled": True,
            "publicClient": False,
            "secret": client_secret(password, group.client_id),
            "standardFlowEnabled": False,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "serviceAccountsEnabled": True,
            "protocolMappers": [_audience_mapper("gradian-core-audience", "gradian-core")],
        }
        for group in seed.groups
    ]


def web_audience_mappers(seed: Seed) -> list[dict[str, Any]]:
    """Put each group service's client id in the audience of the signed-in user's token, so that
    the service can check that the token was meant for it (DES-REG-05)."""
    return [
        _audience_mapper(f"{group.client_id}-audience", group.client_id) for group in seed.groups
    ]


def _csv(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def credential_files(seed: Seed, password: str) -> dict[str, str]:
    """Credential CSV text by file name: users per group, one service client per group, and the
    TA admin, who belongs to no group. The role column is the kind, so top-rankers stand out."""
    header = ("role", "name", "mobile", "password")

    def rows(people: Sequence[Person]) -> list[tuple[str, str, str, str]]:
        return [(p.kind, p.full_name, p.mobile, password) for p in people]

    files = {"ta.csv": _csv(header, rows(seed.ungrouped))}
    for group in seed.groups:
        files[f"{group.slug}.csv"] = _csv(header, rows(seed.members(group)))
        files[f"{group.slug}-service.csv"] = _csv(
            ("client_id", "client_secret"),
            [(group.client_id, client_secret(password, group.client_id))],
        )
    return files


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        seed = load_seed()
    except SeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for relative, text in fixture_files(seed).items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
