"""Account administration (SYS-ADM-01 to SYS-ADM-04, DES-ADM-01 to DES-ADM-04)."""

from typing import Any

from accounts.models import Profile
from accounts.tests.test_internal_users import make_profile
from gradian_keycloak.errors import KeycloakError
from gradian_testing.covers import covers
from gradian_testing.tokens import make_token, service_token
from tests.helpers.base import ApiTestCase

USERS = "/api/v1/admin/users"
ADMIN_SUB = "00000000-0000-4000-8000-000000000001"


def body(**extra: Any) -> dict[str, Any]:
    return {
        "mobile": "09001230001",
        "email": "new.person@gradian.test",
        "first_name": "نوید",
        "last_name": "کاظمی",
        "password": "a-good-password",
        "role": "student",
        **extra,
    }


class AdminTestCase(ApiTestCase):
    def as_admin(self, method: str, path: str, data: Any = None, **token: Any) -> Any:
        client = getattr(self.client, method)
        extra = self.bearer(make_token(roles=("admin",), **token))
        return (
            client(path, data, format="json", **extra)
            if data is not None
            else client(path, **extra)
        )


@covers("SYS-ADM-01")
class CreateTests(AdminTestCase):
    def test_an_administrator_creates_an_account_of_each_role(self) -> None:
        cases: dict[str, dict[str, Any]] = {
            "student": {},
            "professor": {},
            "admin": {},
            "consultant": {"consultant_type": "top_ranker"},
        }
        for number, (role, extra) in enumerate(cases.items()):
            with self.subTest(role=role):
                response = self.as_admin(
                    "post",
                    USERS,
                    body(
                        role=role,
                        mobile=f"090012300{number:02d}",
                        email=f"person{number}@gradian.test",
                        **extra,
                    ),
                )
                self.assertEqual(response.status_code, 201, response.json())
                self.assertEqual(response.json()["role"], role)
                profile = Profile.objects.get(sub=response.json()["sub"])
                self.assertEqual(profile.consultant_type, extra.get("consultant_type", ""))
        created = {(u.role, u.consultant_type) for u in self.idp.created}
        self.assertEqual(
            created,
            {("student", ""), ("professor", ""), ("admin", ""), ("consultant", "top_ranker")},
        )

    def test_the_password_goes_to_keycloak_and_never_comes_back(self) -> None:
        response = self.as_admin("post", USERS, body())
        self.assertEqual(self.idp.created[0].password, "a-good-password")
        self.assertNotIn("password", response.json())
        self.assertNotIn("a-good-password", response.content.decode())

    def test_persian_digits_and_the_country_prefix_give_the_normal_number(self) -> None:
        response = self.as_admin("post", USERS, body(mobile="+۹۸۹۰۰۱۲۳۰۰۰۱"))
        self.assertEqual(response.json()["mobile"], "09001230001")

    def test_a_repeated_mobile_number_or_email_is_a_conflict(self) -> None:
        self.as_admin("post", USERS, body())
        for field, value in (("mobile", "09001230001"), ("email", "new.person@gradian.test")):
            with self.subTest(field=field):
                other = body(
                    **{"mobile": "09001239999", "email": "other.person@gradian.test", field: value}
                )
                response = self.as_admin("post", USERS, other)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["code"], "identity_conflict")
        self.assertEqual(len(self.idp.created), 1)

    def test_a_conflict_found_by_keycloak_is_a_conflict(self) -> None:
        self.idp.fail_with = KeycloakError("exists", 409)
        response = self.as_admin("post", USERS, body())
        self.assertEqual(
            (response.status_code, response.json()["code"]), (409, "identity_conflict")
        )

    def test_when_keycloak_fails_nothing_is_stored(self) -> None:
        self.as_admin("get", USERS)
        before = Profile.objects.count()
        self.idp.fail_with = KeycloakError("down", 503)
        response = self.as_admin("post", USERS, body())
        self.assertEqual(
            (response.status_code, response.json()["code"]),
            (502, "identity_provider_unavailable"),
        )
        self.assertEqual(Profile.objects.count(), before)

    def test_a_consultant_needs_a_type_and_nobody_else_may_have_one(self) -> None:
        missing = self.as_admin("post", USERS, body(role="consultant"))
        self.assertEqual(missing.status_code, 400)
        self.assertIn("consultant_type", missing.json()["details"])
        extra = self.as_admin("post", USERS, body(role="student", consultant_type="consultant"))
        self.assertEqual(extra.status_code, 400)
        self.assertEqual(self.idp.created, [])

    def test_bad_input_is_refused_with_the_fields_named(self) -> None:
        for field, value in (
            ("mobile", "12345"),
            ("email", "not-an-email"),
            ("password", "short"),
            ("role", "wizard"),
            ("first_name", "R2D2"),
        ):
            with self.subTest(field=field):
                response = self.as_admin("post", USERS, body(**{field: value}))
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["code"], "validation_error")
                self.assertIn(field, response.json()["details"])


