# Gradian Core Service - Test Plan

Draft · 2026-10-04

Part of a four-document set: [01 Requirements](01-requirements.md) · [02 Design](02-design.md) · [03 Decision log](03-decisions.md) · **04 Test plan** (this document).

This plan says how each requirement in 01 is verified and how the tests are set up and run. It follows DEC-13: Django's own test runner, with one tag, `integration`, separating tests that need the running stack.

## 1. Test levels

| Level | Name | Needs the stack | Runs with | What it proves |
| --- | --- | --- | --- | --- |
| UNIT | Unit | No | `make test` | Pure logic in isolation: mobile normalizer, role resolver, claim mapper, countdown, seed generator |
| API | API (fast) | No | `make test` | Endpoints, status codes, permissions, error shape and identity sync, with Keycloak replaced by a fake key set and a stubbed Admin API |
| INTEG | Integration | Yes | `make itest` | The real realm and real tokens work end to end: claims, role mapping, seeded users, lockout, group-service checks |
| STATIC | Static checks | No | `make check`, CI | Lint, formatting, missing migrations, OpenAPI validity and compatibility, secret scan |
| MANUAL | Acceptance checklist | Yes | A person, on a clean machine | Setup from scratch, role walkthroughs, the commands themselves |
| PERF | Performance | Yes | Occasional manual run | Latency under the load in SYS-NFR-02 |
| EXT | Relied on | No | Review of the configuration, and the MANUAL checklist | Behaviour that an external component (Keycloak, Django) implements and documents. We own only how it is configured, and we do not write an automated test for it (DEC-17) |

**Relying on an external component.** A test that only restates our own configuration, such as asserting the value of a setting or the contents of the realm file, duplicates the decision it checks and fails whenever that decision legitimately changes. For behaviour that Keycloak or Django provides and tests itself, the traceability tables below mark the requirement `EXT`, name the component, and leave confirmation to the MANUAL checklist, which runs once on a clean machine. A requirement marked `EXT` counts as covered in `scripts/req_coverage.py`, which lists it separately so the reliance stays visible. Code we write on top of the component, such as claim validation or error messages, is still tested.

## 2. How the tests are set up and run

### 2.1 Layout

```
core/<app>/tests/
    test_*.py                  # fast tests: UNIT and API
    integration/test_*.py      # INTEG, every class tagged "integration"
core/tests/helpers/
    base.py                    # ApiTestCase: fake key set and a stubbed Admin API client
    keycloak.py                # real-token helper and temporary-user helper
packages/<package>/src/<module>/tests/
    test_*.py                  # tests of the shared packages, run by `make test`
scripts/tests/                 # tests for the seed generator and check_service
tests/perf/                    # load-test script (PERF)
```

### 2.2 Fast tests (UNIT and API)

- API tests extend `APITestCase` through a small base class that installs a fake key set: a throwaway RSA key pair is generated when the tests start, and the code that fetches Keycloak's keys is patched to return the public half.
- `make_token(sub=..., roles=[...], **claims)` (from `gradian_testing.tokens`) signs a token with that key. Tests build exactly the token they need: wrong issuer, wrong audience, expired, `alg: none`, missing claim, extra roles.
- The Keycloak Admin API client is replaced with a stub that records calls and can be told to fail. This covers write-through (DES-ID-05) and the sync command without a real Keycloak.
- Fast tests create their own small data. The seed tests build the seed in memory from `seed/` and test that; no generated file is needed.
- Django creates and destroys its own test database, so nothing here touches the local development database.

### 2.3 Integration tests (INTEG)

- Every class is decorated `@tag("integration")` and extends a base class that, in `setUpClass`, checks that Keycloak and the realm are reachable. If not, it fails with an instruction to run `make start`; it does not skip silently, because a silent skip hides a broken setup.
- Tokens come from the test-only client `gradian-test` (DES-IDP-09) using a seeded user's mobile number and `SEED_DEFAULT_PASSWORD`. No browser is involved.
- The Django test database is separate from the development one, so each class loads the generated fixture itself (`fixtures = [...]`, written by `make seed`). Because user IDs are fixed (DEC-12), those profiles match the users already in Keycloak.
- Keycloak is **shared** between tests and is not reset between them. Tests that change Keycloak state (change an email, trigger a lockout, disable a user) create a temporary user through the Admin API with a unique mobile number and delete it afterwards. They never modify seeded users.

