# Gradian Core Service - Decision Log

Draft · 2026-10-04

Part of a four-document set: [01 Requirements](01-requirements.md) · [02 Design](02-design.md) · **03 Decision log** (this document) · [04 Test plan](04-test-plan.md).

A decision records a tool or approach chosen to realise a design requirement. It is not a requirement: if a better option appears, the decision changes and the requirements above it stay valid.

## How to read an entry

| Field | Meaning |
| --- | --- |
| **Status** | **Mandated**: imposed by the TA. **Chosen**: decided with the TA's direction. **Proposed**: suggested here, no objection yet. **Assumed**: depends on an open question in 01 section 6.1 and must be confirmed. |
| **Realizes** | The design items (`DES-`) this decision serves |
| **Alternatives** | Options that were weighed |
| **Consequences** | What this commits the project to |

## Index

| ID | Decision | Status |
| --- | --- | --- |
| DEC-01 | Django and Django REST Framework for the Core Service | Mandated |
| DEC-02 | Keycloak with OpenID Connect for identity | Mandated |
| DEC-03 | PostgreSQL for the Core database | Proposed |
| DEC-04 | Docker Compose with a Makefile for local operation | Chosen |
| DEC-05 | Login on a Keycloak-hosted themed page | Assumed (Q1) |
| DEC-06 | Stateless bearer-token API validated locally | Proposed |
| DEC-07 | Local profile cache keyed by `sub`, refreshed from token claims | Proposed |
| DEC-08 | Identity edits written through to Keycloak first | Proposed |
| DEC-09 | Panel chosen from a single realm role; top-ranker as consultant attribute | Proposed |
| DEC-10 | Service registry in the database, embed or redirect per entry | Proposed |
| DEC-11 | Seeding by realm import plus Django fixtures, generated from one source | Chosen |
| DEC-12 | Deterministic IDs derived from the mobile number | Proposed |
| DEC-13 | Django's test runner with an `integration` tag | Chosen |
| DEC-14 | Project groups as Core tables with many-to-many membership | Assumed (Q2, Q3) |
| DEC-15 | API and platform conventions | Proposed |
| DEC-16 | ruff and strict mypy for code quality | Chosen |

## Decisions

### DEC-01 Django and Django REST Framework

- **Status:** Mandated (CON-01).
- **Realizes:** DES-ARC-01.
- **Decision:** The Core Service is a Django project; the REST API uses Django REST Framework; the Django admin is used for operator tasks such as editing service entries.
- **Alternatives:** none, since the framework is imposed.
- **Consequences:** Python and Django versions are pinned in the dependency file and must be agreed with the course environment. The admin comes for free but must not be able to edit identity fields (DES-ID-01).

### DEC-02 Keycloak with OpenID Connect

- **Status:** Mandated (CON-02, CON-03).
- **Realizes:** DES-ARC-01, DES-IDP-01, DES-IDP-02, DES-IDP-04 to DES-IDP-07.
- **Decision:** Keycloak is the only place where credentials and identity attributes live. Mobile number is the username. Email, first name and last name are required profile attributes.
- **Alternatives:** Django's own user model and sessions (rejected: cannot give single sign-on to separate group projects).
- **Consequences:** Every service trusts Keycloak-issued tokens. Keycloak is another container to run and another configuration to version, which is why the realm is committed as a template.
- **Implementation note (step 1):** DES-IDP-04 says a scope adds `gradian-core` to the token audience. The realm template attaches the audience mapper (and the `consultant_type` mapper) to the `gradian-web` client instead of defining a custom client scope, because a custom scope would mean the realm file also has to define Keycloak's built-in `profile`, `email` and `roles` scopes. The tokens are identical. This was written without a running Keycloak, so verify the import against Keycloak 26.0 early (also the service-account roles for the Admin API and the `briefRepresentation` parameter used by `sync_keycloak_users`); switch to a scope if the TA prefers one.

### DEC-03 PostgreSQL

- **Status:** Proposed.
- **Realizes:** DES-ARC-01, DES-OPS-01.
- **Decision:** The Core database is PostgreSQL, run as a Compose service.
- **Alternatives:** SQLite (simplest, but differs from a real deployment and handles concurrent access from several containers poorly).
- **Consequences:** The database is one more container. Table-level design is deferred to the Database Requirements document.

### DEC-04 Docker Compose with a Makefile

- **Status:** Chosen (Makefile by the TA; Compose proposed).
- **Realizes:** DES-OPS-01 to DES-OPS-05, DES-XC-04.
- **Decision:** Docker Compose runs the stack. A Makefile is the single interface for local operation. The Makefile only orders steps; the logic lives in scripts and `manage.py` commands.
- **Alternatives:** `just` or a task runner (nicer syntax but another install); plain scripts (no discoverable interface); running everything by hand (error-prone for 20 teams).
- **Consequences:** Make is not installed by default on Windows, so the underlying commands must stay runnable without it (DES-OPS-05). Targets are documented through `make help`.
- **Implementation note (step 1):** The host needs only Docker, Compose v2 and make. `make lint`, `format`, `typecheck` and `test` run in the `tools` Compose service (profile `tools`, Python 3.13), not on the host. The design lists `test` as needing no containers; it still needs no running stack, but it does run inside a tools container.

