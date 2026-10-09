import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import render_realm
import seed_credentials
import seed_generate
from covers import covers

from gradian_auth.mobile import normalize_mobile

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "sentinel-Password-1"
PER_KIND = {
    ("student", ""): 40,
    ("consultant", "consultant"): 10,
    ("consultant", "top_ranker"): 10,
    ("professor", ""): 10,
    ("admin", ""): 10,
}


def sources() -> tuple[dict[str, Any], dict[str, Any]]:
    people, names = seed_generate.load_sources(ROOT)
    return copy.deepcopy(dict(people)), copy.deepcopy(dict(names))


def seed_of(groups: int = 10) -> seed_generate.Seed:
    people, names = sources()
    people["groups"] = groups
    return seed_generate.build_seed(people, names)


@covers("SYS-DATA-03")
class AllocationTests(unittest.TestCase):
    def test_the_pool_has_every_role_and_does_not_depend_on_the_group_count(self) -> None:
        for groups in (10, 3):
            seed = seed_of(groups)
            self.assertEqual(len(seed.groups), groups)
            found = Counter((p.role, p.consultant_type) for p in seed.people)
            self.assertEqual(found, Counter(PER_KIND))

    def test_users_belong_to_no_group(self) -> None:
        for person in seed_of(3).people:
            self.assertNotIn("group", vars(person))


@covers("SYS-DATA-02")
class IdentityTests(unittest.TestCase):
    def test_mobiles_are_canonical_unique_and_ids_follow_them(self) -> None:
        seed = seed_of(10)
        mobiles = [p.mobile for p in seed.people]
        self.assertEqual(len(mobiles), len(set(mobiles)))
        for person in seed.people:
            with self.subTest(mobile=person.mobile):
                self.assertEqual(normalize_mobile(person.mobile), person.mobile)
                self.assertEqual(person.sub.version, 5)
                self.assertTrue(person.email.endswith("@gradian.test"))
        self.assertEqual(len({p.email for p in seed.people}), len(seed.people))

    def test_students_get_a_field_of_study_and_nobody_else_does(self) -> None:
        for person in seed_of(3).people:
            self.assertEqual(bool(person.field_of_study), person.kind == "student", person.mobile)

    def test_a_small_name_pool_is_refused_instead_of_repeating_names(self) -> None:
        people, names = sources()
        names["last_names"] = names["last_names"][:1]
        names["first_names"] = {"female": names["first_names"]["female"][:2]}
        with self.assertRaises(seed_generate.SeedError):
            seed_generate.build_seed(people, names)


@covers("SYS-DATA-04")
class DeterminismTests(unittest.TestCase):
    def test_two_runs_give_identical_output(self) -> None:
        first, second = seed_of(10), seed_of(10)
        self.assertEqual(seed_generate.fixture_files(first), seed_generate.fixture_files(second))
        self.assertEqual(
            seed_generate.realm_users(first, PASSWORD), seed_generate.realm_users(second, PASSWORD)
        )
        self.assertEqual(
            seed_generate.credential_files(first, PASSWORD),
            seed_generate.credential_files(second, PASSWORD),
        )

    def test_the_password_never_reaches_a_fixture(self) -> None:
        for relative, text in seed_generate.fixture_files(seed_of(3)).items():
            self.assertNotIn(PASSWORD, text, relative)

    def test_a_scheme_that_breaks_a_rule_is_refused(self) -> None:
        breakers: dict[str, Callable[[dict[str, Any]], object]] = {
            "no groups": lambda people: people.update(groups=0),
            "a mobile number of the wrong length": lambda people: people["mobile"].update(
                index_digits=5
            ),
            "repeated kind codes": lambda people: people["mobile"]["kind_codes"].update(admin=1),
            "the temporary code used by a kind": lambda people: people["mobile"].update(
                temporary_kind_code=1
            ),
            "no students": lambda people: people["users"].update(student=0),
            "an id namespace that is not a uuid": lambda people: people.update(id_namespace="x"),
        }
        for label, breaker in breakers.items():
            with self.subTest(label):
                people, names = sources()
                breaker(people)
                with self.assertRaises(seed_generate.SeedError):
                    seed_generate.build_seed(people, names)


class RealmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = seed_generate.load_seed(ROOT)
        template = json.loads((ROOT / "keycloak" / "realm-template.json").read_text("utf-8"))
        profile = json.loads((ROOT / "keycloak" / "user-profile.json").read_text("utf-8"))
        self.realm = render_realm.render(
            template, profile, production=False, seed=self.seed, password=PASSWORD
        )
        self.users = {u["username"]: u for u in self.realm["users"]}
        self.clients = {c["clientId"]: c for c in self.realm["clients"]}

    def test_user_ids_in_the_realm_are_the_profile_ids_in_the_fixture(self) -> None:
        fixture = seed_generate.profile_fixture(self.seed)
        by_mobile = {row["fields"]["mobile"]: row["pk"] for row in fixture}
        in_realm = {username: user["id"] for username, user in self.users.items() if "id" in user}
        self.assertEqual(in_realm, by_mobile)
        for pk in by_mobile.values():
            uuid.UUID(pk)

    def test_every_seeded_user_can_sign_in_and_is_complete(self) -> None:
        for person in self.seed.people:
            with self.subTest(mobile=person.mobile):
                user = self.users[person.mobile]
                self.assertTrue(user["enabled"] and user["emailVerified"])
                self.assertEqual(user["realmRoles"], [person.role])
                self.assertEqual(user["attributes"]["mobile"], [person.mobile])
                self.assertEqual(
                    user["attributes"].get("consultant_type"),
                    [person.consultant_type] if person.consultant_type else None,
                )
                self.assertEqual(
                    user["credentials"],
                    [{"type": "password", "value": PASSWORD, "temporary": False}],
                )
                for field in ("email", "firstName", "lastName"):
                    self.assertTrue(user[field])

    def test_the_realm_needs_a_password(self) -> None:
        with self.assertRaises(ValueError):
            render_realm.render(
                {"clients": [{"clientId": "gradian-web", "protocolMappers": []}]},
                {},
                production=False,
                seed=self.seed,
            )

    def test_each_group_has_its_own_service_client_with_the_service_role(self) -> None:
        secrets = set()
        for group in self.seed.groups:
            with self.subTest(group=group.slug):
                client = self.clients[group.client_id]
                self.assertFalse(client["publicClient"])
                self.assertTrue(client["serviceAccountsEnabled"])
                self.assertFalse(client["directAccessGrantsEnabled"])
                self.assertFalse(client["standardFlowEnabled"])
                secrets.add(client["secret"])
                audiences = [
                    m["config"]["included.client.audience"] for m in client["protocolMappers"]
                ]
                self.assertEqual(audiences, ["gradian-core"])
                account = self.users[f"service-account-{group.client_id}"]
                self.assertEqual(account["serviceAccountClientId"], group.client_id)
                self.assertEqual(account["realmRoles"], ["service"])
        self.assertEqual(len(secrets), len(self.seed.groups))

    def test_user_tokens_carry_every_group_service_as_audience(self) -> None:
        wanted = {group.client_id for group in self.seed.groups} | {"gradian-core"}
        for client_id in ("gradian-web", "gradian-test"):
            with self.subTest(client=client_id):
                mappers = self.clients[client_id]["protocolMappers"]
                found = {
                    m["config"]["included.client.audience"]
                    for m in mappers
                    if m["protocolMapper"] == "oidc-audience-mapper"
                }
                self.assertEqual(found, wanted)

    def test_a_service_secret_depends_on_the_password_and_the_client(self) -> None:
        secret = seed_generate.client_secret
        self.assertEqual(secret("a", "group-1"), secret("a", "group-1"))
        self.assertNotEqual(secret("a", "group-1"), secret("b", "group-1"))
        self.assertNotEqual(secret("a", "group-1"), secret("a", "group-2"))


def read_rows(text: str) -> list[list[str]]:
    return [line.split(",") for line in text.splitlines()]


@covers("SYS-DATA-05")
class CredentialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = seed_of(3)
        self.files = seed_generate.credential_files(self.seed, PASSWORD)

    def test_one_file_lists_every_seeded_user_with_the_shared_password(self) -> None:
        self.assertEqual(sorted(self.files), ["services.csv", "users.csv"])
        rows = read_rows(self.files["users.csv"])
        self.assertEqual(rows[0], ["role", "name", "mobile", "password"])
        self.assertEqual({row[2] for row in rows[1:]}, {p.mobile for p in self.seed.people})
        self.assertEqual({row[3] for row in rows[1:]}, {PASSWORD})

    def test_a_top_ranker_is_told_apart_from_a_consultant(self) -> None:
        roles = Counter(row[0] for row in read_rows(self.files["users.csv"])[1:])
        self.assertEqual((roles["top_ranker"], roles["consultant"]), (10, 10))

    def test_each_group_has_its_service_credentials_in_one_file(self) -> None:
        rows = read_rows(self.files["services.csv"])
        self.assertEqual(rows[0], ["group", "client_id", "client_secret"])
        self.assertEqual(
            rows[1:],
            [
                [str(g.number), g.client_id, seed_generate.client_secret(PASSWORD, g.client_id)]
                for g in self.seed.groups
            ],
        )

    def test_files_are_replaced_private_and_readable_in_excel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "group-1.csv").write_text("an earlier version's file", encoding="utf-8")
            (out / "ta.csv").write_text("an earlier version's file", encoding="utf-8")
            (out / "notes.csv").write_text("not ours", encoding="utf-8")
            seed_credentials.write_files(out, self.files)
            self.assertFalse((out / "group-1.csv").exists())
            self.assertFalse((out / "ta.csv").exists())
            self.assertTrue((out / "notes.csv").exists())
            users = out / "users.csv"
            self.assertEqual(users.stat().st_mode & 0o777, 0o600)
            self.assertTrue(users.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(users.read_text(encoding="utf-8-sig"), self.files["users.csv"])


@covers("SYS-DATA-07")
class CredentialsProductionGuardTests(unittest.TestCase):
    def test_credentials_are_refused_in_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env: Mapping[str, str] = {
                **os.environ,
                "ENVIRONMENT": "production",
                "SEED_DEFAULT_PASSWORD": PASSWORD,
            }
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "seed_credentials.py"), "--out", tmp],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(list(Path(tmp).iterdir()), [])