### 2.4 Commands and CI

| Command | Runs |
| --- | --- |
| `make test` | `manage.py test --exclude-tag=integration`, plus `scripts/tests` (part of `make check`) |
| `make itest` | Starts the system if needed, then `manage.py test --tag=integration` against it |
| `make check` | `lint` (linter, formatter check, `.env.example`, `makemigrations --check`, requirement coverage), `typecheck`, `test` and `schema` |
| `make check-service URL=...` | The group-service conformance check |

CI runs `check` on every push. A second job runs `itest`. Running tests for one requirement is possible through its tag: `manage.py test --tag=req-SYS-AUTH-02`.

### 2.5 Linking tests to requirements

A helper decorator `@covers("SYS-AUTH-02", "SYS-AUTH-07")` adds the tags `req-SYS-AUTH-02` and so on to a test. A script `scripts/req_coverage.py` reads the requirement IDs from `01-requirements.md`, collects the tags from the test code and the `EXT` marks from section 3 below, and lists any requirement with neither a test nor an `EXT` mark, and separately those that rely only on an external implementation (SYS-NFR-08). It runs in `make lint` and in CI.

## 3. Traceability: requirement to verification

Levels are those in section 1. A requirement may be checked at several levels.

### Authentication and access

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-AUTH-01 | EXT, MANUAL | Keycloak authenticates the mobile number and password. Manual: a seeded user of each role signs in, a wrong password is refused, the login page shows the expected fields |
| SYS-AUTH-02 | UNIT, API, INTEG | Role resolver for each single role and for a top-ranker; `/me` returns the right `panel` and `home_path`; a seeded user of each role gets the AC-ROUTE panel from a real token |
| SYS-AUTH-03 | INTEG | A token from one sign-in is accepted by the Core Service and by the reference group service |
| SYS-AUTH-04 | EXT, MANUAL | Keycloak implements remember me and the session lifetimes. Manual: a remembered session survives closing the browser, a normal one does not |
| SYS-AUTH-05 | EXT, MANUAL | Keycloak's brute-force protection locks an account after repeated failures and gives one error for every kind of failure. Manual: lock a temporary user, and compare the error for an unknown number |
| SYS-AUTH-06 | API, MANUAL | `/auth/config` returns the end-session and landing URLs; the logout icon ends the session and returns to the landing page |
| SYS-AUTH-07 | UNIT, API | No panel role gives the student panel and a one-time grant of the role in Keycloak; two panel roles give 403 `ambiguous_role`; `offline_access` is ignored |
| SYS-AUTH-08 | API, INTEG | An inactive profile gets 403 `account_disabled`; a disabled Keycloak user cannot sign in; the sync command deactivates users deleted in Keycloak |
| SYS-AUTH-09 | EXT, MANUAL | Registration is Keycloak's, password reset is switched off. Manual: the login page offers registration and no password reset |
| SYS-AUTH-10 | EXT, MANUAL | Keycloak implements the registration form and its validation. Manual: register through the page, land in the student panel; wrong or repeated mobile, email or password are refused on the form |
| SYS-ADM-01 | API, INTEG | Admin creates each role; the account signs in; a duplicate is 409; a consultant needs `consultant_type`; a failed Keycloak call stores nothing |
| SYS-ADM-02 | API, INTEG | Changing a role replaces the old one in Keycloak and the cache; the next token carries it |
| SYS-ADM-03 | API | List filters by role, status and text; disabling blocks sign-in; re-enabling restores it |
| SYS-ADM-04 | API | Every non-admin column of the access matrix is denied; an administrator changing their own role gets 403 `self_modification_forbidden` |
| SYS-ACC-01 | API | The anonymous column of the access matrix (section 4) |
| SYS-ACC-02 | API, INTEG | The whole access matrix; a real-token spot check for one user per role |

