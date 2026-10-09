"""What group services may ask for (DES-REG-07, SYS-INT-03)."""

import uuid
from typing import Any

from accounts.models import Profile
from tests.helpers.base import ApiTestCase
from tests.helpers.covers import covers
from tests.helpers.tokens import make_token, service_token

USERS = "/api/v1/internal/users"
ROLES = {
    "anonymous": 401,
    "student": 403,
    "consultant": 403,
    "professor": 403,
    "admin": 403,
    "service": 200,
}


def make_profile(number: int, role: str = "student", **extra: Any) -> Profile:
    return Profile.objects.create(
        **{
            "sub": uuid.UUID(int=number),
            "mobile": f"0900000{number:04d}",
            "email": f"user{number}@gradian.test",
            "first_name": "علی",
            "last_name": f"نمونه{number}",
            "role": role,
            **extra,
        }
    )


@covers("SYS-INT-03")
class InternalUsersTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.student = make_profile(1)
        make_profile(2, "professor")
        make_profile(3, "consultant", consultant_type="top_ranker")

    def ask(self, path: str, **token: Any) -> Any:
        return self.client.get(path, **self.bearer(service_token(**token)))

    def test_a_service_looks_up_one_person_by_id(self) -> None:
        body = self.ask(f"{USERS}/{self.student.sub}").json()
        self.assertEqual(body["sub"], str(self.student.sub))
        self.assertEqual(body["full_name"], self.student.full_name)

    def test_an_unknown_or_malformed_id_is_not_found(self) -> None:
        self.assertEqual(self.ask(f"{USERS}/{uuid.uuid4()}").json()["code"], "not_found")
        self.assertEqual(self.ask(f"{USERS}/not-a-uuid").status_code, 404)

    def test_a_service_lists_people_and_filters_by_role(self) -> None:
        self.assertEqual(self.ask(USERS).json()["count"], 3)
        self.assertEqual(self.ask(f"{USERS}?role=professor").json()["count"], 1)
        self.assertEqual(self.ask(f"{USERS}?role=wizard").status_code, 400)

    def test_only_a_service_may_ask(self) -> None:
        tokens: dict[str, dict[str, Any]] = {
            "student": {
                "roles": ("student",),
                "sub": uuid.UUID(int=91),
                "mobile": "09000009091",
                "email": "a1@gradian.test",
            },
            "consultant": {
                "roles": ("consultant",),
                "consultant_type": "consultant",
                "sub": uuid.UUID(int=92),
                "mobile": "09000009092",
                "email": "a2@gradian.test",
            },
            "professor": {
                "roles": ("professor",),
                "sub": uuid.UUID(int=93),
                "mobile": "09000009093",
                "email": "a3@gradian.test",
            },
            "admin": {
                "roles": ("admin",),
                "sub": uuid.UUID(int=94),
                "mobile": "09000009094",
                "email": "a4@gradian.test",
            },
        }
        for path in (USERS, f"{USERS}/{self.student.sub}"):
            for who, expected in ROLES.items():
                with self.subTest(path=path, who=who):
                    if who == "anonymous":
                        response = self.client.get(path)
                    elif who == "service":
                        response = self.ask(path)
                    else:
                        response = self.client.get(path, **self.bearer(make_token(**tokens[who])))
                    self.assertEqual(response.status_code, expected)
