from typing import Any

from django.test import SimpleTestCase

from accounts.claims import extract_roles
from accounts.errors import AmbiguousRoleError, RoleNotAssignedError
from accounts.roles import resolve_panel
from tests.helpers.covers import covers


@covers("SYS-AUTH-02", "SYS-AUTH-07")
class ResolvePanelTests(SimpleTestCase):
    def test_each_single_role_resolves_to_itself(self) -> None:
        for role in ("student", "consultant", "professor", "admin"):
            with self.subTest(role=role):
                self.assertEqual(resolve_panel([role]), role)

    def test_other_realm_roles_are_ignored(self) -> None:
        self.assertEqual(
            resolve_panel(["offline_access", "uma_authorization", "student"]), "student"
        )

    def test_no_panel_role_is_refused(self) -> None:
        with self.assertRaises(RoleNotAssignedError):
            resolve_panel(["offline_access"])

    def test_two_panel_roles_are_refused(self) -> None:
        with self.assertRaises(AmbiguousRoleError):
            resolve_panel(["student", "admin"])

    def test_repeated_role_is_not_ambiguous(self) -> None:
        self.assertEqual(resolve_panel(["student", "student"]), "student")


@covers("SYS-AUTH-07")
class ExtractRolesTests(SimpleTestCase):
    def test_malformed_claims_give_no_roles(self) -> None:
        cases: list[dict[str, Any]] = [
            {},
            {"realm_access": None},
            {"realm_access": {"roles": "admin"}},
        ]
        for claims in cases:
            with self.subTest(claims=claims):
                self.assertEqual(extract_roles(claims), [])