### Identity

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-ID-01 | UNIT, EXT | The Core Service refuses a token that lacks a required identity claim (403 `incomplete_identity`); Keycloak's user profile stops an incomplete account from being created |
| SYS-ID-02 | API, INTEG | A first request creates a profile; a changed claim updates the cache in the same request; after an email change in Keycloak, the next token shows it; `sync_keycloak_users --dry-run` reports a planted mismatch and writes nothing, a real run fixes it |
| SYS-ID-03 | API | Identity fields are read-only in serializers and in the Django admin |
| SYS-ID-04 | UNIT | Normalizer table: Persian digits, Arabic digits, `+98`, `0098`, too short, wrong prefix |
| SYS-ID-05 | API | With the Admin API stub set to fail, `PATCH /me` returns 502 `identity_provider_unavailable` and the cache is unchanged |
| SYS-ID-06 | API | `/panel` returns the full name, and the field of study for a student |

### Panels, services and integration

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-PNL-01 | API | A student gets exactly the 10 entries of AC-SERVICES, in order |
| SYS-PNL-02 | API, MANUAL | Admin gets 3, consultant 6, professor 6; manual check that choosing an entry loads it in the content area |
| SYS-PNL-03 | API | Countdown with a frozen clock (exam today, in the past, in the future); notifications shape; student dashboard fields |
| SYS-PNL-04 | API | The landing response has every section; changing a fixture value changes the response with no code change |
| SYS-PNL-05 | API | An entry with no target URL, and a disabled entry, return `unavailable` |
| SYS-PNL-06 | API | Editing one of two shared entries leaves the other unchanged |
| SYS-INT-01 | API | Setting a target URL through the admin or API makes it appear in `/panel/services` |
| SYS-INT-02 | INTEG | The reference group service accepts a valid token and refuses a missing token, a wrong audience and a wrong role |
| SYS-INT-03 | API | `internal/users/{sub}` and `internal/users` work with a service token and not with a user token; the list filters by role |
| SYS-INT-04 | INTEG | `check_service.py` passes on the reference service and fails on a deliberately broken one |
| SYS-INT-05 | MANUAL | One entry in `embed` mode and one in `redirect` mode work from the frontend |

### Seed data

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-DATA-01 | INTEG | After `make reset`, a token can be obtained for a sampled seeded user of each role |
| SYS-DATA-02 | API | Every seeded profile has a non-empty name and email, a valid normalized mobile number, and an email at the `gradian.test` domain |
| SYS-DATA-03 | UNIT | Per-role counts match AC-SEED and do not depend on the number of groups (10 and 3) |
| SYS-DATA-04 | UNIT | The generator is deterministic (two runs, identical output); realm user ids equal the fixture ids; the password never reaches a fixture. `loaddata` twice is Django's own behaviour with fixed primary keys |
| SYS-DATA-05 | UNIT, MANUAL | One file lists every seeded user with role, name, mobile and password, another each group's client id and secret; files are replaced, private and readable in Excel. Manual: `make users` writes them to the git-ignored directory |
| SYS-DATA-06 | API | After bootstrap there are 25 service entries, landing content and widget data |
| SYS-DATA-07 | UNIT | `seed`, `realm`, `users` and `bootstrap` refuse to run with `ENVIRONMENT=production` |

### Local operation

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-OPS-01 | MANUAL, INTEG | On a clean clone, `make start` reaches a healthy `/health/ready`; checked by someone other than the author |
| SYS-OPS-02 | MANUAL | After changing data, `make reset` restores the seeded state |
| SYS-OPS-03 | MANUAL | `make test` passes with no containers running; `make itest` runs only tagged tests |
| SYS-OPS-04 | MANUAL | `make help` lists every target; the same sequence works on two different machines |
| SYS-OPS-05 | STATIC | A script checks that `.env.example` lists every variable the settings read; a secret scan finds nothing in the repository |
| SYS-OPS-06 | UNIT, EXT | The helper that reads a required variable raises an error naming it; that the settings module fails at startup is Django's behaviour |

### Quality attributes

