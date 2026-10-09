"""AC-ACCESS: who can do what, every cell and the three extra cases (test plan section 4)."""

import uuid
from typing import Any

from accounts.models import Profile
from accounts.tests.test_internal_users import make_profile
from gradian_testing.covers import covers
from gradian_testing.tokens import make_token, service_token
from tests.helpers import seed
from tests.helpers.base import ApiTestCase

CALLERS = ("anonymous", "student", "consultant", "professor", "admin", "service")

PROFILE_ID = uuid.UUID(int=0xA1)

# One status per caller, in the order of CALLERS.
MATRIX: dict[str, tuple[str, tuple[int, ...]]] = {
    "view landing content": ("/api/v1/landing", (200, 200, 200, 200, 200, 200)),
    "view own identity and panel": ("/api/v1/me", (401, 200, 200, 200, 200, 403)),
    "list own panel's services": ("/api/v1/panel/services", (401, 200, 200, 200, 200, 403)),
    "view student dashboard": ("/api/v1/student/dashboard", (401, 200, 403, 403, 403, 403)),
    "panel header": ("/api/v1/panel", (401, 200, 200, 200, 200, 403)),
    "notifications": ("/api/v1/notifications", (401, 200, 200, 200, 200, 403)),
    "list users (service endpoint)": ("/api/v1/internal/users", (401, 403, 403, 403, 403, 200)),
    "look up a user by id": (
        f"/api/v1/internal/users/{PROFILE_ID}",
        (401, 403, 403, 403, 403, 200),
    ),
    "list accounts (admin endpoint)": ("/api/v1/admin/users", (401, 403, 403, 403, 200, 403)),
}
PANEL_PATHS = ("/api/v1/me", "/api/v1/panel", "/api/v1/panel/services", "/api/v1/notifications")
PANEL_ENTRIES = {"student": 10, "consultant": 6, "professor": 6, "admin": 3}


def token_for(caller: str) -> str | None:
    if caller == "anonymous":
        return None
    if caller == "service":
        return service_token()
    return make_token(roles=(caller,), consultant_type="consultant")


@covers("SYS-ACC-01", "SYS-ACC-02")
class AccessMatrixTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        seed.load_services()
        seed.load_blocks()
        make_profile(0xA1)  # its id is PROFILE_ID

    def ask(self, path: str, caller: str) -> Any:
        token = token_for(caller)
        return self.client.get(path, **(self.bearer(token) if token else {}))

    def test_every_cell_of_the_matrix(self) -> None:
        for capability, (path, expected) in MATRIX.items():
            for caller, status in zip(CALLERS, expected, strict=True):
                with self.subTest(capability=capability, caller=caller):
                    self.assertEqual(self.ask(path, caller).status_code, status)

    def test_every_panel_lists_its_own_number_of_services(self) -> None:
        for panel, count in PANEL_ENTRIES.items():
            with self.subTest(panel=panel):
                response = self.ask("/api/v1/panel/services", panel)
                self.assertEqual(response.json()["count"], count)

    def test_an_error_is_never_a_page_or_a_stack_trace(self) -> None:
        for capability, (path, expected) in MATRIX.items():
            for caller, status in zip(CALLERS, expected, strict=True):
                if status >= 400:
                    with self.subTest(capability=capability, caller=caller):
                        body = self.ask(path, caller).json()
                        self.assertEqual(set(body), {"code", "message", "details"})


@covers("SYS-ACC-02", "SYS-AUTH-07", "SYS-AUTH-08")
class ExtraCasesTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        seed.load_services()

    def test_a_person_with_no_panel_role_is_a_student(self) -> None:
        for path in ("/api/v1/me", "/api/v1/panel/services", "/api/v1/student/dashboard"):
            with self.subTest(path=path):
                response = self.get_as(path, roles=())
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_as("/api/v1/panel/services", roles=()).json()["count"], 10)

    def test_a_person_with_two_panel_roles_cannot_enter_any_panel(self) -> None:
        for path in (
            "/api/v1/me",
            "/api/v1/panel",
            "/api/v1/panel/services",
            "/api/v1/notifications",
        ):
            with self.subTest(path=path):
                response = self.get_as(path, roles=("student", "admin"))
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["code"], "ambiguous_role")

    def test_a_disabled_profile_cannot_use_any_endpoint(self) -> None:
        self.get_as("/api/v1/me")
        Profile.objects.update(is_active=False)
        for path in (
            "/api/v1/me",
            "/api/v1/panel",
            "/api/v1/panel/services",
            "/api/v1/notifications",
        ):
            with self.subTest(path=path):
                response = self.get_as(path)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["code"], "account_disabled")
