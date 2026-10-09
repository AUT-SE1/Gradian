# Integration guide for project groups

How a group connects its service to the Gradian platform. It covers what the platform gives you,
what your service must do, how an entry in a panel points at your service, and how to check that you
did it right. Start here; the code you need is in [`packages/`](../packages/README.md).

## 1. What you get and what you build

The Core Service signs people in (through Keycloak), keeps their identity, shows the four panels and
lists the services in each. You build **one service** (a separate Django project). The platform gives
you:

- a **token** for every signed-in person, which your service validates itself: no login of your own;
- a **client** of your own, `group-N`, with a secret, to call the Core Service as a machine;
- a **place in a panel**: an entry whose address you set by configuration, without changing Core code;
- **seeded users** of every role, shared by all groups, to try everything with.

Your service never stores a person's name, email, mobile number or role. They are the identity
provider's; you identify people by `sub` and ask Core when you need more.

## 2. Get your credentials

Run `make users` in `backend/`. It writes `build/credentials/users.csv` (every seeded user with role,
name, mobile number and password) and `build/credentials/services.csv` (`group`, `client_id`,
`client_secret`; yours is the row with your number, for example `group-3`). The folder is git-ignored:
never commit a secret.

## 3. Validate the token

Every request to your service carries `Authorization: Bearer <access token>`. Your service must:

1. check the signature against Keycloak's public keys, the issuer, and the expiry;
2. check that `aud` contains **your own client id** (`group-N`). A token made for another group, or the
   service token of another group, must be refused with 401;
3. identify the person by `sub` and authorize by `realm_access.roles` (`student`, `consultant`,
   `professor`, `admin`), never from a request body or query string;
4. answer 401 without a token, and 403 to a signed-in person whose role may not use the endpoint;
5. expose `GET /health`, with no token needed, answering 200.

You do not have to write this. Install the shared packages and use them:

```python
# settings.py
MIDDLEWARE = [..., "gradian_auth.middleware.KeycloakAuthMiddleware"]
KEYCLOAK_PUBLIC_URL = os.environ["KEYCLOAK_PUBLIC_URL"]   # http://localhost:8080
KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]                 # http://keycloak:8080
KEYCLOAK_CLIENT_ID = "group-3"                            # your own client

# views.py
from gradian_auth.decorators import current_principal, require_user

@require_user("professor", "admin")
def my_view(request):
    principal = current_principal(request)      # principal.sub, principal.panel, principal.identity
    ...
```

The skeletons in `teams/teamN/` are working examples (`/`, `/staff` for a role-restricted endpoint,
`/health`). Details, Django REST Framework, tests and the Docker setup are in the
[gradian-auth guide](../packages/gradian-auth/README.md) and the
[packages index](../packages/README.md).

## 4. Ask the Core Service about people

With your own client's token (client-credentials grant), call the internal API. It answers only to a
service token and refuses people.

| Request | Answer |
| --- | --- |
| `GET /api/v1/internal/users/{sub}` | the identity of one person |
| `GET /api/v1/internal/users?role=professor&is_active=true&q=...` | people, paginated with `limit` and `offset` |

Inside Compose the address is `http://core:8000`. Every seeded user is valid for every group. Code
for the token and the call is in the
[gradian-keycloak guide](../packages/gradian-keycloak/README.md#service_token).

## 5. Appear in a panel

Each panel menu entry has a stable key, an address (`target_url`) and a mode. An entry with no address
shows as *unavailable* until someone connects it. The 25 entries and the group that owns each are in
`seed/content/services.yaml`; the suggested split is:

| Group | Entries |
| --- | --- |
| 1 | `student.simulated-exam` |
| 2 | `student.topic-exam`, `admin.exam-bank` |
| 3 | `student.final-exam-12th` |
| 4 | `student.private-class`, `professor.private-class` |
| 5 | `student.counseling-planning`, `consultant.counseling-sessions`, `admin.counseling-sessions` |
| 6 | `student.marketplace`, `consultant.resources-hub`, `professor.resources-hub`, `admin.store-management` |
| 7 | `consultant.student-reports`, `professor.progress-dashboard` |
| 8 | `student.courses`, `consultant.resolve-problems`, `professor.exam-question-management` |
| 9 | `student.major-selection` |
| 10 | `student.top-ranker-experiences`, `student.experience-exchange`, `consultant.profile`, `consultant.add-experiences`, `professor.profile`, `professor.create-course` |

A service shown in several panels (private class, counseling sessions, resources hub, professional
profile) is several independent entries; they may point at the same service with different addresses
or paths.

**To connect your service:**

- *To try it out:* sign in to the Core Service's Django admin (`http://localhost:8000/admin/`; an
  administrator creates the login with `make manage CMD=createsuperuser`), open *Service entries* and
  set the address and mode. The panel shows it at once. It is replaced the next time the demo data is
  loaded (`make bootstrap`, `make reset`).
