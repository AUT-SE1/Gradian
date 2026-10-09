"""Needs the running stack: `make itest` starts it and runs these."""

from typing import Any

from accounts.models import Profile
from gradian import env
from gradian_testing.covers import covers
from registry.models import ServiceEntry
from tests.helpers.base import IntegrationTestCase
from tests.helpers.keycloak import password_token, service_token
from tests.helpers.repo import group_service_secret

KINDS = [
    ("student", "", 10),
    ("consultant", "consultant", 6),
    ("consultant", "top_ranker", 6),
    ("professor", "", 6),
    ("admin", "", 3),
]
SECTIONS = {
    "navbar",
    "hero",
    "statistics",
    "missions",
    "teachers",
    "rankers",
    "testimonials",
    "footer",
}


class RealPanelTests(IntegrationTestCase):
    fixtures = ["profiles", "services", "landing", "widgets"]  # noqa: RUF012

    def ask(self, path: str, token: str) -> Any:
        return self.client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")

    def token_of(self, role: str, consultant_type: str) -> tuple[Profile, str]:
        profile = (
            Profile.objects.filter(role=role, consultant_type=consultant_type)
            .order_by("mobile")
            .first()
        )
        assert profile is not None
        return profile, password_token(profile.mobile, env.require("SEED_DEFAULT_PASSWORD"))

    @covers("SYS-ACC-02", "SYS-PNL-01", "SYS-PNL-02")
    def test_a_seeded_user_of_each_kind_gets_their_own_menu_and_header(self) -> None:
        for role, consultant_type, count in KINDS:
            with self.subTest(role=role, consultant_type=consultant_type):
                profile, token = self.token_of(role, consultant_type)
                menu = self.ask("/api/v1/panel/services", token).json()
                self.assertEqual(menu["count"], count)
                self.assertEqual({e["key"].split(".")[0] for e in menu["results"]}, {role})
                header = self.ask("/api/v1/panel", token).json()["header"]
                self.assertEqual(header["full_name"], profile.full_name)

    @covers("SYS-ACC-02")
    def test_a_real_student_token_opens_the_dashboard_and_others_do_not(self) -> None:
        _, student = self.token_of("student", "")
        self.assertEqual(self.ask("/api/v1/student/dashboard", student).status_code, 200)
        for role, consultant_type, _ in KINDS[1:]:
            _, token = self.token_of(role, consultant_type)
            self.assertEqual(self.ask("/api/v1/student/dashboard", token).status_code, 403)

    @covers("SYS-DATA-06")
    def test_after_bootstrap_the_services_the_landing_and_the_widgets_are_there(self) -> None:
        self.assertEqual(ServiceEntry.objects.count(), 25)
        landing = self.client.get("/api/v1/landing").json()
        self.assertEqual(set(landing), SECTIONS)
        self.assertTrue(all(landing[name] for name in SECTIONS))
        _, token = self.token_of("student", "")
        dashboard = self.ask("/api/v1/student/dashboard", token).json()
        self.assertTrue(dashboard["study_streak"] and dashboard["experience_feed"])
        self.assertTrue(dashboard["welcome"]["message"].startswith("سلام"))

    @covers("SYS-INT-03", "SYS-ACC-02")
    def test_a_group_service_looks_up_people_with_its_own_credential(self) -> None:
        password = env.require("SEED_DEFAULT_PASSWORD")
        token = service_token("group-1", group_service_secret(1, password))
        profile, _ = self.token_of("professor", "")
        one = self.ask(f"/api/v1/internal/users/{profile.sub}", token)
        self.assertEqual(one.status_code, 200, one.content)
        self.assertEqual(one.json()["sub"], str(profile.sub))
        listed = self.ask("/api/v1/internal/users?role=professor", token).json()
        self.assertEqual(listed["count"], Profile.objects.filter(role="professor").count())
        self.assertEqual(self.ask("/api/v1/me", token).status_code, 403)

    def test_a_group_services_token_is_refused_by_a_person_only_endpoint(self) -> None:
        token = service_token(
            "group-2", group_service_secret(2, env.require("SEED_DEFAULT_PASSWORD"))
        )
        self.assertEqual(self.ask("/api/v1/panel/services", token).status_code, 403)
