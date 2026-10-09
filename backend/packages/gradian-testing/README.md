# gradian-testing

Test your views without a running Keycloak. It fakes Keycloak's signing keys and signs the tokens
your tests need, so you can check the 401, 403 and 200 cases of every endpoint. **Development
only: do not install it in a production image.**

| Module | Use it to |
| --- | --- |
| [`tokens`](#tokens) | `make_token`, `service_token`: sign exactly the token a test needs |
| [`cases`](#cases-and-drf) | `AuthTestCase` and `FakeKeycloakMixin`: fake the key fetch |
| [`drf`](#cases-and-drf) | `AuthAPITestCase` for Django REST Framework |
| [`fakes`](#fakes) | `FakeIdentityAdmin`: a recording stand-in for the Keycloak Admin API |
| [`settings`](#settings) | `KEYCLOAK_TEST_SETTINGS`: settings that make tests independent of `.env` |
| [`covers`](#covers) | `@covers("SYS-...")`: tie a test to a requirement |

## Install

    pip install /path/to/backend/packages/gradian-testing        # add [drf] for DRF services

It needs `gradian-auth` and `gradian-keycloak`; install all three in one command.

## A first test

```python
from gradian_testing.cases import AuthTestCase
from gradian_testing.tokens import make_token, service_token


class ExamViewTests(AuthTestCase):
    def test_no_token_is_401(self) -> None:
        self.assertEqual(self.client.get("/exams").status_code, 401)

    def test_a_student_may_list_exams(self) -> None:
        response = self.get_as("/exams", roles=("student",))
        self.assertEqual(response.status_code, 200)

    def test_a_professor_may_not(self) -> None:
        self.assertEqual(self.get_as("/exams", roles=("professor",)).status_code, 403)

    def test_a_service_token_is_not_a_person(self) -> None:
        response = self.client.get("/exams", **self.bearer(service_token()))
        self.assertEqual(response.status_code, 403)
```

## tokens

```python
make_token(
    roles=("professor",),
    sub="...uuid...",
    mobile="09120000001",
    email="a@x.test",
    first_name="علی",
    last_name="رضایی",
)
```

Every argument is optional. The defaults give a valid student for the service under test (issuer from
your settings, audience `KEYCLOAK_CLIENT_ID`). Break one thing at a time:

| Argument | Use |
| --- | --- |
| `audience="group-9"` or a list | wrong or several audiences |
| `issuer="http://evil.test/realms/gradian"` | wrong issuer |
| `issued_at=1_700_000_000` | expired |
| `expires_in=60` | lifetime in seconds |
| `key=OTHER_PRIVATE_KEY` | signed by a key Keycloak never published |
| `kid="unknown"` or `kid=None` | unknown or missing key id |
| `algorithm="none"` or `"HS256"` | forbidden algorithms |
| `omit=["email"]` | drop a claim |
| `extra={"azp": "group-3"}` | add or override claims |
| `consultant_type="top_ranker"` | needed for role `consultant` |

`service_token()` is a client-credentials token: the `service` role, no person.

## cases and drf

`AuthTestCase` (plain Django, no database) and `AuthAPITestCase` (`gradian_testing.drf`, DRF with a
database) both:

- replace the fetch of Keycloak's keys with the test key set (`self.jwks`; `self.fetch_jwks` is the
  mock, set `side_effect = KeycloakError("down")` to test an outage),
- clear the key cache before and after each test,
- apply `KEYCLOAK_TEST_SETTINGS`,
- give you `self.bearer(token)` and `self.get_as(path, **token_kwargs)`.

Already have a base class? Mix it in first: `class T(FakeKeycloakMixin, TestCase)`. To use other
Keycloak settings, add your own `@override_settings`, which wins.

## fakes

`FakeIdentityAdmin` records calls to the Admin API client (`updates`, `created`, `roles`, `enabled`,
`granted`) and fails every call when you set `fail_with = KeycloakError("down", 502)`. Install it with
`patch("gradian_keycloak.admin_client.get_admin_client", return_value=fake)`. Only Core needs this.

## settings

`KEYCLOAK_TEST_SETTINGS` is a dict of the required `KEYCLOAK_*` settings with test values.

## covers

`@covers("SYS-AUTH-02")` adds the Django test tag `req-SYS-AUTH-02`, so
`manage.py test --tag=req-SYS-AUTH-02` runs the tests for one requirement and
`scripts/req_coverage.py` counts them. Tag only requirements the test really verifies.

## Tests

    python packages/run_tests.py gradian_testing.tests