### DEC-05 Login on a Keycloak-hosted themed page

- **Status:** Assumed (open question Q1).
- **Realizes:** DES-IDP-04, DES-IDP-08, DES-AUTH-05.
- **Decision:** Users sign in on a Keycloak page themed to match the Gradian login design, using Authorization Code with PKCE. The Core Service never sees a password.
- **Alternatives:** A custom login form in the Gradian frontend posting credentials to Django or to Keycloak with a password grant. This matches the PDF mock-up more literally, but password grants are discouraged in current OAuth guidance and put credentials through the frontend.
- **Consequences:** The theme must reproduce the design faithfully. If the TA requires a custom form, DES-IDP-04 and DES-IDP-08 change and `gradian-web` needs direct grants.

### DEC-06 Stateless bearer-token API

- **Status:** Proposed.
- **Realizes:** DES-AUTH-01, DES-AUTH-03, DES-AUTH-05, DES-REG-05, DES-REG-06.
- **Decision:** The Core Service and every group service authenticate requests from a Keycloak-signed bearer token, validated locally against the realm's published keys. No server-side session is kept.
- **Alternatives:** Django sessions (do not carry over to other services); asking Keycloak to introspect every token (adds a network call to each request and makes Keycloak a bottleneck).
- **Consequences:** Tokens cannot be revoked before they expire, so lifetimes stay at 10 minutes or less. Services keep working briefly if Keycloak is down (SYS-NFR-03).

### DEC-07 Local profile cache keyed by `sub`

- **Status:** Proposed (open question Q7).
- **Realizes:** DES-ID-01 to DES-ID-04, DES-AUTH-04, DES-ID-06.
- **Decision:** The Core Service keeps a profile row per user, keyed by Keycloak's `sub`. It is created and refreshed from token claims, with a sync command as a safety net.
- **Alternatives:** Reading Keycloak on every request (slow, couples availability); a Keycloak event webhook (near-instant but needs a Keycloak plugin and more moving parts).
- **Consequences:** A Keycloak change reaches the Core Service within one access-token lifetime. An event listener can be added later without changing the model.
- **Refinement (step 1):** DES-ID-03 compares claims with the cache on every request. Taken literally, this undoes a `PATCH /me`: right after the write-through the user's still-valid token carries the old values and would overwrite the new cache. The profile therefore records `identity_synced_at`, and a token issued before that moment (`iat`, compared at one-second resolution) is not used to refresh identity fields. Tokens issued afterwards refresh the cache as designed.

### DEC-08 Identity edits written through to Keycloak first

- **Status:** Proposed.
- **Realizes:** DES-ID-05.
- **Decision:** Changes to identity fields made through `PATCH /api/v1/me` go to the Keycloak Admin API first; the cache is updated only after Keycloak accepts them.
- **Alternatives:** Editing the cache and syncing later (the two could disagree, which breaks SYS-ID-03); making identity read-only in Core (simplest, but the profile-completion services need a way to edit).
- **Consequences:** The `gradian-core` service account needs user-management rights in Keycloak, and a Keycloak outage makes identity edits fail with 502.
- **Implementation note (step 1):** `PATCH /me` accepts `email`, `first_name` and `last_name` (written through) and the Core-owned `field_of_study`, `avatar_url`, `bio`. It does not accept `mobile` or `role`: the mobile number is the login and no verification step exists, and roles are assigned by an administrator in Keycloak. An email already used in the realm returns 409 `identity_conflict`.

### DEC-09 Panel from a single realm role

- **Status:** Proposed (the shared consultant and top-ranker panel is from the PDF).
- **Realizes:** DES-IDP-03, DES-AUTH-02, DES-AUTH-03, DES-AUTH-06.
- **Decision:** Each user has exactly one panel role. Consultants and top-rankers share the role `consultant`, told apart by the attribute `consultant_type`. A fifth role, `service`, is for machine clients.
- **Alternatives:** Separate roles for top-rankers (they share one panel, so a second role adds nothing); letting users hold several roles (needs a "which panel?" rule the PDF does not give).
- **Consequences:** An account with zero or several panel roles is refused rather than guessed at.

### DEC-10 Service registry in the database

