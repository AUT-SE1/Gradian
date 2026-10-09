# Frontend guide: sign-in and API

For the frontend team. It is the contract between the React app and the Core Service, kept next to the
backend that implements it. The OpenAPI schema is the source of truth for every field
(`http://localhost:8000/api/docs/`, raw at `/api/schema/`); this guide explains how to use it. If
the two disagree, the schema wins: tell the backend team.

**Status.** Every endpoint below exists, and so does the way into a group's service (section 6).
Sign-in, registration,
renewal and the calls in section 5 were checked in headless Chrome against a real Keycloak 26.0.8 and
Core, using `oidc-client-ts` 3.5.0, through `backend/dev-frontend` (`make dev-frontend`), which you can
use as a working example. The current `frontend/` code does not match it yet: see
[What to change](#what-to-change-in-the-current-frontend).

## 1. The picture

- **Keycloak** (`http://localhost:8080`) signs people in on its own themed pages and issues access
  tokens. Your app never sees a password and has no login endpoint to call.
- **Core Service** (`http://localhost:8000`) is the API. Every endpoint is under `/api/v1/`, speaks
  UTF-8 JSON, and takes `Authorization: Bearer <access token>`.
- **Group services** (ports 8001 to 8010) are opened by redirect and sign the person in themselves
  (section 6). If your app calls one's API, send the same `Authorization` header.

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

Tokens last **10 minutes**. `automaticSilentRenew` renews them in the background with the refresh
token, about a minute before they expire; the Keycloak session lasts up to 30 days if the person ticked
*remember me* on the login page. This was verified: with the lifetime lowered to 70 seconds, the page
renewed every 10 seconds for minutes and every call kept working. `userStore` above uses
`localStorage` so a reload keeps the session; that is readable by any script on the page, so keep the
app free of untrusted scripts.

**Do not call `getUser()` on a timer or in a render loop** (for example to show a countdown). Each call
re-arms the library's expiry timers from the time remaining, and inside the last minute that means
"fire in one second" every time, so the renewal keeps being postponed and never happens: the session
silently dies although the app still believes it is signed in. This happened in the first version of
the tester page. Call `getUser()` once per API request (as `authedClient.ts` does), and for a
countdown keep the user object in memory and read its `expires_at`. Use the library's events
(`addUserLoaded`, `addSilentRenewError`, `addUserUnloaded`) to keep your state in step.

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

### Landing page and panel content

These return the display content of the designed pages. The values are Persian demo content that the
backend team can change without a release, so render what you receive and do not hard-code it.

```ts
export type Link = { label: string; href: string };

export type Landing = {
  navbar: { brand: string; links: Link[]; login_label: string; register_label: string } | null;
  hero: {
    eyebrow: string; title: string; subtitle: string;
    primary_cta_label: string; secondary_cta_label: string; image_url: string;
  } | null;
  statistics: { key: string; value: string; label: string }[] | null;
  missions: { title: string; description: string; icon: string }[] | null;
  teachers: { name: string; title: string; bio: string; avatar_url: string }[] | null;
  rankers: { name: string; rank: string; field: string; quote: string; avatar_url: string }[] | null;
  testimonials: { name: string; role: string; text: string; avatar_url: string }[] | null;
  footer: { description: string; links: Link[]; copyright: string } | null;
};

export type Countdown = {
  date: string;                       // the Konkur day, YYYY-MM-DD
  state: 'upcoming' | 'today' | 'past';
  days_remaining: number;             // 0 on the day and after it
  label: string;                      // Persian text, e.g. "۱۲۰ روز تا کنکور"
};

export type PanelHeader = {
  full_name: string;
  avatar_url: string;
  consultant_type: 'consultant' | 'top_ranker' | null;
  field_of_study: string | null;      // students only; "" until chosen; null in other panels
  field_of_study_label: string | null; // Persian, e.g. "ریاضی و فیزیک"
};

export type PanelInfo = { panel: PanelRole; home_path: string; header: PanelHeader; countdown: Countdown };

export type ServiceEntry = {
  key: string;                         // stable id, e.g. "student.simulated-exam"
  title_fa: string; title_en: string; description: string; button_label: string;
  icon: string; order: number;
  status: 'available' | 'unavailable';
  mode: 'embed' | 'redirect';
  url: string | null;                  // null while unavailable
};

export type Dashboard = {
  welcome: { message: string; tip: string } | null;
  countdown: Countdown;
  study_streak: {
    current_days: number; best_days: number; message: string; week: { day: string; done: boolean }[];
  } | null;
  experience_feed: {
    id: number; author: string; author_title: string; title: string; excerpt: string;
    likes: number; comments: number;
  }[] | null;
};

export type NotificationList = {
  unread_count: number; count: number; next: string | null; previous: string | null;
  results: { id: number; title: string; body: string; created_at: string; is_read: boolean }[];
};
```

A section that someone removed on the backend arrives as `null`: show nothing for it, do not fail.

**`GET /landing`**: public, rate-limited like `/auth/config` (cache it). Returns a `Landing`. Use
`navbar.login_label` and `register_label` for the two buttons that call `login()` and `register()`.

**`GET /panel`**: any signed-in person. Returns a `PanelInfo`: the full name for the panel header, the
field of study (students only), and the countdown for the sidebar.

**`GET /panel/services`**: any signed-in person. The services of the caller's own panel, in display
order, in the usual list envelope (`count`, `next`, `previous`, `results`). The student panel has 10
entries, consultant 6, professor 6 and admin 3.

```json
{"count": 10, "next": null, "previous": null, "results": [
  {"key": "student.simulated-exam", "title_fa": "آزمون شبیه‌ساز کنکور", "title_en": "Simulated Konkur exam",
   "description": "شرکت در آزمون‌های جامع شبیه‌ساز کنکور با شرایط و زمان‌بندی واقعی و دریافت کارنامه.",
   "button_label": "ورود به سرویس", "icon": "exam", "order": 1,
   "status": "unavailable", "mode": "embed", "url": null}
]}
```

An entry whose group has not connected its service yet has `status: "unavailable"` and `url: null`:
draw it greyed out with no link; the panel must still load. For an `available` entry, `mode: "redirect"`
means go to `url` (see section 6; this is the mode groups use) and `mode: "embed"` is not in use.
Use `order` as given.

**`GET /student/dashboard`**: students only (403 for every other panel). Returns a `Dashboard`: the
welcome message already filled in with the student's first name, the countdown, the study streak and
a preview of the experience feed. The streak and the feed are demo content for now.

**`GET /notifications`**: any signed-in person. The bell. `unread_count` is the number of unread
notifications across all pages; `results` is paginated with `limit` and `offset`, newest first. It is
empty until someone creates notifications on the backend, and there is no call to mark one read yet:
the bell is display-only.

### Not for the browser

`/api/v1/internal/*` is for group services only and answers 403 to a person. `/health/live`,
`/health/ready` and `/admin/` (Django's own admin) are operations, not API.

## 6. Opening a group's service

Each entry in `GET /panel/services` points at a service built by a project group. **Groups use
`redirect`**: to open an `available` entry, navigate the browser to its `url`:

```ts
function openService(entry: ServiceEntry) {
  if (entry.status === 'available' && entry.url) window.location.assign(entry.url);
}
```

That is all. **Do not put the access token in the URL or hand it to the page.** The person is already
signed in at Keycloak, so the group's page signs them in itself by single sign-on and shows them
straight away, with no second login. The group's page links back to the person's panel
(`/student`, `/professor`, ...) and has its own sign-out, so your app needs no extra route for it.

If the person's Keycloak session has ended (for example they signed out elsewhere), the group's page
sends them to the Keycloak login page like any other visit, and they come back to the group's page
after signing in.

Treat `embed` as not in use: an iframe cannot be given the person's identity this way. Show an `embed`
entry like a `redirect` one until the TA decides otherwise.

Calling a group service's **API** from your own pages also works: send the same
`Authorization: Bearer` header and the service validates the token itself.

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
- **A working example**: `make dev-frontend` serves `backend/dev-frontend/` on `localhost:5173`: sign
  in, register, renew, call each endpoint and watch the token events. Its `public/app.js` is short
  enough to read in one sitting.
- **Run the stack**: `make start` in `backend/`. After changing `FRONTEND_URL` run `make reset`,
  because Keycloak reads it only when it first imports the realm.

## What to change in the current frontend

1. Remove `authApi.login` and the form that posts `{mobile, password}` to `/auth/login/`: that
   endpoint does not exist and will not. `LoginPage` becomes the landing buttons calling `login()` and
   `register()`.
2. Add the `/auth/callback` route (section 2), and `AuthProvider` holding the `Me` object from
   `GET /me`, loaded after sign-in and again on a page reload when `signIn.getUser()` returns a user.
3. Set `VITE_API_BASE_URL=/api/v1` in `.env.example` (it says `http://localhost:8000/api`), and
   drop trailing slashes from paths.
4. Route by `panel` and `home_path`; rename the `/instructor` and `/counsellor` routes to `/professor`
   and `/consultant`, or redirect them.
5. Build the 401 and 403 states of section 4 into the route guard and `httpClient`.
6. Replace `AuthSession`, `AuthUser` and `LoginPayload` in `shared/types/auth.ts` with `Me`.
7. Replace the static landing page and panel menus with `GET /landing`, `GET /panel` and
   `GET /panel/services`, and the dashboard widgets with `GET /student/dashboard` (section 5).
8. Production: decide between an absolute `VITE_API_BASE_URL` and an `/api` proxy in `nginx.conf`.

I did not change any frontend file.