@covers("SYS-ADM-02", "SYS-ADM-03")
class ChangeTests(AdminTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.person = make_profile(5)

    def patch(self, data: dict[str, Any], sub: Any = None) -> Any:
        return self.as_admin("patch", f"{USERS}/{sub or self.person.sub}", data)

    def test_a_new_role_becomes_the_only_panel_role_in_keycloak_and_in_the_cache(self) -> None:
        response = self.patch({"role": "professor"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["panel"], "professor")
        self.assertEqual(self.idp.roles, [(str(self.person.sub), "professor", "")])
        self.person.refresh_from_db()
        self.assertEqual(self.person.role, "professor")

    def test_the_next_token_of_that_person_gets_the_new_panel(self) -> None:
        self.patch({"role": "professor"})
        token = make_token(
            sub=self.person.sub,
            roles=("professor",),
            mobile=self.person.mobile,
            email=self.person.email,
        )
        response = self.client.get("/api/v1/me", **self.bearer(token))
        self.assertEqual((response.status_code, response.json()["panel"]), (200, "professor"))

    def test_becoming_a_consultant_needs_a_type_and_leaving_clears_it(self) -> None:
        self.assertEqual(self.patch({"role": "consultant"}).status_code, 400)
        self.assertEqual(
            self.patch({"role": "consultant", "consultant_type": "top_ranker"}).status_code, 200
        )
        self.person.refresh_from_db()
        self.assertEqual(self.person.consultant_type, "top_ranker")
        self.patch({"role": "student"})
        self.person.refresh_from_db()
        self.assertEqual((self.person.role, self.person.consultant_type), ("student", ""))

    def test_names_and_email_are_written_to_keycloak_first(self) -> None:
        response = self.patch({"first_name": "سارا", "email": "Sara@Gradian.Test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.idp.updates,
            [(str(self.person.sub), {"first_name": "سارا", "email": "sara@gradian.test"})],
        )

    def test_when_keycloak_fails_the_cache_does_not_change(self) -> None:
        self.idp.fail_with = KeycloakError("down", 503)
        response = self.patch({"role": "admin", "first_name": "سارا"})
        self.assertEqual(response.status_code, 502)
        self.person.refresh_from_db()
        self.assertEqual((self.person.role, self.person.first_name), ("student", "علی"))

    def test_an_unknown_account_is_not_found(self) -> None:
        response = self.patch({"first_name": "سارا"}, sub="00000000-0000-4000-8000-0000000000ee")
        self.assertEqual((response.status_code, response.json()["code"]), (404, "not_found"))

    def test_an_empty_change_is_refused(self) -> None:
        self.assertEqual(self.patch({}).status_code, 400)

    def test_the_mobile_number_cannot_be_changed(self) -> None:
        self.patch({"mobile": "09001239999", "first_name": "سارا"})
        self.person.refresh_from_db()
        self.assertEqual(self.person.mobile, "09000000005")

    def test_the_list_filters_by_role_status_and_text(self) -> None:
        make_profile(6, "professor")
        make_profile(7, "student", is_active=False)
        make_profile(8, "student", first_name="مریم")

        def found(query: str) -> set[str]:
            response = self.as_admin("get", f"{USERS}?{query}")
            self.assertEqual(response.status_code, 200)
            return {row["mobile"] for row in response.json()["results"]}

        self.assertEqual(found("role=professor"), {"09000000006"})
        self.assertEqual(found("role=student&is_active=false"), {"09000000007"})
        self.assertIn("09000000005", found("role=student&is_active=true"))
        self.assertNotIn("09000000007", found("is_active=true"))
        self.assertEqual(found("q=مریم"), {"09000000008"})
        self.assertEqual(found("q=user6@"), {"09000000006"})
        self.assertEqual(found("q=0000005"), {"09000000005"})

    def test_the_list_is_paginated_and_an_unknown_role_is_refused(self) -> None:
        for number in range(6, 10):
            make_profile(number)
        page = self.as_admin("get", f"{USERS}?limit=2&offset=1").json()
        self.assertEqual((len(page["results"]), page["count"]), (2, 6))
        self.assertEqual(self.as_admin("get", f"{USERS}?role=wizard").status_code, 400)

    def test_one_account_can_be_read(self) -> None:
        response = self.as_admin("get", f"{USERS}/{self.person.sub}")
        self.assertEqual(response.json()["mobile"], "09000000005")

    def test_disabling_blocks_the_person_and_enabling_restores_them(self) -> None:
        token = make_token(sub=self.person.sub, mobile=self.person.mobile, email=self.person.email)

        def me() -> Any:
            return self.client.get("/api/v1/me", **self.bearer(token))

        self.assertEqual(me().status_code, 200)
        self.patch({"is_active": False})
        self.assertEqual(self.idp.enabled, [(str(self.person.sub), False)])
        blocked = me()
        self.assertEqual((blocked.status_code, blocked.json()["code"]), (403, "account_disabled"))
        self.patch({"is_active": True})
        self.assertEqual(me().status_code, 200)


@covers("SYS-ADM-04", "SYS-ACC-02")
class AccessTests(AdminTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.person = make_profile(5)

    def calls(self) -> dict[str, Any]:
        sub = self.person.sub
        return {
            "list": ("get", USERS, None),
            "create": ("post", USERS, body()),
            "read": ("get", f"{USERS}/{sub}", None),
            "change": ("patch", f"{USERS}/{sub}", {"first_name": "سارا"}),
        }

    def test_everyone_but_an_administrator_is_refused_on_every_endpoint(self) -> None:
        callers: dict[str, tuple[str | None, int]] = {
            "anonymous": (None, 401),
            "student": (make_token(roles=("student",)), 403),
            "consultant": (make_token(roles=("consultant",), consultant_type="consultant"), 403),
            "professor": (make_token(roles=("professor",)), 403),
            "service": (service_token(), 403),
        }
        for caller, (token, expected) in callers.items():
            for name, (method, path, data) in self.calls().items():
                with self.subTest(caller=caller, call=name):
                    extra = self.bearer(token) if token else {}
                    client = getattr(self.client, method)
                    response = (
                        client(path, data, format="json", **extra)
                        if data is not None
                        else client(path, **extra)
                    )
                    self.assertEqual(response.status_code, expected)
        self.assertEqual(self.idp.created + self.idp.updates, [])

    def test_an_administrator_cannot_change_their_own_role_type_or_status(self) -> None:
        self.as_admin("get", USERS)
        for change in (
            {"role": "student"},
            {"is_active": False},
            {"consultant_type": "consultant"},
        ):
            with self.subTest(change=change):
                response = self.as_admin("patch", f"{USERS}/{ADMIN_SUB}", change)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["code"], "self_modification_forbidden")
        self.assertEqual(self.idp.roles + self.idp.enabled, [])

    def test_an_administrator_may_still_change_their_own_name(self) -> None:
        self.as_admin("get", USERS)
        response = self.as_admin("patch", f"{USERS}/{ADMIN_SUB}", {"first_name": "سارا"})
        self.assertEqual(response.status_code, 200)