- *To keep it:* set `target_url` and `mode` for your entries in `seed/content/services.yaml`, then
  `make seed` and `make bootstrap`.

**Redirect is the way.** The panel sends the person to your address with a plain navigation: there
is no token in the URL and nothing for the frontend to hand over. Your pages learn who the person is
by **single sign-on**: the person is already signed in at Keycloak, so your page sends them there and
they come straight back, with no second login. You do not write this; `gradian-auth` has it:

```python
# urls.py:   path("auth/", include("gradian_auth.oidc_urls"))
# views.py:
from gradian_auth.decorators import current_principal, require_page_user
from gradian_auth.oidc import panel_url

@require_page_user()                       # a visitor who is not signed in is sent to sign in and back
def my_page(request):
    principal = current_principal(request)  # sub, panel, identity: as in section 3
    ... panel_url(principal)                # the link back to the person's own panel
```

The settings (`GRADIAN_SERVICE_URL`, `GRADIAN_FRONTEND_URL`, `KEYCLOAK_CLIENT_SECRET` and the rest) and
what the code guarantees are in the
[gradian-auth guide](../packages/gradian-auth/README.md#pages-reached-by-redirect-single-sign-on). The
skeletons in `teams/teamN/` already do it: open `http://localhost:800N/app` after signing in at the
panel and you land on the page signed in, without a login form.

Your service signs people in with its own client `group-N`, whose secret is in `services.csv`. Keycloak
accepts sign-ins for it only at the address in `group_services` in `seed/people.yaml` (group N on port
8000 + N, `http://localhost:{port}`). If your service runs somewhere else, change that and
`make reset`, so Keycloak learns the new address.

A redirected page must offer a way back to the person's panel (`panel_url`) and a way to sign out
(`/auth/logout`).

`embed` (loading your address in an iframe in the panel) exists in the registry but is not used: a page
in an iframe cannot be given the person's identity the way a redirected page can. If a group ever needs
it, the service must send `Content-Security-Policy: frame-ancestors <frontend origin>` and accept
cross-origin (CORS) calls from the frontend origin (`FRONTEND_URL`, `http://localhost:5173`), and the
TA must first decide how the identity reaches the iframe.

## 6. Check your service

With the stack running (`make start`) and your service up, run:

    make check-service URL=http://team3:8003 \
      ARGS="--group 3 --page-path /app --restricted-path /staff --allowed-roles professor,admin"

`URL` is the address the tools container can reach (inside Compose, `http://teamN:800N`). It signs in
real seeded users and checks, in order: the health endpoint; 401 without a token and for an invalid
one; 200 for a signed-in person; 401 for the service token of another group (the audience check);
with `--restricted-path`, 403 for a person of the wrong role; and, with `--page-path /app --group N`, that
a visitor who is not signed in is sent on to Keycloak's sign-in for your own client `group-N`. A check that cannot run is shown as
`SKIP`, never as passed. Exit status 0 means nothing failed.

## 7. Rules of the road

- The API of the Core Service only grows once groups start integrating: nothing is removed or renamed
  (`make schema` compares against `docs/openapi-baseline.yaml`). The reference is `/api/docs/`.
- Keep your service's tests independent of Keycloak: `gradian-testing` signs tokens for you.
- Never log tokens or passwords, and never put a secret in a repository.
