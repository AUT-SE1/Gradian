# gradian-auth

Decide who is calling your Django service. It validates the Keycloak access token, turns it into a
**principal** (a signed-in person, or a platform service), and gives you the access rules for your
views. It works with plain Django views and with Django REST Framework.

This is what DES-REG-05 asks of every group service: accept the Keycloak token as a Bearer token,
validate signature, issuer, expiry and that `aud` contains **your own client id**, identify people
by `sub`, authorize by role.

| Module | Use it to |
| --- | --- |
| [`middleware`](#middleware-and-decorators-plain-django) | Authenticate every request of a plain Django service |
| [`decorators`](#middleware-and-decorators-plain-django) | `@require_user(...)`, `@require_service` on plain views |
| [`drf`](#drf) | Authentication class, permission classes and error handler for DRF |
| [`principals`](#principals) | The caller: `UserPrincipal` or `ServicePrincipal` |
| [`claims`](#claims) | Token claims to an `Identity`, role extraction, name validation |
| [`roles`](#roles) | Resolve the single panel role; home paths |
| [`tokens`](#tokens-and-jwks) | `validate_token`: signature, issuer, expiry, audience |
| [`jwks`](#tokens-and-jwks) | The signing-key cache |
| [`authenticate`](#authenticate-and-the-principal-builder) | Header to caller; swap how the principal is built |
| [`errors`](#errors) | One error shape `{code, message, details}`; your own error codes |
| [`mobile`](#mobile) | Normalize an Iranian mobile number |
| [`context`](#context) | Who the current request is for, for log lines |

## Install

Install it together with `gradian-keycloak` (neither is on PyPI):

    pip install /path/to/backend/packages/gradian-keycloak "/path/to/backend/packages/gradian-auth[drf]"

Leave out `[drf]` if you do not use Django REST Framework. See [packages/README.md](../README.md)
for Docker and for services in another repository.

## Settings

Everything in the [gradian-keycloak settings](../gradian-keycloak/README.md#settings), above all
`KEYCLOAK_PUBLIC_URL`, `KEYCLOAK_URL` and `KEYCLOAK_CLIENT_ID`. Tokens are accepted only if `aud`
contains `KEYCLOAK_CLIENT_ID`. Users' tokens carry the audience of every group (DEC-20), so
a token meant for group 4 is refused by group 3.

| Setting | Default | Meaning |
| --- | --- | --- |
| `GRADIAN_PUBLIC_PATHS` | `("/health",)` | Plain-Django middleware only: path prefixes that are never authenticated |
| `GRADIAN_PRINCIPAL_BUILDER` | `gradian_auth.principals.build_principal` | Dotted path of a function from claims to principal; Core replaces it |

## Quickstart: plain Django

```python
# settings.py
MIDDLEWARE = [
    # ...
    "gradian_auth.middleware.KeycloakAuthMiddleware",
]
KEYCLOAK_PUBLIC_URL = os.environ["KEYCLOAK_PUBLIC_URL"]
KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
KEYCLOAK_CLIENT_ID = "group-3"
```

```python
# views.py
from django.http import JsonResponse
from gradian_auth.decorators import current_principal, require_service, require_user


@require_user("student")  # a person whose panel is student
def my_exams(request):
    principal = current_principal(request)
    return JsonResponse({"sub": principal.sub, "name": principal.identity.first_name})


@require_user()  # any signed-in person
def me(request): ...


@require_service  # another service, with a client-credentials token
def sync(request): ...
```

`/health` needs no token. Run `python manage.py check`, then call your service with
`Authorization: Bearer <access token>` (get one as described in the
[backend README](../../README.md)): without a token you get 401, with another role 403.

## Quickstart: Django REST Framework

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["gradian_auth.drf.KeycloakBearerAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "gradian_auth.drf.exception_handler",
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}
```

```python
from gradian_auth.drf import HasPanelRole, IsPanelUser, IsPlatformService


class Professors(HasPanelRole):
    allowed_roles = ("professor", "admin")


class Exams(APIView):
    permission_classes = (Professors,)

    def get(self, request):
        return Response({"sub": request.user.sub})  # request.user is the principal
```

`UNAUTHENTICATED_USER: None` keeps DRF from needing `django.contrib.auth`.

## middleware and decorators (plain Django)

`KeycloakAuthMiddleware` sets `request.principal` (the caller, or `None`) and `request.claims`.

- No `Authorization` header, or another scheme: anonymous. The decorators decide.
- A bad token (wrong signature, issuer, audience, expired, malformed): answered **401
  `invalid_token`** immediately.
- A valid token with an unusable identity: 403 `incomplete_identity` or `ambiguous_role`.
- Keycloak unreachable and no cached keys: 502 `identity_provider_unavailable`.
- Paths in `GRADIAN_PUBLIC_PATHS` skip authentication altogether. A prefix matches whole path
  segments (`/health` matches `/health/deep`, not `/healthy`).

Decorators (they need the middleware; without it every view stays closed):

| Decorator | Allows | Otherwise |
| --- | --- | --- |
| `@require_user("a", "b")` | a person with panel `a` or `b` | 401 `not_authenticated`, or 403 `permission_denied` |
| `@require_user()` | any signed-in person | same |
| `@require_service` | a platform service (client-credentials token) | same |

`require_user` needs the parentheses; `@require_user` alone raises `TypeError` at import. Decorators
are for synchronous function views; for class-based views use `method_decorator`. `current_principal(request)`
returns the principal or `None`.

## drf

| Name | What it does |
| --- | --- |
| `KeycloakBearerAuthentication` | Validates the token; `request.user` is the principal, `request.auth` the claims |
| `IsPanelUser` | Any signed-in person |
| `HasPanelRole` | Subclass and set `allowed_roles = ("professor",)` |
| `IsPlatformService` | A service with the `service` role |
| `exception_handler` | Every error as `{code, message, details}`; our errors keep their status |

Errors that DRF raises (validation, 404, throttling, parse errors) get stable English codes and
Persian messages too. Your own `ApiError` subclasses roll back an `ATOMIC_REQUESTS` transaction like
DRF's own errors do.

## principals

```python
from gradian_auth.principals import ServicePrincipal, UserPrincipal

principal.sub  # str, the Keycloak user id; the key for your own data
principal.is_authenticated  # always True
# UserPrincipal
principal.panel  # "student" | "consultant" | "professor" | "admin"
principal.identity  # Identity: sub (UUID), mobile, email, first_name, last_name, role, consultant_type
# ServicePrincipal
principal.client_id  # the calling client, from the token's `azp`, e.g. "group-3"
```

**Identify people by `principal.sub` and authorize by `principal.panel`, never from a request body or
query string, and keep no editable copy of identity fields** (DES-REG-05). Ask Core for the rest
(see [service_token](../gradian-keycloak/README.md#service_token)).

## claims

`identity_from_claims(claims, role)` builds an `Identity` from a token's claims or raises 403
`incomplete_identity` with `details.fields` naming what is wrong. `extract_roles(claims)` reads
`realm_access.roles`; `is_valid_name(text)` checks a name (letters, spaces, ZWNJ, 1 to 100).
You normally get all of this through the principal.

## roles

`resolve_panel(roles)` returns the single panel role, ignoring others such as `offline_access`; no
panel role means `student`; two raise 403 `ambiguous_role`. `HOME_PATHS` maps a role to
`/student`, `/consultant`, ... Role changes reach a token that is already issued only when it
expires (at most 10 minutes).

## tokens and jwks

```python
from gradian_auth.tokens import validate_token

claims = validate_token(token)  # audience = KEYCLOAK_CLIENT_ID
claims = validate_token(token, audience="group-7")  # another audience
```

Only RS256 is accepted (no `alg: none`, no HS256). `exp`, `iss`, `aud` and `sub` are required. The
key cache fetches keys on first use, refreshes when a token names an unknown `kid` (at most once per
10 seconds, so random `kid`s cannot cause a fetch storm), and keeps working from cached keys when
Keycloak is briefly down.

## authenticate and the principal builder

`parse_bearer(header_bytes)` and `authenticate_token(token)` are the two steps both adapters use; call
them to support another framework. How claims become a principal is replaceable:

```python
# settings.py
GRADIAN_PRINCIPAL_BUILDER = "myservice.auth.build_principal"

# myservice/auth.py
from gradian_auth.principals import build_principal as token_principal


def build_principal(claims):
    principal = token_principal(claims)  # validates roles and identity
    # e.g. create your own row for a first-time user, refuse a banned one
    return principal
```

Core uses this to keep its `Profile` cache and return a subclass of `UserPrincipal` with a `profile`
field. A principal must be a `UserPrincipal` or `ServicePrincipal` (a subclass is fine).

## errors

Every error has the body `{"code": "invalid_token", "message": "<Persian>", "details": {}}` with a
stable English `code`. Shared codes: `not_authenticated`, `invalid_token`, `permission_denied`,
`ambiguous_role`, `incomplete_identity`, `identity_provider_unavailable`, plus DRF's
`validation_error`, `not_found`, `throttled`, ... Add your own:

```python
from gradian_auth.errors import ApiError, register_messages

register_messages({"exam_closed": "این آزمون بسته شده است."})


class ExamClosedError(ApiError):
    status_code = 409
    default_code = "exam_closed"


raise ExamClosedError(details={"exam": 12})
```

Registering the same text twice is harmless; a different text for an existing code raises
`ValueError`. In plain Django, `gradian_auth.middleware.error_response(exc)` renders an `ApiError`.

## mobile

`normalize_mobile("+98 912...")` returns `09XXXXXXXXX` (Persian and Arabic digits, `+98` and `0098`
accepted) or raises `InvalidMobileError`. The mobile number is the username.

## context

`gradian_auth.context.user_sub` is a `ContextVar` set to the caller's `sub` after authentication, for
log lines. The plain-Django middleware resets it after each request. With DRF nothing resets it, so
add a middleware that does (Core's `RequestContextMiddleware` is an example) if you log it.

## Testing your views

Use [`gradian-testing`](../gradian-testing/README.md): it makes signed tokens and fakes Keycloak's
keys, so your tests need no running Keycloak.

## Gotchas

- Tokens last 10 minutes. The frontend renews them; a 401 means get a new one.
- Authenticate every path except health. A forgotten decorator on a plain-Django view means anyone
  with a valid token can call it; prefer `@require_user()` on everything.
- Service tokens (`aud` has only `gradian-core`) are refused by group services. That is intended.
- Browsers calling your service from the frontend need CORS: install `django-cors-headers` and allow
  the frontend origin; this package does not do it.

## Tests

    python packages/run_tests.py gradian_auth.tests

Tested with Django 6.1.1, Django REST Framework 3.18.1 and PyJWT 2.15.0.
