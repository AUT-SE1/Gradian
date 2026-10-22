import json
import os
import subprocess
import unittest
from pathlib import Path

import render_realm
from covers import covers

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "refuse_production.sh"


def run_guard(environment: str | None) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ENVIRONMENT"}}
    if environment is not None:
        env["ENVIRONMENT"] = environment
    return subprocess.run(
        [str(GUARD), "seed-render"], env=env, capture_output=True, text=True, check=False
    )


@covers("SYS-DATA-07")
class ProductionGuardTests(unittest.TestCase):
    def test_refuses_in_production(self) -> None:
        result = run_guard("production")
        self.assertEqual(result.returncode, 1)
        self.assertIn("seed-render", result.stderr)

    def test_allows_other_environments(self) -> None:
        for environment in ("development", "test"):
            with self.subTest(environment=environment):
                self.assertEqual(run_guard(environment).returncode, 0)

    def test_realm_renderer_refuses_production_too(self) -> None:
        env = {**os.environ, "ENVIRONMENT": "production"}
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "render_realm.py"),
                "--out",
                str(ROOT / "build" / "never-written.json"),
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)


class RenderRealmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads((ROOT / "keycloak" / "realm-template.json").read_text("utf-8"))
        self.profile = json.loads((ROOT / "keycloak" / "user-profile.json").read_text("utf-8"))

    def clients(self, *, production: bool) -> set[str]:
        realm = render_realm.render(self.template, self.profile, production=production)
        return {client["clientId"] for client in realm["clients"]}

    def test_test_client_exists_only_outside_production(self) -> None:
        self.assertIn("gradian-test", self.clients(production=False))
        self.assertNotIn("gradian-test", self.clients(production=True))

    def test_realm_has_the_designed_roles_and_settings(self) -> None:
        roles = {role["name"] for role in self.template["roles"]["realm"]}
        self.assertEqual(roles, {"student", "consultant", "professor", "admin", "service"})
        self.assertTrue(self.template["rememberMe"])
        self.assertFalse(self.template["resetPasswordAllowed"])
        self.assertLessEqual(self.template["accessTokenLifespan"], 600)
        self.assertEqual(self.template["failureFactor"], 5)

    def test_registration_identity_rules_are_enforced_by_keycloak_config(self) -> None:
        self.assertEqual(self.template["passwordPolicy"], "length(8)")
        self.assertFalse(self.template["duplicateEmailsAllowed"])

        attributes = {attribute["name"]: attribute for attribute in self.profile["attributes"]}
        self.assertEqual(
            attributes["username"]["validations"]["pattern"]["pattern"], r"^09\d{9}$"
        )
        expected_name_pattern = r"^(?=.*[\p{L}\p{M}])[\p{L}\p{M}\u200c ]+$"
        for field in ("firstName", "lastName"):
            with self.subTest(field=field):
                attribute = attributes[field]
                self.assertEqual(attribute["required"]["roles"], ["admin", "user"])
                self.assertEqual(
                    attribute["validations"]["pattern"]["pattern"], expected_name_pattern
                )
        self.assertEqual(attributes["email"]["required"]["roles"], ["admin", "user"])
        self.assertIn("email", attributes["email"]["validations"])
        self.assertEqual(attributes["mobile"]["permissions"]["edit"], ["admin"])
        self.assertEqual(attributes["consultant_type"]["permissions"]["edit"], ["admin"])

    def test_web_client_uses_pkce_and_no_password_grant(self) -> None:
        web = next(c for c in self.template["clients"] if c["clientId"] == "gradian-web")
        self.assertTrue(web["publicClient"])
        self.assertFalse(web["directAccessGrantsEnabled"])
        self.assertEqual(web["attributes"]["pkce.code.challenge.method"], "S256")

    def test_user_profile_is_embedded_as_a_json_string(self) -> None:
        realm = render_realm.render(self.template, self.profile, production=False)
        config = realm["components"][render_realm.USER_PROFILE_PROVIDER][0]["config"]
        embedded = json.loads(config["kc.user.profile.config"][0])
        names = {attribute["name"] for attribute in embedded["attributes"]}
        self.assertTrue({"username", "email", "firstName", "lastName", "mobile"} <= names)

    def test_rendering_does_not_modify_the_template(self) -> None:
        before = json.dumps(self.template, sort_keys=True)
        render_realm.render(self.template, self.profile, production=False)
        self.assertEqual(json.dumps(self.template, sort_keys=True), before)
