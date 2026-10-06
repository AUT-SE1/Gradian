# Gradian: Konkur preparation platform (Core Service)

The Core Service signs people in through Keycloak, resolves their role-based panel, and (in later
steps) serves the landing content, the 25 panel service entries and the project-group data that the
student group services connect to.

Documentation lives in [`docs/backend/`](docs/backend/): [requirements](docs/backend/01-requirements.md),
[design and API](docs/backend/02-design.md), [decisions](docs/backend/03-decisions.md),
[test plan](docs/backend/04-test-plan.md). Working on the code? Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Status

| Step | Scope | State |
| --- | --- | --- |
| 1 | Tooling, project skeleton, Keycloak realm template, identity and authentication (`/me`, `/auth/config`, profile cache and sync), health checks, OpenAPI | **Done** |
| 2 | Seed generator (users for every group, fixtures, credentials), group and project-group APIs, service-account endpoints | Next |
| 3 | Panels: landing content, service registry (25 entries), dashboard widgets, notifications | Planned |
| 4 | Group-service template and `check-service`, integration tests, load test, integration guide | Planned |

`make req-coverage` shows which requirements already have a test.

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

    make up bootstrap          # env files, realm file, containers, migrations
    make dev-user MOBILE=09120000001 ROLES=student
    make up TEAMS="1 6 5"      # core + teams 1, 6, 5; the other teams are stopped
    make down                  # stop and remove everything
    make reset                 # wipe the database and Keycloak data, start clean
    make logs / make shell
    make check                 # lint + typecheck + test, in containers

`make up` creates every missing `.env` from its `.env.example` with fresh secrets (existing files
are never overwritten). Edit the root `.env` for passwords, the public URL and `FRONTEND_URL`.
A required variable that is missing stops startup with a message naming it.
`make help` lists every target.

Keycloak console: http://localhost:8080 (`KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`).
The `gradian` realm is imported from `keycloak/realm-template.json` (rendered to
`build/realm-gradian.json` by `make seed-render`). It has no users until step 2 adds the seeded
ones, so create demo users with `make dev-user`: `MOBILE` is required; `ROLES` is a
comma-separated list (default `student`; `none` or `student,admin` show the 403 role errors);
a consultant needs `CONSULTANT_TYPE=consultant` or `top_ranker`. The password is
`SEED_DEFAULT_PASSWORD` from `.env`.

API docs: http://localhost:8000/api/docs/ (OpenAPI schema at `/api/schema/`).
Django admin: http://localhost:8000/admin/ (create an operator with
`make manage CMD=createsuperuser`; identity fields are read-only there).

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

An account with no panel role, or with more than one, is refused with 403 `role_not_assigned` or
`ambiguous_role`. Errors always look like `{"code": "...", "message": "<Persian>", "details": {}}`.

## Layout

    core/            Django project: gradian/ (settings), accounts/ (identity), common/ (errors, logging, health)
    keycloak/        realm-template.json, user-profile.json
    scripts/         render_realm.py, dev_user.py, check_env_example.py, req_coverage.py, wait_for.sh, ...
    docs/backend/    requirements, design, decisions, test plan
    teams/           the ten team service skeletons (see below)

## Test

    make test               # fast tests; no stack needed
    make test-integration   # needs `make up bootstrap`
    make check              # lint + typecheck + test

## Team services (`teams/`)

Each `teams/teamN/` is a separate Django project with its own Dockerfile, compose file and `.env`.
Per the design (DES-REG-05) a group service validates the Keycloak access token itself and checks
that `aud` contains its own client id; the Core Service no longer proxies requests or sets
`X-User-*` headers. The skeletons in `teams/` still read those headers and are replaced by a
token-validating reference service in step 4.
