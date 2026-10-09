"""The service registry and the panel menus (SYS-PNL-01, 02, 05, 06, SYS-INT-01, 05)."""

from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from gradian_testing.covers import covers
from gradian_testing.tokens import service_token
from registry.models import Mode, ServiceEntry
from tests.helpers import seed
from tests.helpers.base import ApiTestCase

SERVICES = "/api/v1/panel/services"
COUNTS = {"student": 10, "consultant": 6, "professor": 6, "admin": 3}


def entry(key: str, **extra: Any) -> ServiceEntry:
    panel = key.split(".", 1)[0]
    values: dict[str, Any] = {
        "panel": panel,
        "title_fa": "عنوان",
        "title_en": "Title",
        "order": 1,
    }
    return ServiceEntry.objects.create(key=key, **{**values, **extra})


@covers("SYS-PNL-01", "SYS-PNL-02")
class PanelMenuTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        seed.load_services()

    def test_each_panel_gets_exactly_its_own_entries(self) -> None:
        for panel, count in COUNTS.items():
            with self.subTest(panel=panel):
                body = self.get_as(SERVICES, roles=(panel,), consultant_type="consultant").json()
                self.assertEqual(body["count"], count)
                self.assertEqual({e["key"].split(".")[0] for e in body["results"]}, {panel})

    def test_entries_come_in_display_order(self) -> None:
        results = self.get_as(SERVICES, roles=("student",)).json()["results"]
        self.assertEqual([e["order"] for e in results], list(range(1, 11)))
        self.assertEqual(results[0]["key"], "student.simulated-exam")
        self.assertEqual(results[-1]["key"], "student.experience-exchange")

    def test_a_person_with_no_panel_role_gets_the_student_menu(self) -> None:
        body = self.get_as(SERVICES, roles=()).json()
        self.assertEqual(body["count"], 10)

    def test_an_entry_has_what_the_panel_needs_to_draw_it(self) -> None:
        first = self.get_as(SERVICES, roles=("admin",)).json()["results"][0]
        self.assertEqual(
            set(first),
            {
                "key",
                "title_fa",
                "title_en",
                "description",
                "button_label",
                "icon",
                "order",
                "status",
                "mode",
                "url",
            },
        )
        self.assertEqual(first["title_fa"], "بانک آزمون و شبیه‌ساز")

    def test_the_menu_costs_the_same_number_of_queries_however_many_entries_there_are(self) -> None:
        def queries() -> int:
            with CaptureQueriesContext(connection) as captured:
                self.get_as(SERVICES, roles=("student",))
            return len(captured)

        self.get_as(SERVICES, roles=("student",))
        many = queries()
        ServiceEntry.objects.exclude(key="student.simulated-exam").delete()
        self.assertEqual(queries(), many)


@covers("SYS-PNL-05")
class UnavailableTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        entry("student.a", order=1)
        entry("student.b", order=2, target_url="https://b.example/app")
        entry("student.c", order=3, target_url="https://c.example/app", enabled=False)

    def results(self) -> dict[str, Any]:
        rows = self.get_as(SERVICES).json()["results"]
        return {row["key"]: row for row in rows}

    def test_no_target_url_means_unavailable_and_the_panel_still_loads(self) -> None:
        response = self.get_as(SERVICES)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.results()["student.a"]["status"], "unavailable")
        self.assertIsNone(self.results()["student.a"]["url"])

    def test_a_disabled_entry_is_unavailable_even_with_a_url(self) -> None:
        row = self.results()["student.c"]
        self.assertEqual(row["status"], "unavailable")
        self.assertIsNone(row["url"])

    def test_a_connected_entry_is_available_with_its_url(self) -> None:
        row = self.results()["student.b"]
        self.assertEqual((row["status"], row["url"]), ("available", "https://b.example/app"))

    def test_unavailable_entries_are_still_counted(self) -> None:
        self.assertEqual(self.get_as(SERVICES).json()["count"], 3)


@covers("SYS-PNL-06")
class SharedServiceTests(ApiTestCase):
    def test_editing_one_of_two_shared_entries_leaves_the_other_alone(self) -> None:
        seed.load_services()
        shared = "https://private-class.example"
        ServiceEntry.objects.filter(key="student.private-class").update(
            target_url=f"{shared}/student", mode=Mode.REDIRECT
        )
        professor = ServiceEntry.objects.get(key="professor.private-class")
        self.assertEqual((professor.target_url, professor.mode), ("", Mode.REDIRECT))

    def test_the_shared_services_exist_as_separate_rows_in_each_panel(self) -> None:
        seed.load_services()
        for title in (
            "Private class",
            "Online counseling sessions",
            "Konkur resources and notes hub",
        ):
            rows = ServiceEntry.objects.filter(title_en=title)
            with self.subTest(title=title):
                self.assertGreaterEqual(rows.count(), 2)
                self.assertEqual(rows.count(), len({row.panel for row in rows}))


@covers("SYS-INT-01", "SYS-INT-05")
class ConnectingTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        entry("student.a")
        entry("student.b", order=2)

    def test_setting_a_target_url_in_the_django_admin_makes_it_appear(self) -> None:
        User.objects.create_superuser("root", "root@gradian.test", "pw-for-tests-only")
        self.client.login(username="root", password="pw-for-tests-only")
        url = "/admin/registry/serviceentry/student.a/change/"
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        form = {
            "title_fa": "عنوان",
            "title_en": "Title",
            "description": "",
            "button_label": "ورود به سرویس",
            "icon": "",
            "order": 1,
            "target_url": "https://group3.example/app",
            "mode": "redirect",
            "enabled": "on",
            "owner_group": 3,
        }
        self.assertEqual(self.client.post(url, form).status_code, 302)
        self.client.logout()
        row = {r["key"]: r for r in self.get_as(SERVICES).json()["results"]}["student.a"]
        self.assertEqual(
            (row["status"], row["mode"], row["url"]),
            ("available", "redirect", "https://group3.example/app"),
        )

    def test_one_entry_can_be_embedded_and_another_redirected(self) -> None:
        ServiceEntry.objects.filter(key="student.a").update(
            target_url="https://a.example", mode=Mode.EMBED
        )
        ServiceEntry.objects.filter(key="student.b").update(
            target_url="https://b.example", mode=Mode.REDIRECT
        )
        modes = {r["key"]: r["mode"] for r in self.get_as(SERVICES).json()["results"]}
        self.assertEqual(modes, {"student.a": "embed", "student.b": "redirect"})

    def test_the_admin_refuses_a_target_that_is_not_a_web_address(self) -> None:
        bad = ServiceEntry(key="student.x", panel="student", title_fa="ا", title_en="x", order=3)
        bad.target_url = "ftp://files.example/app"
        with self.assertRaises(ValidationError):
            bad.full_clean()

    @override_settings(DEBUG=False)
    def test_the_key_must_belong_to_the_panel(self) -> None:
        bad = ServiceEntry(key="professor.x", panel="student", title_fa="ا", title_en="x", order=3)
        with self.assertRaises(ValidationError) as caught:
            bad.full_clean()
        self.assertIn("key", caught.exception.message_dict)


@covers("SYS-ACC-02")
class MenuAccessTests(ApiTestCase):
    def test_a_service_token_is_refused(self) -> None:
        response = self.client.get(SERVICES, **self.bearer(service_token()))
        self.assertEqual(response.status_code, 403)

    def test_no_token_is_401(self) -> None:
        self.assertEqual(self.client.get(SERVICES).status_code, 401)
