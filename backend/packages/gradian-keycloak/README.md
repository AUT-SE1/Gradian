# gradian-keycloak

Everything that talks to Keycloak over HTTP, for Django services of the Gradian platform:
the realm's signing keys, the access token of your own service, and the Admin API.

Most services only need the first two. If you validate tokens, you want
[`gradian-auth`](../gradian-auth/README.md), which builds on this package.

| Module | Use it to | Who needs it |
| --- | --- | --- |
| [`config`](#config) | Read where Keycloak is and which client you are | everyone (used by the others) |
| [`realm`](#realm) | Fetch the realm's public signing keys, check Keycloak is reachable | `gradian-auth`, health checks |
| [`service_token`](#service_token) | Get your own service's access token to call another service | group services that call Core |
| [`admin_client`](#admin_client) | Create users, change roles, enable or disable accounts | **Core only** |
| [`roles`](#roles) | The realm's role names | everyone |
| [`errors`](#errors) | `KeycloakError` | everyone |

## Install

The packages are not on PyPI. Install them together, from this repository:

    pip install /path/to/backend/packages/gradian-keycloak /path/to/backend/packages/gradian-auth

See [packages/README.md](../README.md) for Docker, for services in another repository, and for
development.

## Settings

Put these in your Django `settings.py`. They are read on every call.

| Setting | Required | Meaning |
| --- | --- | --- |
| `KEYCLOAK_PUBLIC_URL` | yes | The address browsers use, e.g. `http://localhost:8080`. It is the `iss` of every token. |
| `KEYCLOAK_URL` | yes | The address your container uses, e.g. `http://keycloak:8080`. The two differ and both are right (DEC-18). |
| `KEYCLOAK_CLIENT_ID` | yes | **Your service's own Keycloak client**, e.g. `group-3`. Tokens must name it in `aud`. |
| `KEYCLOAK_CLIENT_SECRET` | for `service_token`, `admin_client` and signing people in on your pages (`gradian_auth.oidc`) | The client's secret. Group secrets are in `build/credentials/services.csv` (`make users`). |
| `KEYCLOAK_REALM` | no | Default `gradian`. |
| `KEYCLOAK_TIMEOUT_SECONDS` | no | Default `5`. |

A missing required setting raises `ImproperlyConfigured` naming it. Never commit the secret: read it
from the environment.

## config

```python
from gradian_keycloak.config import get_config

config = get_config()
config.issuer  # http://localhost:8080/realms/gradian
config.jwks_url  # http://keycloak:8080/realms/gradian/protocol/openid-connect/certs
config.token_url  # .../protocol/openid-connect/token
config.admin_url  # http://keycloak:8080/admin/realms/gradian
config.client_id, config.client_secret, config.timeout
```

`get_config()` returns a frozen dataclass built from the settings above. The issuer comes from the
**public** address and the other URLs from the **internal** one.

## realm

```python
from gradian_keycloak.realm import check_reachable, fetch_jwks

fetch_jwks()  # the realm's public keys as a dict; raises KeycloakError on any failure
check_reachable()  # same call, for a readiness probe
```

You rarely call this yourself: `gradian-auth` caches the keys and refreshes them when needed.
In tests, patch `gradian_keycloak.realm.fetch_jwks` (see `gradian-testing`).

## service_token

Your service's own access token, for calling another service (client-credentials grant). It is
cached and renewed shortly before it expires, and is safe to share between threads.

```python
import requests
from django.conf import settings
from gradian_keycloak.service_token import ServiceTokenClient

tokens = ServiceTokenClient()  # one per process is enough


def core_user(sub: str) -> dict | None:
    response = requests.get(
        f"{settings.CORE_URL}/api/v1/internal/users/{sub}",  # CORE_URL = http://core:8000
        headers=tokens.auth_headers(),
        timeout=5,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
```

Core's `/api/v1/internal/users` and `/internal/users/{sub}` accept exactly this token (DES-REG-07).
The list endpoint is paginated: follow `next` until it is `null`.

Things that go wrong:

- `ImproperlyConfigured: Missing setting KEYCLOAK_CLIENT_SECRET`: set it.
- `KeycloakError: could not obtain a service token`: wrong secret, or Keycloak is down.
- Core answers 400 for a host name: add your caller's target name (`core`) to Core's
  `DJANGO_ALLOWED_HOSTS`.
- Core answers 403: the token has no `service` role. Group clients are generated with it; a client
  you created by hand needs it.

## admin_client

The Keycloak Admin API as Core uses it. **Only a client whose service account has the realm-management
roles can use it, which today is `gradian-core`. Group services must not call it.**

```python
from gradian_keycloak.admin_client import NewUser, get_admin_client

admin = get_admin_client()
sub = admin.create_user(
    NewUser(
        mobile="09000100001",
        email="a@x.test",
        first_name="علی",
        last_name="رضایی",
        password="...",
        role="student",
        consultant_type="",
    )
)
admin.set_panel_role(sub, "professor", "")  # makes it the only panel role
admin.set_enabled(sub, False)
admin.update_user(sub, {"email": "new@x.test"})
admin.grant_role(sub, "student")
admin.list_panel_users()  # every user with their panel roles
```

All methods raise `KeycloakError`; `error.status` is the HTTP status, or `None` if Keycloak could not
be reached. `create_user` removes the account again if the role cannot be assigned. Depend on the
`IdentityAdmin` protocol in type hints, and get the client through `get_admin_client()`, so tests can
replace it.

## roles

```python
from gradian_keycloak.roles import DEFAULT_PANEL, PANEL_ROLES, SERVICE_ROLE

PANEL_ROLES  # ("student", "consultant", "professor", "admin")
SERVICE_ROLE  # "service": machine clients
DEFAULT_PANEL  # "student": a person with no panel role
```

## errors

`KeycloakError(message, status=None)` is the only exception this package raises for a Keycloak
problem. It is not an HTTP error of yours: translate it (`gradian-auth` turns a key-fetch failure
into 502 `identity_provider_unavailable`).

## Tests

    python packages/run_tests.py gradian_keycloak.tests

Tested with Django 6.1.1 and requests 2.34.2.
