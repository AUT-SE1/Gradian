# Gradian: Konkur preparation platform (Core Service)

The Core Service signs people in through Keycloak, resolves their role-based panel, and (in later
steps) serves the landing content and the 25 panel service entries. The student project groups build
their features as separate Django services that sign people in through the same Keycloak and call
the Core Service by API.

Documentation lives in [`docs/backend/`](docs/backend/): [requirements](docs/backend/01-requirements.md),
[design and API](docs/backend/02-design.md), [decisions](docs/backend/03-decisions.md),
[test plan](docs/backend/04-test-plan.md). Working on the code? Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Status

| Step | Scope | State |
| --- | --- | --- |
| 1 | Tooling, project skeleton, Keycloak realm template, identity and authentication (`/me`, `/auth/config`, profile cache and sync), health checks, OpenAPI | **Done** |
| 2 | Seed generator (users for every group, fixture, credentials), service clients and the internal user API, registration page, account administration | **Done** (frontend contract still open) |
| 3 | Panels: landing content, service registry (25 entries), dashboard widgets, notifications | Planned |
| 4 | Group-service template and `check-service`, integration tests, load test, integration guide | Planned |

`make lint` prints which requirements already have a test.

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

1. `make start`, then `make users`. Open `build/credentials/group-1.csv`: one line per seeded user
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
   `build/credentials/group-1-service.csv` and get a token:

       curl -s -d grant_type=client_credentials -d client_id=group-1 -d client_secret=... \
         http://localhost:8080/realms/gradian/protocol/openid-connect/token

   Call `GET /api/v1/internal/users?role=student` and `/api/v1/internal/users/{sub}` with it. The
   same token is refused on `/me`, and a person's token is refused on `/internal/users`.
6. `make reset` returns everything to the seeded state.

## Seeded users

`seed/people.yaml` is the single source: 10 groups, and per group 4 students, 1 consultant,
1 top-ranker (a consultant with `consultant_type=top_ranker`), 1 professor and 1 admin, plus one
TA admin who belongs to no group. Every user signs in with the mobile number and
`SEED_DEFAULT_PASSWORD` from `.env`.

A project group is only an allocation: the system does not record it, and every user is valid for
every group's service. A group's allocation is its own users in `build/credentials/group-N.csv`
(role, name, mobile, password) and its own Keycloak client `group-N` in
`group-N-service.csv`; `ta.csv` holds the TA admin. The folder is git-ignored; do not share it
outside the course.

Mobile number = `0900` + group (3 digits, `000` for the TA) + kind (1 digit) + index (3 digits).
Kinds: 1 student, 2 consultant, 3 top-ranker, 4 professor, 5 admin. So `09000031002` is the
second student of group 3. Group number 999 is reserved for the temporary users of integration
tests. Emails are `<kind>.<group>.<index>@gradian.test`, for example `top-ranker.3.1@gradian.test`.
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

    core/            Django project: gradian/ (settings), accounts/ (identity, admin and service APIs), common/ (errors, logging, health)
    keycloak/        realm-template.json, user-profile.json, themes/gradian/ (login and registration pages)
    seed/            people.yaml, names.yaml: the seeded users
    scripts/         seed_generate.py, seed_credentials.py, render_realm.py, check_env_example.py, req_coverage.py, wait_for.sh, ...
    docs/backend/    requirements, design, decisions, test plan
    teams/           the ten team service skeletons (see below)

## Test

    make test     # fast tests; no system needed
    make itest    # starts the system if needed, then the integration tests
    make check    # lint, strict types, fast tests, OpenAPI check

## Team services (`teams/`)

Each `teams/teamN/` is a separate Django project with its own Dockerfile, compose file and `.env`.
Per the design (DES-REG-05) a group service validates the Keycloak access token itself and checks
that `aud` contains its own client id; the Core Service no longer proxies requests or sets
`X-User-*` headers. The skeletons in `teams/` still read those headers and are replaced by a
token-validating reference service in step 4.
