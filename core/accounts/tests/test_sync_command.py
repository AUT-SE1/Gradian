"""`sync_keycloak_users` (DES-ID-04) against a stubbed Admin API."""

import uuid
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.keycloak import KeycloakError, KeycloakUser
from accounts.models import Profile
from tests.helpers.base import FakeIdentityAdmin
from tests.helpers.covers import covers

A = "00000000-0000-4000-8000-00000000000a"
B = "00000000-0000-4000-8000-00000000000b"


def kc_user(sub: str = A, **overrides: object) -> KeycloakUser:
    values: dict[str, object] = {
        "sub": sub,
        "username": "09120000001",
        "email": "a@gradian.test",
        "first_name": "علی",
        "last_name": "رضایی",
        "enabled": True,
        "roles": ("student",),
        "consultant_type": "",
    }
    values.update(overrides)
    return KeycloakUser(**values)  # type: ignore[arg-type]  # test helper builds from a dict


def profile(sub: str = A, **overrides: object) -> Profile:
    values: dict[str, object] = {
        "sub": uuid.UUID(sub),
        "mobile": "09120000001",
        "email": "a@gradian.test",
        "first_name": "علی",
        "last_name": "رضایی",
        "role": "student",
    }
    values.update(overrides)
    return Profile.objects.create(**values)


@covers("SYS-ID-02", "SYS-AUTH-08")
class SyncKeycloakUsersTests(TestCase):
    def setUp(self) -> None:
        self.idp = FakeIdentityAdmin()
        patcher = patch("accounts.keycloak.get_admin_client", return_value=self.idp)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_command(self, *args: str) -> str:
        out = StringIO()
        call_command("sync_keycloak_users", *args, stdout=out)
        return out.getvalue()

    def test_creates_missing_profiles(self) -> None:
        self.idp.users = [kc_user()]
        self.run_command()
        self.assertEqual(Profile.objects.get(sub=A).email, "a@gradian.test")

    def test_dry_run_reports_a_planted_mismatch_and_writes_nothing(self) -> None:
        profile()
        self.idp.users = [
            kc_user(email="changed@gradian.test"),
            kc_user(B, username="09120000002", email="b@gradian.test"),
        ]
        output = self.run_command("--dry-run")
        self.assertIn(f"update {A}: email", output)
        self.assertIn(f"create {B}", output)
        self.assertNotIn("changed@gradian.test", output)  # names fields, never values
        self.assertEqual(Profile.objects.get(sub=A).email, "a@gradian.test")
        self.assertFalse(Profile.objects.filter(sub=B).exists())

    def test_a_real_run_fixes_the_mismatch(self) -> None:
        profile()
        self.idp.users = [kc_user(email="changed@gradian.test", roles=("professor",))]
        self.run_command()
        fixed = Profile.objects.get(sub=A)
        self.assertEqual((fixed.email, fixed.role), ("changed@gradian.test", "professor"))

    def test_a_second_run_changes_nothing(self) -> None:
        self.idp.users = [kc_user()]
        self.run_command()
        output = self.run_command()
        self.assertIn("0 created, 0 updated, 0 deactivated", output)

    def test_users_deleted_in_keycloak_are_deactivated_not_deleted(self) -> None:
        profile()
        self.idp.users = []
        self.run_command()
        self.assertFalse(Profile.objects.get(sub=A).is_active)

    def test_disabled_keycloak_users_are_deactivated_and_reactivated(self) -> None:
        profile()
        self.idp.users = [kc_user(enabled=False)]
        self.run_command()
        self.assertFalse(Profile.objects.get(sub=A).is_active)
        self.idp.users = [kc_user(enabled=True)]
        self.run_command()
        self.assertTrue(Profile.objects.get(sub=A).is_active)

    def test_unusable_users_are_skipped_and_left_alone(self) -> None:
        profile()
        self.idp.users = [kc_user(roles=("student", "admin"))]
        output = self.run_command()
        self.assertIn("skip", output)
        self.assertTrue(Profile.objects.get(sub=A).is_active)

    def test_keycloak_failure_is_a_command_error(self) -> None:
        self.idp.fail_with = KeycloakError("down")
        with self.assertRaises(CommandError):
            self.run_command()
