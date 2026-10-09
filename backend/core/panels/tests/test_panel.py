"""Landing, panel header, student dashboard and notifications."""

from datetime import date
from typing import Any
from unittest.mock import patch

from django.test import override_settings

from accounts.models import Profile
from gradian_testing.covers import covers
from gradian_testing.tokens import service_token
from panels.models import ContentBlock, Notification
from tests.helpers import seed
from tests.helpers.base import ApiTestCase

LANDING = "/api/v1/landing"
PANEL = "/api/v1/panel"
DASHBOARD = "/api/v1/student/dashboard"
NOTIFICATIONS = "/api/v1/notifications"
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


@covers("SYS-PNL-04", "SYS-ACC-01")
class LandingTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        seed.load_blocks()

    def test_anyone_can_read_it_without_signing_in(self) -> None:
        response = self.client.get(LANDING)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), SECTIONS)

    def test_every_section_has_content(self) -> None:
        body = self.client.get(LANDING).json()
        for name in SECTIONS:
            with self.subTest(section=name):
                self.assertTrue(body[name])
        self.assertEqual(len(body["statistics"]), 4)
        self.assertEqual(len(body["teachers"]), 4)
        self.assertEqual(len(body["rankers"]), 4)
        self.assertEqual(len(body["testimonials"]), 4)

    def test_changing_the_stored_content_changes_the_answer_without_a_code_change(self) -> None:
        block = ContentBlock.objects.get(key="landing.hero")
        block.data = {**block.data, "title": "عنوان تازه"}
        block.save()
        self.assertEqual(self.client.get(LANDING).json()["hero"]["title"], "عنوان تازه")

    def test_a_deleted_section_is_null_and_the_rest_still_load(self) -> None:
        ContentBlock.objects.filter(key="landing.footer").delete()
        body = self.client.get(LANDING).json()
        self.assertIsNone(body["footer"])
        self.assertIsNotNone(body["hero"])

    def test_a_token_is_not_needed_and_a_bad_one_is_ignored(self) -> None:
        self.assertEqual(self.client.get(LANDING, **self.bearer("garbage")).status_code, 200)

    @covers("SYS-NFR-01")
    @override_settings(PUBLIC_RATE_LIMIT="2/min")
    def test_it_is_rate_limited_like_every_public_endpoint(self) -> None:
        codes = [self.client.get(LANDING).status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])


@covers("SYS-ID-06", "SYS-PNL-03")
class PanelHeaderTests(ApiTestCase):
    def test_a_student_sees_the_full_name_and_the_field_of_study(self) -> None:
        self.get_as(PANEL, roles=("student",))
        Profile.objects.update(field_of_study="mathematics")
        body = self.get_as(PANEL, roles=("student",)).json()
        self.assertEqual(body["panel"], "student")
        self.assertEqual(body["home_path"], "/student")
        self.assertEqual(body["header"]["full_name"], "علی رضایی")
        self.assertEqual(body["header"]["field_of_study"], "mathematics")
        self.assertEqual(body["header"]["field_of_study_label"], "ریاضی و فیزیک")

    def test_a_student_who_has_not_chosen_a_field_has_none_to_show(self) -> None:
        body = self.get_as(PANEL, roles=("student",)).json()
        self.assertEqual(body["header"]["field_of_study"], "")
        self.assertIsNone(body["header"]["field_of_study_label"])

    def test_other_panels_show_the_name_but_no_field_of_study(self) -> None:
        for role in ("consultant", "professor", "admin"):
            with self.subTest(role=role):
                body = self.get_as(PANEL, roles=(role,), consultant_type="top_ranker").json()
                self.assertEqual(body["header"]["full_name"], "علی رضایی")
                self.assertIsNone(body["header"]["field_of_study"])
                self.assertIsNone(body["header"]["field_of_study_label"])

    def test_a_consultant_header_says_which_kind(self) -> None:
        body = self.get_as(PANEL, roles=("consultant",), consultant_type="top_ranker").json()
        self.assertEqual(body["header"]["consultant_type"], "top_ranker")
        self.assertIsNone(self.get_as(PANEL, roles=("admin",)).json()["header"]["consultant_type"])

    def test_the_sidebar_countdown_follows_the_configured_date_and_the_clock(self) -> None:
        with (
            override_settings(KONKUR_DATE=date(2027, 6, 25)),
            patch("panels.views.timezone.localdate", return_value=date(2027, 6, 5)),
        ):
            countdown = self.get_as(PANEL).json()["countdown"]
        self.assertEqual(countdown["days_remaining"], 20)
        self.assertEqual(countdown["state"], "upcoming")
        self.assertEqual(countdown["label"], "۲۰ روز تا کنکور")

    def test_a_service_is_not_a_panel_user(self) -> None:
        self.assertEqual(self.client.get(PANEL, **self.bearer(service_token())).status_code, 403)


