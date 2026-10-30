# Gradian: University Entrance Exam Prep Platform

Django backend, Keycloak for authentication (the username is the phone number, e.g. `+989...`), and a React/TypeScript frontend. Everything runs in Docker.

## Repository layout

| Folder | Contents |
|---|---|
| `backend/` | Django core, Keycloak, PostgreSQL and the team services (`backend/teams/teamN/`) |
| `frontend/` | Main React app and the independent team apps (`frontend/teams/teamN`) |
| `docs/`, `scripts/` | Documentation and helper scripts |

## Ports

| Port | Service |
|---|---|
| 5173 | Frontend |
| 8000 | Main backend (core) |
| 8080 | Keycloak (auth) |
| 5433 | PostgreSQL (bound to `127.0.0.1` only) |
| 8001–8010 | Team 1–10 services (localhost only; see `TEAM_SERVICES` in `gradian/settings.py`) |

If something else on your machine already uses these ports (nginx, another Vite/Docker project, ...), stop it first. See [Troubleshooting](#troubleshooting).

## Prerequisites

- Git
- Docker with Docker Compose v2 (`docker compose`)
- `make` (recommended)
- Ports 5173, 8000, 8080 and 5433 free

## Quick start (first run)

Start the backend **before** the frontend. Each `docker compose up` below keeps running in its terminal; use a separate terminal for each, or add `-d` to run in the background.

### 1. Clone

```bash
git clone https://github.com/AUT-SE1/Gradian.git
cd Gradian
```

### 2. Create the Docker network (once)

Compose expects an external network called `gradian` and does not create it. Without it you get
`network gradian declared as external, but could not be found`.

```bash
docker network create gradian
```

### 3. Create the `.env` file

```bash
cd backend
make env
```

This creates `.env` from `.env.example` and fills in fresh random secrets. If you copy the file manually instead
(`cp .env.example .env`), replace every `change-me` value (`DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`,
`KEYCLOAK_ADMIN_PASSWORD`, `DEV_USER_PASSWORD`, ...).

### 4. Generate the Keycloak realm file

`docker-compose.yml` mounts `backend/build/realm-gradian.json` into Keycloak as its import file. That file is not
committed; it is rendered from `backend/keycloak/realm-template.json` using the values in `.env`.

```bash
make realm
ls -la build/realm-gradian.json     # must be a regular file, not a directory
```

> **Warning:** if you run `docker compose up` before this file exists, Docker creates an empty **directory** with that
> name (owned by root). Keycloak then starts without importing the `gradian` realm, and the login page fails.
> See [Fixing a missing realm](#fixing-a-missing-realm-404-on-realmsgradian).

### 5. Start the backend

```bash
docker compose up -d --build
```

Keycloak needs up to a minute to become ready. Check:

```bash
docker compose ps                                  # core, db and keycloak should be healthy
curl -I http://localhost:8000
curl -I http://localhost:8080/realms/gradian       # must return 200 OK
```

### 6. Start the frontend

In another terminal:

```bash
cd frontend
docker compose up --build
```

Open http://localhost:5173. The first build takes a few minutes.

More frontend docs: [`frontend/README.md`](frontend/README.md) and
[`frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md`](frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md).

### Shortcut: one command with demo data

From `backend/`, `make start` runs the whole sequence (seed data, realm, services, bootstrap) and creates the demo users:

```bash
make start
```

## Stopping and resetting

```bash
cd backend  && docker compose down
cd frontend && docker compose down
```

To also delete the database and Keycloak data (for example to force the realm to be imported again), use `-v`.
**This deletes all local data.**

```bash
cd backend && docker compose down -v
```

## Make targets

Run these from `backend/`. Older versions of this README listed `make all`, `make 3`, `make teams 1 6 5` and
`make down`; those targets do not exist in the current Makefile and fail with `No rule to make target`.

| Command | Description |
|---|---|
| `make env` | Create every missing `.env` from its `.env.example`, with fresh secrets |
| `make realm` | Render `build/realm-gradian.json`, the Keycloak import file |
| `make up` | Create `.env` files and the realm, then start core, Keycloak, the database and the team services |
| `make start` | Everything above plus demo data and users (`seed realm up bootstrap`) |
| `make users` | Write the seeded users' sign-in details and group service credentials to `build/credentials/` |
| `make test` | Run the tests |
| `make logs` | Same as `docker compose logs -f` |

List all targets with `grep -E '^[a-zA-Z_-]+:.*##' Makefile`.

> `make core` does nothing (`Nothing to be done for 'core'`) because a directory named `core/` exists and the target is
> not declared `.PHONY`. Use `docker compose` or one of the targets above.

## Signing in

The username is the phone number; the password is `DEV_USER_PASSWORD` from `.env`. These dev users exist after
`make start`:

| Role | Phone |
|---|---|
| admin | `+989120000001` |
| candidate | `+989120000002` |
| advisor | `+989120000003` |
| instructor | `+989120000004` |

Keycloak admin console: http://localhost:8080 (`KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` from `.env`).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no configuration file provided: not found` | You are in a folder without a `docker-compose.yml` | `cd` into `backend/` or `frontend/`; there is no compose file at the repository root |
| `network gradian declared as external, but could not be found` | The network was never created | `docker network create gradian` |
| `port is already allocated`, or `curl` to a port fails | Another program holds the port, or nothing is running | `sudo ss -ltnp \| grep -E ':(5173\|8000\|8080\|5433)\b'` and `docker ps`; stop the conflicting service (`docker stop <name>`, `sudo systemctl stop nginx`, ...) |
| `localhost:5173` shows a different project | A container or dev server from another project is on that port | Same as above; open the page in a private window to rule out browser cache |
| `docker compose ps` shows nothing | `up` was not run, or it failed immediately | Run `docker compose up --build` without `-d` and read the output |
| Login page says it could not reach the login service, and `curl http://localhost:8080/realms/gradian` returns `404` | The `gradian` realm was not imported because `backend/build/realm-gradian.json` was missing (or is a directory) | See below |
| Keycloak shows "We are sorry... Page not found" on the login URL | Same cause: the realm does not exist | See below |
| `change-me` values in `.env` | `.env` was copied but not filled in | `make env`, or edit the values by hand |

### Fixing a missing realm (404 on `/realms/gradian`)

```bash
cd backend
docker compose down -v
sudo rm -rf build/realm-gradian.json     # in case Docker created a directory
make realm                               # if this fails with "permission denied": sudo chown -R $USER:$USER build
ls -la build/realm-gradian.json          # must be a file, not a directory
docker compose up -d --build
curl -I http://localhost:8080/realms/gradian    # must return 200
```

Then hard-refresh the login page (`Ctrl+Shift+R`).

## Authentication flow

1. Get a token from Keycloak:
   ```bash
   curl -d grant_type=password -d client_id=gradian-web \
        --data-urlencode username=+989120000002 -d password=<DEV_USER_PASSWORD> \
        http://localhost:8080/realms/gradian/protocol/openid-connect/token
   ```
2. `GET /api/auth/me/` with `Authorization: Bearer <access_token>` returns `{phone, role, redirect}`.
3. Go to `redirect`:

| Role | Home | Endpoints (GET) |
|---|---|---|
| admin | `/api/admin-panel/` | `question-bank/`, `adviser-meetings/`, `shop-items/` |
| candidate | `/api/candidate/` | returns the ten team service URLs |
| advisor | `/api/advisor/` | `profile/`, `student-reports/`, `academic-tutoring/`, `experiences/`, `online-meetings/`, `resource-hub/` |
| instructor | `/api/instructor/` | TBD |

Feature endpoints are placeholders (`views.feature`). Replace them with real views guarded by `@role_required("<role>")`.

## Team services (simplified microservices)

Each `backend/teams/teamN/` is its own Django project (`config/` + `core` app) with its own Dockerfile,
docker-compose, `.env` and SQLite database. Teams never handle login themselves:

```
client -> core /api/teams/N/<path>   (checks the Keycloak token)
       -> teamN:800N/<path>           with headers X-User-Phone, X-User-Role, Authorization
```

Read the user with `current_user(request)` in `teams/teamN/core/views.py`. Team ports are bound to `127.0.0.1`
because the service trusts those headers, so always go through the gateway.

Run one team on its own:

```bash
docker network create gradian        # if you have not already
cd backend/teams/teamN
cp .env.example .env
docker compose up --build
```

## Independent frontend team applications

The shared React application lives in `frontend/src`. Each project group also has an independent frontend application
in `frontend/teams/teamN`. A team may use React, Angular, Vue, Svelte or plain HTML/CSS/JavaScript. The shell opens the
URL from the Core Service registry, and the team application authenticates with Keycloak using Authorization Code +
PKCE before calling its backend service.

```bash
cd frontend
npm run teams:check          # validate the team application contract
npm run build:teams          # after installing dependencies in the team folders
```

The optional `frontend/docker-compose.teams.yml` builds the ten starter applications on ports 8101–8110.

## Tests

```bash
cd backend
make test                    # or: python manage.py test
```
