"""The default principal builder (DES-AUTH-02, DES-AUTH-03)."""

import uuid

from django.test import SimpleTestCase

from gradian_auth.errors import AmbiguousRoleError, IncompleteIdentityError
from gradian_auth.principals import ServicePrincipal, UserPrincipal, build_principal
from gradian_testing.covers import covers

SUB = "00000000-0000-4000-8000-000000000001"


def person(*roles: str, **claims: object) -> dict[str, object]:
    return {
        "sub": SUB,
        "preferred_username": "+989120000001",
        "email": "a@gradian.test",
        "given_name": "علی",
        "family_name": "رضایی",
        "realm_access": {"roles": ["offline_access", *roles]},
        **claims,
    }


@covers("SYS-AUTH-02", "SYS-AUTH-07")
class BuildPrincipalTests(SimpleTestCase):
    def test_a_person_has_an_identity_and_their_panel(self) -> None:
        principal = build_principal(person("professor"))
        assert isinstance(principal, UserPrincipal)
        self.assertEqual(principal.panel, "professor")
        self.assertEqual(principal.sub, SUB)
        self.assertEqual(principal.identity.sub, uuid.UUID(SUB))
        self.assertEqual(principal.identity.mobile, "09120000001")
        self.assertTrue(principal.is_authenticated)

    def test_no_panel_role_means_student(self) -> None:
        principal = build_principal(person())
        assert isinstance(principal, UserPrincipal)
        self.assertEqual(principal.panel, "student")

    def test_a_service_has_no_identity_and_names_its_client(self) -> None:
        principal = build_principal(
            {"sub": "svc-1", "azp": "group-3", "realm_access": {"roles": ["service"]}}
        )
        self.assertEqual(principal, ServicePrincipal(sub="svc-1", client_id="group-3"))
        self.assertTrue(principal.is_authenticated)

    def test_two_panel_roles_are_refused_and_logged(self) -> None:
        with (
            self.assertLogs("gradian.auth", level="WARNING") as logs,
            self.assertRaises(AmbiguousRoleError) as caught,
        ):
            build_principal(person("student", "admin"))
        self.assertEqual(caught.exception.details, {"roles": ["admin", "student"]})
        self.assertEqual(getattr(logs.records[0], "event", None), "role_failure")
        self.assertEqual(getattr(logs.records[0], "reason", None), "ambiguous_role")

    def test_the_service_role_together_with_a_panel_role_is_refused_and_logged(self) -> None:
        with (
            self.assertLogs("gradian.auth", level="WARNING") as logs,
            self.assertRaises(AmbiguousRoleError) as caught,
        ):
            build_principal(person("service", "admin"))
        self.assertEqual(caught.exception.details, {"roles": ["admin", "service"]})
        self.assertEqual(getattr(logs.records[0], "reason", None), "service_and_panel")

    def test_a_person_with_missing_claims_is_refused_naming_the_fields(self) -> None:
        claims = person("student")
        del claims["email"]
        with self.assertRaises(IncompleteIdentityError) as caught:
            build_principal(claims)
        self.assertEqual(caught.exception.details, {"fields": ["email"]})
