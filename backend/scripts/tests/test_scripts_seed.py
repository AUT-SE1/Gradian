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
                secrets.add(client["secret"])
                audiences = [
                    m["config"]["included.client.audience"]
                    for m in client["protocolMappers"]
                    if m["protocolMapper"] == "oidc-audience-mapper"
                ]
                self.assertEqual(audiences, ["gradian-core", group.client_id])
                account = self.users[f"service-account-{group.client_id}"]
                self.assertEqual(account["serviceAccountClientId"], group.client_id)
                self.assertEqual(account["realmRoles"], ["service"])
        self.assertEqual(len(secrets), len(self.seed.groups))

    def test_a_group_can_sign_people_in_on_its_own_pages_with_single_sign_on(self) -> None:
        for group in self.seed.groups:
            with self.subTest(group=group.slug):
                client = self.clients[group.client_id]
                self.assertTrue(client["standardFlowEnabled"])
                self.assertFalse(client["implicitFlowEnabled"])
                self.assertEqual(
                    client["redirectUris"], [f"http://localhost:{8000 + group.number}/*"]
                )
                self.assertEqual(client["webOrigins"], [])
                self.assertEqual(
                    client["attributes"]["post.logout.redirect.uris"], "${FRONTEND_URL}/"
                )
                claims = {
                    m["config"]["claim.name"]
                    for m in client["protocolMappers"]
                    if m["protocolMapper"] == "oidc-usermodel-attribute-mapper"
                }
                self.assertEqual(claims, {"consultant_type"})

    def test_a_service_that_runs_elsewhere_is_set_in_one_place(self) -> None:
        people, names = sources()
        people["group_services"] = {"origin": "https://svc{port}.example", "port_base": 9100}
        built = seed_generate.build_seed(people, names)
        self.assertEqual(built.groups[2].origin, "https://svc9103.example")

    def test_a_group_service_address_without_a_port_placeholder_is_refused(self) -> None:
        for origin in ("http://localhost:8001", "localhost:{port}"):
            with self.subTest(origin=origin):
                people, names = sources()
                people["group_services"] = {"origin": origin, "port_base": 8000}
                with self.assertRaises(seed_generate.SeedError):
                    seed_generate.build_seed(people, names)

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


def requirement_services() -> dict[str, list[tuple[str, str, str]]]:
    """AC-SERVICES from the requirements document: (key, English title, Persian title) per panel."""
    text = (ROOT / "docs" / "01-requirements.md").read_text(encoding="utf-8")
    table = text.split("### AC-SERVICES", 1)[1].split("###", 1)[0]
    found: dict[str, list[tuple[str, str, str]]] = {}
    for line in table.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0].startswith("`"):
            key = cells[0].strip("`")
            found.setdefault(key.split(".")[0], []).append((key, cells[2], cells[3]))
    return found


Documents = tuple[dict[str, Any], dict[str, Any], dict[str, Any]]


def content_sources() -> Documents:
    def read(name: str) -> dict[str, Any]:
        return copy.deepcopy(dict(seed_generate._load(ROOT / "seed" / "content" / f"{name}.yaml")))

    return read("services"), read("landing"), read("widgets")


@covers("SYS-DATA-06", "SYS-PNL-01", "SYS-PNL-02")
class ServiceContentTests(unittest.TestCase):
    def test_the_entries_are_exactly_those_of_ac_services_in_their_order(self) -> None:
        expected = requirement_services()
        self.assertEqual(
            {p: len(rows) for p, rows in expected.items()},
            {"student": 10, "admin": 3, "consultant": 6, "professor": 6},
        )
        content = seed_generate.load_content(ROOT)
        built: dict[str, list[tuple[str, str, str]]] = {}
        for entry in content.services:
            built.setdefault(entry["panel"], []).append(
                (entry["key"], entry["title_en"], entry["title_fa"])
            )
        self.assertEqual(built, expected)

    def test_display_order_counts_from_one_within_each_panel(self) -> None:
        orders: dict[str, list[int]] = {}
        for entry in seed_generate.load_content(ROOT).services:
            orders.setdefault(entry["panel"], []).append(entry["order"])
        for panel, values in orders.items():
            self.assertEqual(values, list(range(1, len(values) + 1)), panel)

    def test_nothing_is_connected_yet_and_every_entry_names_a_group(self) -> None:
        for entry in seed_generate.load_content(ROOT).services:
            self.assertEqual(entry["target_url"], "")
            self.assertEqual(entry["mode"], "redirect")
            self.assertIsInstance(entry["owner_group"], int)

    def test_the_fixtures_hold_the_services_and_every_content_block(self) -> None:
        files = seed_generate.fixture_files(seed_of(10))
        services = json.loads(files[seed_generate.SERVICES_FIXTURE])
        self.assertEqual(len(services), 25)
        self.assertEqual({row["model"] for row in services}, {"registry.serviceentry"})
        blocks = json.loads(files[seed_generate.LANDING_FIXTURE]) + json.loads(
            files[seed_generate.WIDGETS_FIXTURE]
        )
        self.assertEqual(len(blocks), 11)
        self.assertEqual({row["model"] for row in blocks}, {"panels.contentblock"})

    def test_the_content_does_not_depend_on_the_number_of_groups(self) -> None:
        three = seed_generate.fixture_files(seed_of(3))
        ten = seed_generate.fixture_files(seed_of(10))
        for path in (seed_generate.SERVICES_FIXTURE, seed_generate.LANDING_FIXTURE):
            self.assertEqual(three[path], ten[path])


@covers("SYS-DATA-06")
class ContentValidationTests(unittest.TestCase):
    def build(self) -> seed_generate.Content:
        return seed_generate.build_content(*content_sources())

    def refuses(self, change: Callable[..., object]) -> None:
        services, landing, widgets = content_sources()
        change(services, landing, widgets)
        with self.assertRaises(seed_generate.SeedError):
            seed_generate.build_content(services, landing, widgets)

    def test_the_committed_content_is_valid(self) -> None:
        self.assertEqual(len(self.build().services), 25)

    def test_content_that_breaks_a_rule_is_refused(self) -> None:
        breakers: dict[str, Callable[..., object]] = {
            "a repeated key": lambda s, *_: s["services"].append(dict(s["services"][0])),
            "a key that is not <panel>.<name>": lambda s, *_: s["services"][0].update(key="exam"),
            "an unknown panel": lambda s, *_: s["services"][0].update(key="teacher.exam"),
            "an unknown mode": lambda s, *_: s["services"][0].update(mode="popup"),
            "a target that is not a web address": lambda s, *_: s["services"][0].update(
                target_url="ftp://x"
            ),
            "an owner group of zero": lambda s, *_: s["services"][0].update(owner_group=0),
            "a missing title": lambda s, *_: s["services"][0].pop("title_fa"),
            "no services": lambda s, *_: s.update(services=[]),
            "a missing landing section": lambda s, landing, w: landing.pop("hero"),
            "an unknown landing section": lambda s, landing, w: landing.update(extra={}),
            "a missing widget": lambda s, landing, widgets: widgets.pop("welcome"),
        }
        for label, breaker in breakers.items():
            with self.subTest(label):
                self.refuses(breaker)

    def test_a_connected_entry_keeps_its_target_and_mode_in_the_fixture(self) -> None:
        services, landing, widgets = content_sources()
        services["services"][0].update(target_url="https://g1.example/app", mode="redirect")
        content = seed_generate.build_content(services, landing, widgets)
        row = seed_generate.service_fixture(content)[0]["fields"]
        self.assertEqual((row["target_url"], row["mode"]), ("https://g1.example/app", "redirect"))
