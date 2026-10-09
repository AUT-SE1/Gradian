# Gradian: Konkur preparation platform (Core Service)

The Core Service signs people in through Keycloak, resolves their role-based panel, and serves the
landing content, the panel headers, the student dashboard and the 25 panel service entries. The student project groups build
their features as separate Django services that sign people in through the same Keycloak and call
the Core Service by API.

Documentation lives in [`docs/`](docs/): [requirements](docs/01-requirements.md),
[design and API](docs/02-design.md), [decisions](docs/03-decisions.md),
[test plan](docs/04-test-plan.md), the [guide for the frontend team](docs/05-frontend-guide.md) and the
[integration guide for project groups](docs/06-integration-guide.md). Working on the code? Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Status

| Step | Scope | State |
| --- | --- | --- |
| 1 | Tooling, project skeleton, Keycloak realm template, identity and authentication (`/me`, `/auth/config`, profile cache and sync), health checks, OpenAPI | **Done** |
| 2 | Seed generator (users for every group, fixture, credentials), service clients and the internal user API, registration page, account administration | **Done** (frontend contract still open) |
| 3 | Panels: landing content, service registry (25 entries), dashboard widgets, notifications | **Done** |
| 4 | Group-service reference and `check-service`, integration tests, OpenAPI stability check, load test, integration guide | **Done**, except that the load target (SYS-NFR-02) still has to be measured with `make perf` on a real machine |

`make lint` prints which requirements already have a test, and fails when one has neither a test nor an
`EXT` mark in the test plan.

## Ports

| Port | Service |
| --- | --- |
| 8080 | Keycloak |
| 8000 | Core Service (`core/`) |
| 5432 | PostgreSQL (localhost only) |
| 8001-8010 | Team services in `teams/teamN/` (localhost only) |

## Requirements on your machine

Docker Engine, the Docker Compose v2 plugin (`docker compose`) and `make`. Nothing else: all
Python tooling and the services run in containers, so your own Python version does not matter.

## Run

Everything is a `make` target. The main ones, each a short name for a sequence of steps (`make help`
shows them and the steps they are made of):

| Command | What it does |
| --- | --- |
| `make start` | Everything, with demo data: `.env` files, user fixture, realm file, containers, migrations |
| `make stop` | Remove the containers, keep the data |
| `make reset` | Wipe the database and Keycloak data, then `start` again |
| `make check` | Lint, strict types, fast tests and the OpenAPI check: run before every push |
| `make itest` | Start the system if needed, then the tests that use it |
| `make users` | Write the sign-in details of the seeded users to `build/credentials/` |
| `make check-service URL=...` | Check that a group service follows the integration rules (`docs/06-integration-guide.md`) |
| `make perf` | Load test: 50 concurrent users, p95 must stay within 300 ms (needs the stack) |
| `make baseline` | Freeze the current OpenAPI schema; `make schema` then fails on anything removed or renamed |
| `make dev-frontend` | Serve a throwaway page on http://localhost:5173 to try the sign-in flow (`dev-frontend/README.md`) |
| `make packages` | Build wheels of `packages/` into `build/wheels/`, for services in another repository |

`make start TEAMS="1 6 5"` also starts the services of teams 1, 6 and 5 (`all` for every team).
`make logs`, `make shell` and `make manage CMD="..."` are for working with the running system, and
`make format` applies formatting.

`make start` creates every missing `.env` from its `.env.example` with fresh secrets (existing
files are never overwritten). Edit the root `.env` for passwords, the public URL and `FRONTEND_URL`,
then `make reset`: Keycloak reads the realm only when it first imports it. A required variable that
is missing stops startup with a message naming it.

Keycloak console: http://localhost:8080 (`KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`).
API docs: http://localhost:8000/api/docs/ (OpenAPI schema at `/api/schema/`).
Django admin: http://localhost:8000/admin/ (create an operator with
`make manage CMD=createsuperuser`; identity fields are read-only there).

## Trying the system by hand

1. `make start`, then `make users`. Open `build/credentials/users.csv`: one line per seeded user
   with role, name, mobile number and password (the password is `SEED_DEFAULT_PASSWORD`).
2. Open http://localhost:8000/api/docs/, press *Authorize*, choose `keycloakPassword`, enter a
   mobile number and the password, and leave the client id. Try `GET /api/v1/me`: it returns the
   person's panel, for example `student`. Press *Logout* and sign in as another role.