- **Status:** Proposed (open question Q4).
- **Realizes:** DES-REG-01 to DES-REG-04.
- **Decision:** The 25 panel entries live in a database table, seeded from a fixture, with an editable target URL and an `embed` or `redirect` mode per entry.
- **Alternatives:** A static configuration file (needs a redeploy to connect a group); only embedding (excludes services that cannot be framed); only redirect (loses the PDF's "content area" behaviour).
- **Consequences:** Group services that embed must allow framing from the frontend origin.

### DEC-11 Seeding by realm import and fixtures

- **Status:** Chosen (fixtures plus a bootstrap target by the TA; the generator is proposed).
- **Realizes:** DES-IDP-01, DES-DATA-01, DES-DATA-02, DES-DATA-04 to DES-DATA-06, DES-DATA-08 to DES-DATA-10.
- **Decision:** Keycloak users are loaded through Keycloak's realm import; Core data is loaded with Django fixtures by `make bootstrap`. Both are generated from `seed/people.yaml` by one deterministic script, and the generated fixtures are committed.
- **Alternatives:** A custom management command that creates users through the Admin API (works against a shared Keycloak, kept as a variant, DES-DATA-10); hand-written fixtures and realm JSON (drift between the two, tedious to scale to many groups).
- **Consequences:** Passwords never enter committed files, because the realm file is rendered into a git-ignored directory. Realm import runs only on an empty Keycloak, so `make reset` removes the Keycloak volume. A check in CI catches fixtures that fall out of date.

### DEC-12 Deterministic IDs from the mobile number

- **Status:** Proposed.
- **Realizes:** DES-DATA-03.
- **Decision:** A user's ID is a UUIDv5 of the normalized mobile number. It is used as the Keycloak user ID and as the Core profile primary key.
- **Alternatives:** Random IDs created by Keycloak (the fixtures cannot reference them in advance, so a lookup step is needed).
- **Consequences:** Fixtures and Keycloak agree without coordination, and `loaddata` can be repeated. This relies on the realm import honouring a supplied user ID; check it against the chosen Keycloak version early.

### DEC-13 Django's test runner with an `integration` tag

- **Status:** Chosen.
- **Realizes:** DES-IDP-09, DES-OPS-02, and the test plan.
- **Decision:** Tests are Django `TestCase` classes. Those that need the running stack are tagged `integration`; `make test` excludes the tag and `make test-integration` selects it. No additional test framework is required.
- **Alternatives:** pytest with markers (more features, an extra dependency).
- **Consequences:** Fast tests replace Keycloak with a fake key set. Integration tests use a test-only client, so DES-IDP-09 exists only outside production.
- **Implementation note (step 1):** Fast tests run on in-memory SQLite through `gradian.settings_test`, so `make test` needs no containers and no `.env`. Integration tests run inside the `core` container against PostgreSQL and the real Keycloak.

### DEC-14 Project groups as Core tables

- **Status:** Assumed (open questions Q2 and Q3).
- **Realizes:** DES-DATA-07, DES-REG-07.
- **Decision:** A project group is a row in the Core database, linked to users through a membership table. Membership is not stored in Keycloak.
- **Alternatives:** Keycloak groups (would put course administration into the identity provider and into every token).
- **Consequences:** Group services read membership through the Core API. If "groups" means something else, this decision and sections 5 and 7 of the design change.

### DEC-15 API and platform conventions

- **Status:** Proposed.
- **Realizes:** DES-API-01, DES-API-03 to DES-API-07, DES-XC-01 to DES-XC-03.
- **Decision:** Versioned base path `/api/v1/`; one error shape with English codes and Persian messages; OpenAPI 3 generated from code; structured JSON logs; Persian locale and Tehran time zone; configurable CORS and rate limits.
- **Alternatives:** Unversioned paths (breaking changes would hit every group at once); English-only messages (the product is Persian).
- **Consequences:** Removing or renaming anything under `/api/v1/` after groups integrate needs a new version.

### DEC-16 ruff and strict mypy

- **Status:** Chosen (requested for the project; not a requirement).
- **Realizes:** DES-OPS-02, DES-OPS-04 (the `lint`, `format` and `typecheck` targets), supports SYS-OPS-04.
- **Decision:** ruff is the only linter and formatter; mypy runs in strict mode with `django-stubs` and `djangorestframework-stubs` over the Core Service, its tests and `scripts/`. Both are configured in `core/pyproject.toml` and run through `make lint`, `make format` and `make typecheck`. The rules and the workflow are in `CONTRIBUTING.md`.
- **Alternatives:** black, isort and flake8 (three tools and three configurations instead of one); pyright (faster, but the Django plugin is stronger in mypy).
- **Consequences:** Dev tools are pinned in `core/requirements-dev.txt`, separate from runtime dependencies. They run in a `tools` Compose service (the `dev` stage of `core/Dockerfile`), so no Python is needed on the host (see the DEC-04 note). Every function is annotated and `Any` stays at the edges. `django-stubs-ext` is a runtime dependency so generic annotations like `ModelAdmin[Profile]` work. A change that fails `make check` is not merged.
