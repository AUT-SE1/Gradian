"""Needs the running stack: `make itest` starts it and runs these."""

from accounts.models import Profile
from gradian import env
from gradian_testing.covers import covers
from tests.helpers.base import IntegrationTestCase
from tests.helpers.keycloak import password_token

KINDS = [
    ("student", ""),
    ("consultant", "consultant"),
    ("consultant", "top_ranker"),
    ("professor", ""),
    ("admin", ""),
]


@covers("SYS-DATA-01", "SYS-AUTH-02")
class SeededSignInTests(IntegrationTestCase):
    """Every kind of seeded user signs in with the shared password and lands on their own panel.
    The generated fixture gives the profiles the ids Keycloak imported, so none is duplicated."""

    fixtures = ["profiles"]  # noqa: RUF012  # Django declares it as a plain list

    def sign_in(self, profile: Profile) -> dict[str, str]:
        token = password_token(profile.mobile, env.require("SEED_DEFAULT_PASSWORD"))
        response = self.client.get("/api/v1/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200, response.content)
        body: dict[str, str] = response.json()
        return body

    def test_a_seeded_user_of_each_kind_reaches_their_panel(self) -> None:
        profiles = Profile.objects.count()
        for role, consultant_type in KINDS:
            with self.subTest(role=role, consultant_type=consultant_type):
                profile = (
                    Profile.objects.filter(role=role, consultant_type=consultant_type)
                    .order_by("mobile")
                    .first()
                )
                assert profile is not None
                body = self.sign_in(profile)
                self.assertEqual(body["sub"], str(profile.sub))
                self.assertEqual(body["panel"], role)
                self.assertEqual(body["home_path"], f"/{role}")
                self.assertEqual(body["consultant_type"], consultant_type)
        self.assertEqual(Profile.objects.count(), profiles)