| Requirement | Level | What the tests check |
| --- | --- | --- |
| SYS-NFR-01 | API, EXT | Captured logs and error bodies contain no token or password; the rate limit returns 429 past the configured limit. HTTPS and the standard hardening are Django's security settings; `manage.py check --deploy` can be run by hand with production settings |
| SYS-NFR-02 | PERF | At 50 concurrent users, `/me` and `/panel/services` stay within 300 ms at the 95th percentile |
| SYS-NFR-03 | API, INTEG | With the key fetch failing after a first success, a valid token still works; with Keycloak stopped, `/health/ready` fails |
| SYS-NFR-04 | STATIC | The exported OpenAPI schema is compared with the frozen baseline; removals and renames fail |
| SYS-NFR-05 | UNIT, EXT | Every error message is Persian while its code is English. The default language and time zone are Django settings and are not asserted |
| SYS-NFR-06 | API | Log records exist for profile creation, a role-resolution failure and a sync change |
| SYS-NFR-07 | MANUAL | Someone follows the README to a running system; the integration guide exists |
| SYS-NFR-08 | STATIC | `scripts/req_coverage.py` reports no requirement with neither a test nor an `EXT` mark |

## 4. Access matrix test (AC-ACCESS)

The requirement states capabilities; this table fixes the endpoints and exact responses. The API test iterates over every cell.

| Capability | Endpoint | Anonymous | Student | Consultant | Professor | Admin | Service |
| --- | --- | --- | --- | --- | --- | --- | --- |
| View landing content | `GET /api/v1/landing` | 200 | 200 | 200 | 200 | 200 | 200 |
| View own identity and panel | `GET /api/v1/me` | 401 | 200 | 200 | 200 | 200 | 403 |
| List own panel's services | `GET /api/v1/panel/services` | 401 | 200 (10) | 200 (6) | 200 (6) | 200 (3) | 403 |
| View student dashboard | `GET /api/v1/student/dashboard` | 401 | 200 | 403 | 403 | 403 | 403 |
| List users | `GET /api/v1/internal/users` (service), `GET /api/v1/admin/users` (admin) | 401 | 403 | 403 | 403 | 200 | 200 |
| Look up a user by ID | `GET /api/v1/internal/users/{sub}` | 401 | 403 | 403 | 403 | 403 | 200 |
| List accounts | `GET /api/v1/admin/users` | 401 | 403 | 403 | 403 | 200 | 403 |

The number in brackets is the count of entries returned. Three extra cases sit beside the matrix: a user with no panel role (200, the student panel), a user with two panel roles (403 `ambiguous_role`) and an inactive profile (403 `account_disabled`).

## 5. Test data rules

- Fast tests never depend on seed content, except the seed tests that exist to check it.
- Integration tests never modify seeded users in Keycloak; they create and remove temporary ones.
- Mobile numbers used by temporary users come from a range outside the seeded one, so they cannot collide.
- The test realm file, including the client `gradian-test`, is never built for production (DES-IDP-09).

## 6. Manual acceptance checklist

Run by someone other than the author, on a clean machine, from a fresh clone.

1. `make env`, set `SEED_DEFAULT_PASSWORD`, then `make start`. The system becomes healthy without further steps.
2. Sign in as one seeded user of each role, and confirm the landing panel against AC-ROUTE.
3. In each panel, confirm the service count and that an unconnected entry shows as unavailable.
4. Use the logout icon in each panel and confirm the return to the landing page.
5. Change one entry's target URL in the Django admin and see it in the panel.
6. Change a user's email in Keycloak, sign in again, and see the new email.
7. Run `make users` and check `users.csv` and `services.csv`.
8. Run `make reset` and confirm the seeded state returns.
9. Run `make test` with no containers, then `make itest`.
10. Run `make check-service` against the reference service.

## 7. Definition of done

- Every requirement in 01 has at least one test, and `scripts/req_coverage.py` reports no gaps.
- `make check` is green in CI, and `make itest` is green on the Compose stack.
- The access matrix test passes for every cell.
- The manual acceptance checklist passes on a clean machine.
- The performance run meets SYS-NFR-02 once before groups begin integrating.