@covers("SYS-PNL-03")
class DashboardTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        seed.load_blocks()

    def test_the_student_gets_every_widget(self) -> None:
        body = self.get_as(DASHBOARD).json()
        self.assertEqual(set(body), {"welcome", "countdown", "study_streak", "experience_feed"})
        self.assertEqual(len(body["study_streak"]["week"]), 7)
        self.assertEqual(len(body["experience_feed"]), 3)

    def test_the_welcome_message_is_for_this_student(self) -> None:
        message = self.get_as(DASHBOARD, first_name="سارا", last_name="کریمی").json()["welcome"]
        self.assertEqual(message["message"], "سلام سارا، به گرادیان خوش آمدی!")

    def test_the_full_name_placeholder_is_filled_too(self) -> None:
        block = ContentBlock.objects.get(key="widget.welcome")
        block.data = {**block.data, "message": "{full_name} عزیز"}
        block.save()
        self.assertEqual(self.get_as(DASHBOARD).json()["welcome"]["message"], "علی رضایی عزیز")

    def test_missing_widget_content_is_null_not_an_error(self) -> None:
        ContentBlock.objects.filter(key="widget.study_streak").delete()
        response = self.get_as(DASHBOARD)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["study_streak"])

    def test_only_a_student_may_open_it(self) -> None:
        for role in ("consultant", "professor", "admin"):
            with self.subTest(role=role):
                self.assertEqual(
                    self.get_as(DASHBOARD, roles=(role,), consultant_type="consultant").status_code,
                    403,
                )


@covers("SYS-PNL-03")
class NotificationTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mine = self.profile()

    def profile(self) -> Profile:
        self.get_as(NOTIFICATIONS)
        return Profile.objects.get()

    def notify(self, title: str, profile: Profile | None = None, **extra: Any) -> Notification:
        return Notification.objects.create(profile=profile or self.mine, title=title, **extra)

    def test_it_is_empty_by_default_with_a_zero_count(self) -> None:
        body = self.get_as(NOTIFICATIONS).json()
        self.assertEqual(
            body, {"unread_count": 0, "count": 0, "next": None, "previous": None, "results": []}
        )

    def test_it_lists_newest_first_and_counts_the_unread(self) -> None:
        from django.utils import timezone

        self.notify("old", read_at=timezone.now())
        self.notify("middle")
        self.notify("new")
        body = self.get_as(NOTIFICATIONS).json()
        self.assertEqual([n["title"] for n in body["results"]], ["new", "middle", "old"])
        self.assertEqual(body["unread_count"], 2)
        self.assertEqual([n["is_read"] for n in body["results"]], [False, False, True])
        self.assertEqual(set(body["results"][0]), {"id", "title", "body", "created_at", "is_read"})

    def test_the_unread_count_covers_every_page_not_only_the_one_shown(self) -> None:
        for number in range(5):
            self.notify(f"n{number}")
        body = self.get_as(f"{NOTIFICATIONS}?limit=2").json()
        self.assertEqual((len(body["results"]), body["count"], body["unread_count"]), (2, 5, 5))

    def test_nobody_sees_another_persons_notifications(self) -> None:
        stranger = Profile.objects.create(
            sub="00000000-0000-4000-8000-0000000000ff",
            mobile="09120000099",
            email="other@gradian.test",
            first_name="نیما",
            last_name="رحیمی",
            role="student",
        )
        self.notify("secret", stranger)
        self.assertEqual(self.get_as(NOTIFICATIONS).json()["count"], 0)

    def test_a_service_token_is_refused(self) -> None:
        self.assertEqual(
            self.client.get(NOTIFICATIONS, **self.bearer(service_token())).status_code, 403
        )