3. **Register as a new person.** Open the registration page (see below), fill the form, and you
   are signed in as a new student. Call `/me` again with the new token: the profile now exists, and
   the role `student` has been granted in Keycloak.
4. **Act as an administrator.** Sign in as an admin from the CSV, then use `/api/v1/admin/users`
   to list accounts, create a professor with a password, and change someone's role. Sign in as
   the new professor to see the new panel.
5. **Act as a group service.** Take `client_id` and `client_secret` from
   `build/credentials/services.csv` (the `group-1` row) and get a token:

       curl -s -d grant_type=client_credentials -d client_id=group-1 -d client_secret=... \
         http://localhost:8080/realms/gradian/protocol/openid-connect/token

   Call `GET /api/v1/internal/users?role=student` and `/api/v1/internal/users/{sub}` with it. The
   same token is refused on `/me`, and a person's token is refused on `/internal/users`.
6. `make reset` returns everything to the seeded state.

## Panels, services and content

| Endpoint | Who | What |
| --- | --- | --- |
| `GET /api/v1/landing` | anyone | navbar, hero, statistics, mission cards, teachers, top-rankers, testimonials, footer |
| `GET /api/v1/panel` | any panel | full name (and field of study for a student) for the header, and the Konkur countdown |
| `GET /api/v1/panel/services` | any panel | the entries of your own panel in order: 10 student, 6 consultant, 6 professor, 3 admin |
| `GET /api/v1/student/dashboard` | student | welcome message, countdown, study streak, experience-feed preview |
| `GET /api/v1/notifications` | any panel | the bell: unread count and items, empty until someone creates some in the Django admin |

An entry whose service is not connected (no address) or is disabled is still listed, with
`status: unavailable`. To connect one, set its address and mode in the Django admin (*Service
entries*; quick, but replaced when the demo data is loaded again) or in `seed/content/services.yaml`
(permanent), see the [integration guide](docs/06-integration-guide.md).

The demo content is in `seed/content/` (`services.yaml`, `landing.yaml`, `widgets.yaml`, Persian) and
is loaded as fixtures by `make seed` and `make bootstrap`; it can also be edited in the Django admin
(*Content blocks*; the shape is checked when you save). The countdown counts down to `KONKUR_DATE` in
`.env`.

## Seeded users

`seed/people.yaml` is the single source: 40 students, 10 consultants, 10 top-rankers (consultants
with `consultant_type=top_ranker`), 10 professors and 10 admins. Every user signs in with the mobile
number and `SEED_DEFAULT_PASSWORD` from `.env`.

The users are one pool shared by all project groups, and every user is valid for every group's
service. The system does not record groups. `make users` writes `build/credentials/users.csv`
(role, name, mobile, password) and `services.csv` (each group's Keycloak client id and secret, one
client `group-N` per group). The folder is git-ignored; do not share it outside the course.

Mobile number = `0900` + kind (1 digit) + index (6 digits). Kinds: 1 student, 2 consultant,
3 top-ranker, 4 professor, 5 admin. So `09001000002` is the second student and `09005000001` the
first admin. Kind 9 is reserved for the temporary users of integration tests. Emails are
`<kind>.<index>@gradian.test`, for example `top-ranker.3@gradian.test`.
User ids are `uuid5(namespace, mobile)`, the same in Keycloak and in the Core `Profile`.

The fixture `core/accounts/fixtures/profiles.json` and the realm file `build/realm-gradian.json`
are build artifacts, generated by `make seed` and `make realm` and git-ignored. Change the seed by
editing `seed/people.yaml`, then `make reset`.

Group services call the Core Service with the client-credentials token of their group's client
(`group-N`, DEC-20) on `GET /api/v1/internal/users?role=` and `GET /api/v1/internal/users/{sub}`.

## How sign-in works

1. The frontend (client `gradian-web`, Authorization Code with PKCE) reads `GET /api/v1/auth/config`
   and sends the user to Keycloak's themed login page: mobile number and password.
2. It calls `GET /api/v1/me` with `Authorization: Bearer <access token>`.
3. The Core Service validates the token locally (RS256 signature from the realm's published keys,
   issuer, expiry, audience `gradian-core`), creates or refreshes the user's profile from the token
   claims, and returns the identity plus `panel` and `home_path`:

| Role | `home_path` |
| --- | --- |
| `student` | `/student` |
| `consultant` (also top-rankers: `consultant_type=top_ranker`) | `/consultant` |
| `professor` | `/professor` |
| `admin` | `/admin` |

A person with no panel role is a student (Core also grants the role in Keycloak the first time it
sees them). An account with more than one panel role is refused with 403 `ambiguous_role`. Errors
always look like `{"code": "...", "message": "<Persian>", "details": {}}`.

## Registration and account administration

Anyone can register on the Keycloak page `http://localhost:8080/realms/gradian/protocol/openid-connect/registrations`
(with the `gradian-web` authorization parameters; `GET /api/v1/auth/config` returns it as
`registration_endpoint`, and the login page links to it). A registrant gives first name, last name,
mobile number, email and a password of at least 8 characters, is signed in at once, and is a
student. Mobile numbers are not verified, and there is no password recovery. The page is the theme
in `keycloak/themes/gradian/`; its [README](keycloak/themes/gradian/README.md) is the contract for
the frontend team, who will restyle it later.

Administrators (admin panel) manage accounts through the API, also from `/api/docs/`:

| Endpoint | What it does |
| --- | --- |
| `GET /api/v1/admin/users?role=&is_active=&q=` | List accounts |
| `POST /api/v1/admin/users` | Create an account of any role, with its password (consultants need `consultant_type`) |
| `GET /api/v1/admin/users/{sub}` | One account |
| `PATCH /api/v1/admin/users/{sub}` | Change role, `consultant_type`, `is_active`, names, email, field of study |

A new role replaces the person's old one, and a token already issued keeps the old role until it
expires (at most 10 minutes). Administrators cannot change their own role or status.

## Layout

    core/            Django project: gradian/ (settings), accounts/ (identity, admin and service APIs), registry/ (service entries and panel menus), panels/ (landing, header, dashboard, notifications), common/ (errors, logging, health)
    keycloak/        realm-template.json, user-profile.json, themes/gradian/ (login and registration pages)
    seed/            people.yaml, names.yaml: the seeded users; content/: services, landing and widgets
    dev-frontend/    the sign-in tester page behind `make dev-frontend`
    packages/        gradian-keycloak, gradian-auth, gradian-testing: shared code, installed by Core and by every group service (see packages/README.md)
    scripts/         seed_generate.py, seed_credentials.py, render_realm.py, check_env_example.py, req_coverage.py, wait_for.sh, ...
    docs/            requirements, design, decisions, test plan, guides for the frontend team and for groups
    teams/           the ten team service skeletons (see below)

## Test

    make test     # fast tests; no system needed
    make itest    # starts the system if needed, then the integration tests
    make check    # lint, strict types, fast tests, OpenAPI check
    make perf     # the load test; run it on the machine that will host the system

Continuous integration should run `make check` on every push, and a second job `make itest`
(it starts the stack). The CI platform is not chosen yet; both are single commands.

**After adding or changing a model** run `make migrations` and commit the files. The `registry` and
`panels` apps are new, so run it once before `make start`; `make lint` fails while a migration is
missing.

## Team services (`teams/`)

Each `teams/teamN/` is a separate Django project with its own Dockerfile, compose file and `.env`.
Per the design (DES-REG-05) a group service validates the Keycloak access token itself and checks
that `aud` contains its own client id; the Core Service does not proxy requests or set `X-User-*`
headers. The skeletons in `teams/` do this with the shared [`packages/`](packages/README.md): each
sets `KEYCLOAK_CLIENT_ID=group-N` in its `.env` (copy the other Keycloak lines from `.env.example`;
an existing `.env` is never overwritten, so add them by hand) and reads the caller with
`current_principal(request)`. Start with the [gradian-auth guide](packages/gradian-auth/README.md).

People reach a group's pages by **redirect** from the panel and are signed in there by single sign-on
(they are already signed in at Keycloak): with the skeletons, sign in at the panel, then open
`http://localhost:800N/app` and you land on the page without a login form. Each group's client needs
its secret from `services.csv` in `KEYCLOAK_CLIENT_SECRET`; see the
[integration guide](docs/06-integration-guide.md).
