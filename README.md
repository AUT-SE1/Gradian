# Gradian: University Entrance Exam Prep Platform (backend core)

Django backend. Keycloak handles login, and the username is the phone number (`+989...`).

## Ports
| Port | Service |
|------|---------|
| 8080 | Keycloak (auth) |
| 8000 | Main backend (this repo) |
| 8001–8010 | Team 1–10 services in `teams/teamN/` (localhost only; see `TEAM_SERVICES` in `gradian/settings.py`) |

## Run
    make all            # core (keycloak + backend) + all ten teams
    make core           # core only
    make 3              # core + team 3
    make teams 1 6 5    # core + teams 1, 6, 5
    make down           # stop everything
    make logs / make test

Starting a selection stops the teams not in it. On first run, `make` creates each missing `.env` from its
`.env.example` with a fresh secret key (existing `.env` files are never overwritten). Edit the root `.env`
for passwords and the public URL. Every service joins the shared docker network `gradian`.
Keycloak admin console: http://localhost:8080 (`KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`). The `gradian` realm is imported from `keycloak/`.
Dev users (password = `DEV_USER_PASSWORD`): `+989120000001` admin, `…02` candidate, `…03` advisor, `…04` instructor.

## Flow
1. Get a token from Keycloak:
       curl -d grant_type=password -d client_id=gradian-web --data-urlencode username=+989120000002 -d password=<DEV_USER_PASSWORD> \
         http://localhost:8080/realms/gradian/protocol/openid-connect/token
2. `GET /api/auth/me/` with `Authorization: Bearer <access_token>` returns `{phone, role, redirect}`.
3. Go to `redirect`:

| Role | Home | Endpoints (GET) |
|------|------|-----------------|
| admin | `/api/admin-panel/` | `question-bank/`, `adviser-meetings/`, `shop-items/` |
| candidate | `/api/candidate/` | returns the ten team service URLs |
| advisor | `/api/advisor/` | `profile/`, `student-reports/`, `academic-tutoring/`, `experiences/`, `online-meetings/`, `resource-hub/` |
| instructor | `/api/instructor/` | TBD |

Feature endpoints are placeholders (`views.feature`). Replace them with real views guarded by `@role_required("<role>")`.

## Team services (simplified microservices)
Each `teams/teamN/` is its own Django project (`config/` + `core` app) with its own Dockerfile,
docker-compose, `.env` and SQLite database. Teams never handle login themselves:

    client -> core /api/teams/N/<path>  (checks the Keycloak token)
           -> teamN:800N/<path>          with headers X-User-Phone, X-User-Role, Authorization

Read the user with `current_user(request)` in `teams/teamN/core/views.py`. Team ports are bound to
127.0.0.1 because the service trusts those headers, so always go through the gateway.
Run one team alone: `cd teams/teamN && docker compose up --build` (needs `docker network create gradian` and a `.env`).

## Test
    python manage.py test


## Frontend

فرانت‌اند React/TypeScript در پوشه‌ی `frontend/` قرار دارد و Compose مستقل خودش را دارد. ابتدا بک‌اند و سپس فرانت‌اند را اجرا کنید:

```powershell
cd backend
Copy-Item .env.example .env
docker compose up -d --build

cd ../frontend
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend core: http://localhost:8000
- Keycloak: http://localhost:8080

راهنمای اجرای فرانت‌اند: [`frontend/README.md`](frontend/README.md)  
راهنمای معماری و قرارداد استفاده از AI: [`frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md`](frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md)
