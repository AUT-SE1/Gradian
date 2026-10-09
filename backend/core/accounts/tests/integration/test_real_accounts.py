"""Needs the running stack: `make itest` starts it and runs these.

Every test that changes Keycloak creates a temporary user in the reserved mobile range and removes
it again; the seeded users are never touched (test plan 2.3).
"""

from typing import Any

import requests

from accounts.models import Profile
from gradian import env
from gradian_keycloak import admin_client
from gradian_testing.covers import covers
from tests.helpers.base import IntegrationTestCase
from tests.helpers.keycloak import (
    TemporaryUser,
    password_token,
    remove_user,
    temporary_user,
    unique_mobile,
)

USERS = "/api/v1/admin/users"


class RealAccountTests(IntegrationTestCase):
    fixtures = ["profiles"]  # noqa: RUF012

    def call(self, method: str, path: str, token: str, data: Any = None) -> Any:
        extra = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        client = getattr(self.client, method)
        return (
            client(path, data, format="json", **extra)
            if data is not None
            else client(path, **extra)
        )

    def admin_token(self) -> str:
        admin = Profile.objects.filter(role="admin").order_by("mobile").first()
        assert admin is not None
        return password_token(admin.mobile, env.require("SEED_DEFAULT_PASSWORD"))

    def sign_in(self, user: TemporaryUser) -> str:
        return password_token(user.mobile, user.password)

    @covers("SYS-ADM-01", "SYS-ADM-02")
    def test_an_administrator_creates_an_account_that_signs_in_and_changes_its_role(self) -> None:
        mobile = unique_mobile()
        admin = self.admin_token()
        created = self.call(
            "post",
            USERS,
            admin,
            {
                "mobile": mobile,
                "email": f"made.{mobile}@gradian.test",
                "first_name": "نوید",
                "last_name": "کاظمی",
                "password": "Created-Pass-1",
                "role": "student",
            },
        )
        self.assertEqual(created.status_code, 201, created.content)
        sub = created.json()["sub"]
        try:
            token = password_token(mobile, "Created-Pass-1")
            self.assertEqual(self.call("get", "/api/v1/me", token).json()["panel"], "student")

            changed = self.call("patch", f"{USERS}/{sub}", admin, {"role": "professor"})
            self.assertEqual(changed.status_code, 200, changed.content)
            fresh = password_token(mobile, "Created-Pass-1")
            self.assertEqual(self.call("get", "/api/v1/me", fresh).json()["panel"], "professor")
        finally:
            remove_user(sub)

    @covers("SYS-AUTH-08")
    def test_a_disabled_account_cannot_sign_in_and_enabling_restores_it(self) -> None:
        with temporary_user() as user:
            self.assertTrue(self.sign_in(user))
            admin_client.get_admin_client().set_enabled(user.sub, False)
            with self.assertRaises(requests.HTTPError):
                self.sign_in(user)
            admin_client.get_admin_client().set_enabled(user.sub, True)
            self.assertTrue(self.sign_in(user))

    @covers("SYS-AUTH-08")
    def test_a_token_issued_before_the_account_was_disabled_is_refused_once_core_knows(
        self,
    ) -> None:
        with temporary_user() as user:
            token = self.sign_in(user)
            self.assertEqual(self.call("get", "/api/v1/me", token).status_code, 200)
            admin = self.admin_token()
            self.call("patch", f"{USERS}/{user.sub}", admin, {"is_active": False})
            blocked = self.call("get", "/api/v1/me", token)
            self.assertEqual(
                (blocked.status_code, blocked.json()["code"]), (403, "account_disabled")
            )

    @covers("SYS-ID-02")
    def test_a_change_made_in_keycloak_shows_in_the_next_token_and_the_cache(self) -> None:
        with temporary_user() as user:
            first = self.call("get", "/api/v1/me", self.sign_in(user)).json()
            self.assertEqual(first["email"], user.email)
            new_email = f"changed.{user.mobile}@gradian.test"
            admin_client.get_admin_client().update_user(user.sub, {"email": new_email})
            second = self.call("get", "/api/v1/me", self.sign_in(user)).json()
            self.assertEqual(second["email"], new_email)
            self.assertEqual(Profile.objects.get(sub=user.sub).email, new_email)

    @covers("SYS-AUTH-07")
    def test_a_person_with_no_panel_role_is_a_student_and_is_granted_the_role(self) -> None:
        with temporary_user(role="student") as user:
            admin_client.get_admin_client().set_panel_role(user.sub, "student", "")
            self.assertEqual(
                self.call("get", "/api/v1/me", self.sign_in(user)).json()["panel"], "student"
            )
