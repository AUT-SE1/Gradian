# Frontend guide: sign-in and API

For the frontend team. It is the contract between the React app and the Core Service, kept next to the
backend that implements it. The OpenAPI schema is the source of truth for every field
(`http://localhost:8000/api/docs/`, raw at `/api/schema/`); this guide explains how to use it. If
the two disagree, the schema wins: tell the backend team.

**Status.** Everything below exists and is tested, except the section "Not available yet". The
current `frontend/` code does not match it yet: see [What to change](#what-to-change-in-the-current-frontend).

## 1. The picture

- **Keycloak** (`http://localhost:8080`) signs people in on its own themed pages and issues access
  tokens. Your app never sees a password and has no login endpoint to call.
- **Core Service** (`http://localhost:8000`) is the API. Every endpoint is under `/api/v1/`, speaks
  UTF-8 JSON, and takes `Authorization: Bearer <access token>`.
- **Group services** (ports 8001 to 8010) validate the same token themselves. When a panel embeds
  or calls one, send the same header.

```
browser --PKCE--> Keycloak --code--> browser --token--> Core /api/v1/me --> {panel, home_path, ...}
```

Base URL: use **`/api/v1`**, relative, with **no trailing slashes** (`/me`, not `/me/`). In
development the Vite dev server proxies `/api` to the backend, so set `VITE_API_BASE_URL=/api/v1`. The
production container serves static files only (`nginx.conf` has no `/api` proxy), so a production
build needs an absolute `VITE_API_BASE_URL` (for example `https://core.example/api/v1`) or a proxy in
front. Core allows cross-origin calls from `FRONTEND_URL` only.

## 2. Sign-in (Authorization Code with PKCE)

Use `oidc-client-ts` (`npm i oidc-client-ts`). It does the code exchange, PKCE, token renewal and
logout. Read `GET /api/v1/auth/config` once and build everything from it. It is public and
rate-limited (60 requests a minute per address by default), so do not call it on every render.

```json
{
  "issuer": "http://localhost:8080/realms/gradian",
  "realm": "gradian",
  "client_id": "gradian-web",
  "registration_endpoint": "http://localhost:8080/realms/gradian/protocol/openid-connect/registrations",
  "end_session_url": "http://localhost:8080/realms/gradian/protocol/openid-connect/logout",
  "landing_url": "http://localhost:5173/"
}
```

Types used in this guide (`src/features/auth/authTypes.ts`):

```ts
export type AuthConfig = {
  issuer: string;
  realm: string;
  client_id: string;
  registration_endpoint: string;
  end_session_url: string;
  landing_url: string;
};

export type PanelRole = 'student' | 'consultant' | 'professor' | 'admin';

export type Me = {
  sub: string;
  mobile: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: PanelRole;
  consultant_type: '' | 'consultant' | 'top_ranker';
  panel: PanelRole;
  home_path: string;
  field_of_study: '' | 'experimental' | 'mathematics' | 'humanities';
  avatar_url: string;
  bio: string;
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};
```

The two user managers (`src/features/auth/oidc.ts`). Sign-up uses the same settings but starts at the
registration endpoint, because Keycloak 26.0.8 ignores `prompt=create`:

```ts
import { UserManager, WebStorageStateStore } from 'oidc-client-ts';
import { httpClient } from '@/shared/api/httpClient';
import type { AuthConfig } from './authTypes';

let managers: Promise<{ signIn: UserManager; signUp: UserManager }> | null = null;

export function getManagers() {
  managers ??= (async () => {
    const config = await httpClient.get<AuthConfig>('/auth/config');
    const settings = {
      authority: config.issuer,
      client_id: config.client_id,
      redirect_uri: `${window.location.origin}/auth/callback`,
      post_logout_redirect_uri: config.landing_url,
      response_type: 'code',
      scope: 'openid',
      automaticSilentRenew: true,
      userStore: new WebStorageStateStore({ store: window.localStorage }),
    };
    const signIn = new UserManager(settings);
    const metadata = await signIn.metadataService.getMetadata();
    const signUp = new UserManager({
      ...settings,
      metadata: { ...metadata, authorization_endpoint: config.registration_endpoint },
    });
    return { signIn, signUp };
  })().catch((error: unknown) => {
    managers = null; // do not cache a failure, so the next call tries again
    throw error;
  });
  return managers;
}

export const login = async () => (await getManagers()).signIn.signinRedirect();
export const register = async () => (await getManagers()).signUp.signinRedirect();
export const logout = async () => (await getManagers()).signIn.signoutRedirect();
```

Routes you need:

- **Landing page**: a *ورود* button that calls `login()` and a *ثبت‌نام* button that calls `register()`.
- **`/auth/callback`**: calls `finishSignIn()` and then navigates to `me.home_path`. This exact path
  is registered in Keycloak (`${FRONTEND_URL}/auth/callback`); a different path is refused.

```ts
import { httpClient } from '@/shared/api/httpClient';
import { getManagers } from './oidc';
import type { Me } from './authTypes';

export async function finishSignIn(): Promise<Me> {
  const { signIn } = await getManagers();
  const user = await signIn.signinRedirectCallback();
  const me = await httpClient.get<Me>('/me', {
    headers: { Authorization: `Bearer ${user.access_token}` },
  });
  return me;
}
```

- **Logout**: call `logout()`. It ends the Keycloak session and returns to `landing_url`.

The look of the login and registration pages is a Keycloak theme, not React: see
`backend/keycloak/themes/gradian/README.md`. Their field rules (mobile `09` plus 9 digits, password of
at least 8 characters, Persian errors) are enforced there; do not repeat them in the app.

### Calling the API with the token

Wrap `httpClient` so that every call carries the current token, and so that errors can be read
(`src/shared/api/authedClient.ts`):

```ts
import { getManagers } from '@/features/auth/oidc';
import { ApiError } from './ApiError';
import { httpClient } from './httpClient';
import type { ApiErrorBody } from '@/features/auth/authTypes';

async function authHeader(): Promise<HeadersInit> {
  const { signIn } = await getManagers();
  const user = await signIn.getUser();
  return user && !user.expired ? { Authorization: `Bearer ${user.access_token}` } : {};
}

export const api = {
  get: async <T>(path: string) => httpClient.get<T>(path, { headers: await authHeader() }),
  patch: async <T>(path: string, body: unknown) =>
    httpClient.patch<T>(path, body, { headers: await authHeader() }),
  post: async <T>(path: string, body: unknown) =>
    httpClient.post<T>(path, body, { headers: await authHeader() }),
};

export function errorBody(error: unknown): ApiErrorBody | null {
  if (!(error instanceof ApiError)) return null;
  const p = error.payload as Partial<ApiErrorBody> | null;
  return p && typeof p.code === 'string' ? (p as ApiErrorBody) : null;
}
```

Tokens last **10 minutes**. `automaticSilentRenew` renews them in the background; the Keycloak session
lasts up to 30 days if the person ticked *remember me* on the login page. I could not test renewal in
a real browser: check once that a session survives past 10 minutes and a reload. `userStore` above
uses `localStorage` so a reload keeps the session; that is readable by any script on the page, so
keep the app free of untrusted scripts.

## 3. Roles and routing

`GET /api/v1/me` returns `panel` and `home_path`. **Route by those, not by your own role names.**

| `panel` | `home_path` | Who |
| --- | --- | --- |
| `student` | `/student` | students, and everyone who has just registered |
| `consultant` | `/consultant` | consultants and top-rankers (`consultant_type` is `consultant` or `top_ranker`) |
| `professor` | `/professor` | professors |
| `admin` | `/admin` | administrators |

The current frontend uses `instructor` and `counsellor` for the last two. Keep those as display
labels if you like, but the routes and the values you compare against are `professor` and
`consultant`. A person has exactly one panel. Roles are enforced by the server: hiding a menu entry is
for comfort, the API answers 403 anyway.

## 4. Errors

Every error, from every endpoint, has one shape, and `code` is a stable English string:

```json
{"code": "invalid_token", "message": "نشانه ورود نامعتبر یا منقضی است. دوباره وارد شوید.", "details": {}}
```

Branch on `code` (and the HTTP status), never on `message`. `message` is Persian: show it as a fallback,
and map `code` to your own i18n strings for English.

| Status | `code` | Meaning | What the app does |
| --- | --- | --- | --- |
| 401 | `not_authenticated` | no token sent | start sign-in |
| 401 | `invalid_token` | expired, tampered, or meant for another service | try one silent renew, then start sign-in |
| 403 | `permission_denied` | signed in, wrong panel for this endpoint | show a "no access" state |
| 403 | `ambiguous_role` | the account has more than one panel role | show a "contact support" state |
| 403 | `account_disabled` | an administrator disabled the account | show it, and sign out |
| 403 | `incomplete_identity` | the account misses a required field; `details.fields` names them | "contact support" |
| 403 | `self_modification_forbidden` | an admin changed their own role or status | show a message |
| 400 | `validation_error` | `details` maps each bad field to a list of problems | show them under the fields |
| 400 | `parse_error` | the body is not valid JSON | a bug in the app |
| 404 | `not_found` | no such resource | "not found" state |
| 409 | `identity_conflict` | the email or mobile number belongs to another account | show it on the field |
| 429 | `throttled` | too many requests; `details.retry_after_seconds` | wait, then retry |
| 502 | `identity_provider_unavailable` | Keycloak is unreachable | "try again later" |
| 500 | `server_error` | unexpected | "try again later" |

401 and 403 are different states in the UI: 401 means *sign in*, 403 means *you are signed in but may
not*. The existing `ApiError` class keeps the body in `payload`; `errorBody()` above reads it.

## 5. Endpoints

All paths are under `/api/v1`. "Panel" means the caller's panel. Example values are illustrative.

### `GET /auth/config`: public

See section 2. Cache it for the page's lifetime.

### `GET /me`: any signed-in person

The profile is created on the first call and refreshed from the token's claims, so call it right after
sign-in.

```json
{
  "sub": "5d0e0f7e-2f3c-5a49-a0f2-2f9b5a1f7c11",
  "mobile": "09001000001", "email": "student.1@gradian.test",
  "first_name": "علی", "last_name": "رضایی", "full_name": "علی رضایی",
  "role": "student", "panel": "student", "home_path": "/student",
  "consultant_type": "", "field_of_study": "experimental", "avatar_url": "", "bio": ""
}
```

Errors: 401, 403 (`ambiguous_role`, `account_disabled`, `incomplete_identity`), 409, 502.

### `PATCH /me`: any signed-in person

Send only what changed. Allowed fields: `email`, `first_name`, `last_name`, `field_of_study`
(`experimental`, `mathematics`, `humanities`), `avatar_url`, `bio` (500 characters at most). The mobile
number and role cannot be changed. An empty body is 400. Names and email are written to Keycloak first:
if that fails you get 502 and nothing is saved.

```http
PATCH /api/v1/me
Content-Type: application/json

{"first_name": "محمد", "field_of_study": "mathematics"}
```

The answer is the full profile, same as `GET /me`: **use it to update your state**. The token you hold
still carries the old name until it is renewed, so never read names from the token.
A new registrant has no `field_of_study`; collect it here if the design needs it.

### Administrator endpoints: panel `admin` only

All answer 401 without a token and 403 `permission_denied` to a signed-in person of another panel.

**`GET /admin/users`** lists accounts, paginated. Query: `role`, `is_active` (`true`/`false`), `q`
(part of the mobile number, email or name), `limit` (default 50, at most 200), `offset`.

```json
{"count": 61, "next": "http://localhost:8000/api/v1/admin/users?limit=50&offset=50",
 "previous": null, "results": [ /* accounts, same fields as /me plus "is_active" */ ]}
```

The list is not an array: read `results`. (Until this version the OpenAPI schema wrongly described it
as a single object; regenerate your types if you generated them.)

**`POST /admin/users`** creates an account that can sign in at once. Required: `mobile`, `email`,
`first_name`, `last_name`, `password` (8 to 128 characters, never returned), `role`
(`student`, `consultant`, `professor`, `admin`). `consultant_type` is required for role `consultant`
and not allowed for others. Optional: `field_of_study`. Answers 201 with the account. Mobile numbers
may be written with Persian digits or `+98`; the answer has the normalized `09...` form. 409
`identity_conflict` if the mobile or email exists.

**`GET /admin/users/{sub}`** one account. 404 `not_found` if unknown.

**`PATCH /admin/users/{sub}`** changes `email`, `first_name`, `last_name`, `role`, `consultant_type`,
`is_active`, `field_of_study`. A new `role` replaces the old one. `is_active: false` blocks sign-in.
An administrator cannot change their own `role`, `consultant_type` or `is_active` (403
`self_modification_forbidden`). **A role change reaches a token that was already issued only when it
expires, at most 10 minutes later;** the person sees the new panel after the next renewal or sign-in.

### Not for the browser

`/api/v1/internal/*` is for group services only and answers 403 to a person. `/health/live`,
`/health/ready` and `/admin/` (Django's own admin) are operations, not API.

## 6. Not available yet

Planned for the next backend step (see `02-design.md`, section 6.2), so **do not build against them
yet**: `GET /landing`, `GET /panel`, `GET /panel/services` (the service entries and how to open each:
embed or redirect), `GET /student/dashboard`, `GET /notifications`. Until then the landing page and the
panel menus are static in the frontend. When they land, this guide gets their section.

## 7. Trying it without writing code

- **Swagger UI** at `http://localhost:8000/api/docs/`: press *Authorize*, choose `keycloakPassword`,
  enter a mobile number and its password. Development only.
- **Seeded users**: `make users` (in `backend/`) writes `build/credentials/users.csv` with role,
  name, mobile and password. The first student is `09001000001`, the first admin `09005000001`; the
  password is `SEED_DEFAULT_PASSWORD` from `backend/.env`.
- **A token from the command line** (development only; this client does not exist in production):

      curl -s -d grant_type=password -d client_id=gradian-test \
        -d username=09001000001 --data-urlencode password=<SEED_DEFAULT_PASSWORD> \
        http://localhost:8080/realms/gradian/protocol/openid-connect/token

  then `curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/me`.
- **Run the stack**: `make start` in `backend/`. After changing `FRONTEND_URL` run `make reset`,
  because Keycloak reads it only when it first imports the realm.

