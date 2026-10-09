"""The Admin client against an in-memory stand-in for the Admin API."""

import re
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import requests

from gradian_keycloak import admin_client
from gradian_keycloak.admin_client import KeycloakAdminClient, NewUser
from gradian_keycloak.errors import KeycloakError
from gradian_keycloak.tests.base import FakeResponse, KeycloakSettingsTestCase, StubTokens

Handler = Callable[[str, dict[str, Any]], FakeResponse]
BASE = "http://keycloak.internal.test/admin/realms/gradian"


class AdminApi:
    """Routes `requests.request` calls by (method, path) and records them."""

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Handler | FakeResponse] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def on(self, method: str, path: str, outcome: Handler | FakeResponse) -> None:
        self.routes[(method, path)] = outcome

    def __call__(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        path = url.removeprefix(BASE)
        self.calls.append((method, path, kwargs))
        outcome = self.routes.get((method, path))
        if outcome is None:
            return FakeResponse(404, {})
        return outcome(path, kwargs) if callable(outcome) else outcome

    def paths(self, method: str) -> list[str]:
        return [path for m, path, _ in self.calls if m == method]


class AdminClientTests(KeycloakSettingsTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api = AdminApi()
        patcher = patch("requests.request", side_effect=self.api)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client_under_test = KeycloakAdminClient(tokens=StubTokens())  # type: ignore[arg-type]  # a stub with the one method used

    def test_calls_carry_the_service_token_and_the_configured_timeout(self) -> None:
        self.api.on("GET", "/users/u1", FakeResponse(200, {"id": "u1"}))
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        self.client_under_test.set_enabled("u1", False)
        kwargs = self.api.calls[0][2]
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer stub-token"})
        self.assertEqual(kwargs["timeout"], 5.0)

    def test_update_user_merges_the_changes_into_the_stored_representation(self) -> None:
        stored = {"id": "u1", "firstName": "Ali", "lastName": "Reza", "email": "a@x.test"}
        self.api.on("GET", "/users/u1", FakeResponse(200, stored))
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        self.client_under_test.update_user("u1", {"first_name": "Sara", "email": "s@x.test"})
        sent = next(kw["json"] for m, _, kw in self.api.calls if m == "PUT")
        self.assertEqual(
            sent, {"id": "u1", "firstName": "Sara", "lastName": "Reza", "email": "s@x.test"}
        )

    def test_set_enabled_writes_the_flag_back(self) -> None:
        self.api.on("GET", "/users/u1", FakeResponse(200, {"id": "u1", "enabled": True}))
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        self.client_under_test.set_enabled("u1", False)
        sent = next(kw["json"] for m, _, kw in self.api.calls if m == "PUT")
        self.assertIs(sent["enabled"], False)

    def test_grant_role_posts_the_role_representation(self) -> None:
        role = {"id": "r1", "name": "student"}
        self.api.on("GET", "/roles/student", FakeResponse(200, role))
        self.api.on("POST", "/users/u1/role-mappings/realm", FakeResponse(204))
        self.client_under_test.grant_role("u1", "student")
        sent = next(kw["json"] for m, _, kw in self.api.calls if m == "POST")
        self.assertEqual(sent, [role])

    def new_user(self, **changes: str) -> NewUser:
        values = {
            "mobile": "09000100001",
            "email": "a@x.test",
            "first_name": "علی",
            "last_name": "رضایی",
            "password": "pass-1234",
            "role": "consultant",
            "consultant_type": "top_ranker",
        }
        return NewUser(**{**values, **changes})

    def test_create_user_returns_the_new_id_and_grants_the_role(self) -> None:
        self.api.on(
            "POST", "/users", FakeResponse(201, headers={"Location": f"{BASE}/users/new-id"})
        )
        self.api.on("GET", "/roles/consultant", FakeResponse(200, {"name": "consultant"}))
        self.api.on("POST", "/users/new-id/role-mappings/realm", FakeResponse(204))
        self.assertEqual(self.client_under_test.create_user(self.new_user()), "new-id")
        body = next(kw["json"] for m, p, kw in self.api.calls if (m, p) == ("POST", "/users"))
        self.assertEqual(body["username"], "09000100001")
        self.assertEqual(
            body["attributes"], {"mobile": ["09000100001"], "consultant_type": ["top_ranker"]}
        )
        self.assertEqual(body["credentials"][0]["temporary"], False)

    def test_create_user_removes_the_account_when_the_role_cannot_be_assigned(self) -> None:
        self.api.on(
            "POST", "/users", FakeResponse(201, headers={"Location": f"{BASE}/users/new-id"})
        )
        self.api.on("GET", "/roles/consultant", FakeResponse(500, {}))
        self.api.on("DELETE", "/users/new-id", FakeResponse(204))
        with self.assertRaises(KeycloakError):
            self.client_under_test.create_user(self.new_user())
        self.assertEqual(self.api.paths("DELETE"), ["/users/new-id"])

    def test_the_original_error_survives_a_failed_cleanup(self) -> None:
        self.api.on(
            "POST", "/users", FakeResponse(201, headers={"Location": f"{BASE}/users/new-id"})
        )
        self.api.on("GET", "/roles/consultant", FakeResponse(500, {}))
        self.api.on("DELETE", "/users/new-id", FakeResponse(500, {}))
        with self.assertRaisesRegex(KeycloakError, "roles/consultant"):
            self.client_under_test.create_user(self.new_user())

    def test_a_student_has_no_consultant_attribute(self) -> None:
        self.api.on("POST", "/users", FakeResponse(201, headers={"Location": f"{BASE}/users/n"}))
        self.api.on("GET", "/roles/student", FakeResponse(200, {"name": "student"}))
        self.api.on("POST", "/users/n/role-mappings/realm", FakeResponse(204))
        self.client_under_test.create_user(self.new_user(role="student", consultant_type=""))
        body = next(kw["json"] for m, p, kw in self.api.calls if (m, p) == ("POST", "/users"))
        self.assertEqual(body["attributes"], {"mobile": ["09000100001"]})

    def test_set_panel_role_replaces_the_old_panel_role_and_keeps_other_roles(self) -> None:
        self.api.on(
            "GET", "/users/u1", FakeResponse(200, {"id": "u1", "attributes": {"mobile": ["09"]}})
        )
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        current = [{"name": "student"}, {"name": "offline_access"}]
        self.api.on("GET", "/users/u1/role-mappings/realm", FakeResponse(200, current))
        self.api.on("DELETE", "/users/u1/role-mappings/realm", FakeResponse(204))
        self.api.on("GET", "/roles/admin", FakeResponse(200, {"name": "admin"}))
        self.api.on("POST", "/users/u1/role-mappings/realm", FakeResponse(204))
        self.client_under_test.set_panel_role("u1", "admin", "")
        removed = next(kw["json"] for m, _, kw in self.api.calls if m == "DELETE")
        self.assertEqual(removed, [{"name": "student"}])
        granted = next(kw["json"] for m, _, kw in self.api.calls if m == "POST")
        self.assertEqual(granted, [{"name": "admin"}])

    def test_set_panel_role_changes_nothing_when_the_role_is_already_the_only_one(self) -> None:
        self.api.on("GET", "/users/u1", FakeResponse(200, {"id": "u1"}))
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        self.api.on("GET", "/users/u1/role-mappings/realm", FakeResponse(200, [{"name": "admin"}]))
        self.client_under_test.set_panel_role("u1", "admin", "")
        self.assertEqual(self.api.paths("DELETE") + self.api.paths("POST"), [])

    def test_set_panel_role_sets_or_clears_the_consultant_type_attribute(self) -> None:
        stored = {"id": "u1", "attributes": {"consultant_type": ["consultant"]}}
        self.api.on("GET", "/users/u1", FakeResponse(200, stored))
        self.api.on("PUT", "/users/u1", FakeResponse(204))
        self.api.on(
            "GET", "/users/u1/role-mappings/realm", FakeResponse(200, [{"name": "consultant"}])
        )
        self.client_under_test.set_panel_role("u1", "consultant", "top_ranker")
        sent = next(kw["json"] for m, _, kw in self.api.calls if m == "PUT")
        self.assertEqual(sent["attributes"], {"consultant_type": ["top_ranker"]})

    def test_list_panel_users_merges_roles_and_adds_roleless_users_as_students(self) -> None:
        def users(role: str) -> list[dict[str, Any]]:
            return {
                "student": [{"id": "s1", "username": "0901", "enabled": True}],
                "admin": [{"id": "s1", "username": "0901", "enabled": True}],
                "consultant": [
                    {
                        "id": "c1",
                        "username": "0902",
                        "email": "c@x.test",
                        "firstName": "سارا",
                        "lastName": "کریمی",
                        "enabled": False,
                        "attributes": {"consultant_type": ["top_ranker"]},
                    }
                ],
            }.get(role, [])

        for role in ("student", "consultant", "professor", "admin"):
            self.api.on("GET", f"/roles/{role}/users", FakeResponse(200, users(role)))
        everyone = [
            {"id": "s1", "username": "0901"},
            {"id": "n1", "username": "0903"},
            {"id": "svc", "username": "service-account-x", "serviceAccountClientId": "x"},
        ]
        self.api.on("GET", "/users", FakeResponse(200, everyone))
        found = {u.sub: u for u in self.client_under_test.list_panel_users()}
        self.assertEqual(set(found), {"s1", "c1", "n1"})
        self.assertEqual(found["s1"].roles, ("admin", "student"))
        self.assertEqual(found["n1"].roles, ())
        self.assertEqual(
            (found["c1"].consultant_type, found["c1"].enabled, found["c1"].first_name),
            ("top_ranker", False, "سارا"),
        )

    def test_list_panel_users_follows_pages(self) -> None:
        pages = {0: [{"id": "a"}, {"id": "b"}], 2: [{"id": "c"}]}

        def student_page(path: str, kwargs: dict[str, Any]) -> FakeResponse:
            return FakeResponse(200, pages[kwargs["params"]["first"]])

        self.api.on("GET", "/roles/student/users", student_page)
        for role in ("consultant", "professor", "admin"):
            self.api.on("GET", f"/roles/{role}/users", FakeResponse(200, []))
        self.api.on("GET", "/users", FakeResponse(200, []))
        with patch.object(admin_client, "PAGE_SIZE", 2):
            subs = {u.sub for u in self.client_under_test.list_panel_users()}
        self.assertEqual(subs, {"a", "b", "c"})

    def test_http_errors_carry_the_status(self) -> None:
        self.api.on("GET", "/users/u1", FakeResponse(409, {}))
        with self.assertRaises(KeycloakError) as caught:
            self.client_under_test.set_enabled("u1", True)
        self.assertEqual(caught.exception.status, 409)

    def test_an_unreachable_server_is_a_keycloak_error_without_a_status(self) -> None:
        with (
            patch("requests.request", side_effect=requests.ConnectionError("down")),
            self.assertRaises(KeycloakError) as caught,
        ):
            self.client_under_test.set_enabled("u1", True)
        self.assertIsNone(caught.exception.status)
        self.assertTrue(re.search(r"GET /users/u1", str(caught.exception)))
