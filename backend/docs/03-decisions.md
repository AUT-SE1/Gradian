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
| DEC-05 | Login and registration on a Keycloak-hosted themed page | Chosen (Q1 answered by the registration decision) |
| DEC-06 | Stateless bearer-token API validated locally | Proposed |
| DEC-07 | Local profile cache keyed by `sub`, refreshed from token claims | Proposed |
| DEC-08 | Identity edits written through to Keycloak first | Proposed |
| DEC-09 | Panel chosen from a single realm role; top-ranker as consultant attribute | Proposed |
| DEC-10 | Service registry in the database, embed or redirect per entry | Proposed |
| DEC-11 | Seeding by realm import plus Django fixtures, generated from one source | Chosen |
| DEC-12 | Deterministic IDs derived from the mobile number | Proposed |
| DEC-13 | Django's test runner with an `integration` tag | Chosen |
| DEC-14 | Project groups are an allocation of seed users, not Core tables | Chosen (project owner) |
| DEC-15 | API and platform conventions | Proposed |
| DEC-16 | ruff and strict mypy for code quality | Chosen |
| DEC-17 | Rely on external components for behaviour they own | Chosen |
| DEC-18 | Public and internal addresses for Keycloak | Chosen |
| DEC-19 | Monorepo with `backend/` and `frontend/` | Chosen |
| DEC-20 | One Keycloak client per group service | Proposed |
| DEC-21 | Self-registration, with student as the default role | Chosen (project owner) |
| DEC-22 | Account administration through the Core API | Chosen (project owner) |

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
- **Implementation note (step 1):** The host needs only Docker, Compose v2 and make. `make lint`, `format`, `typecheck` and `test` run in the `tools` Compose service (profile `tools`, Python 3.13), not on the host. The design lists `test` as needing no containers; it still needs no running stack, but it does run inside a tools container. Keycloak runs as root in `docker-compose.yml` so that its named data volume is writable; that is for local development only.

### DEC-05 Login and registration on a Keycloak-hosted themed page

- **Status:** Chosen. The project owner asked for a registration page hosted with the sign-in page, which settles Q1.
- **Update:** the theme `gradian` (DES-IDP-08) now carries the registration page too, and a themed page is the only way to offer it.
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
- **Consequences:** An account with several panel roles is refused rather than guessed at. An account with none is a student (DEC-21).

### DEC-10 Service registry in the database

- **Status:** Proposed (open question Q4).
- **Realizes:** DES-REG-01 to DES-REG-04.
- **Decision:** The 25 panel entries live in a database table, seeded from a fixture, with an editable target URL and an `embed` or `redirect` mode per entry.
- **Alternatives:** A static configuration file (needs a redeploy to connect a group); only embedding (excludes services that cannot be framed); only redirect (loses the PDF's "content area" behaviour).
- **Consequences:** Group services that embed must allow framing from the frontend origin.

### DEC-11 Seeding by realm import and fixtures

- **Status:** Chosen (fixtures plus a bootstrap target by the TA; the generator is proposed).
- **Realizes:** DES-IDP-01, DES-DATA-01 to DES-DATA-06, DES-DATA-08, DES-DATA-10.
- **Decision:** Keycloak users are loaded through Keycloak's realm import; Core data is loaded with Django fixtures by `make bootstrap`. Both are generated from `seed/people.yaml` by one deterministic script. The fixture is a build artifact, git-ignored and written again by `make seed` (changed from committed fixtures, so no generated file can drift from the source).
- **Alternatives:** A custom management command that creates users through the Admin API (works against a shared Keycloak, kept as a variant, DES-DATA-10); hand-written fixtures and realm JSON (drift between the two, tedious to scale to many groups).
- **Consequences:** Passwords never enter committed files, because the realm file is rendered into a git-ignored directory. Realm import runs only on an empty Keycloak, so `make reset` removes the Keycloak volume. Because nothing generated is committed, there is no drift to check.

### DEC-12 Deterministic IDs from the mobile number

- **Status:** Proposed.
- **Realizes:** DES-DATA-03.
- **Decision:** A user's ID is a UUIDv5 of the normalized mobile number. It is used as the Keycloak user ID and as the Core profile primary key.
- **Alternatives:** Random IDs created by Keycloak (the fixtures cannot reference them in advance, so a lookup step is needed).
- **Consequences:** Fixtures and Keycloak agree without coordination, and `loaddata` can be repeated. This relies on the realm import honouring a supplied user ID; check it against the chosen Keycloak version early.
- **Verified (step 2):** Keycloak 26.0.8 keeps the supplied `id` of every user in a realm import, and each seeded user signs in with the shared password.

### DEC-13 Django's test runner with an `integration` tag

- **Status:** Chosen.
- **Realizes:** DES-IDP-09, DES-OPS-02, and the test plan.
- **Decision:** Tests are Django `TestCase` classes. Those that need the running stack are tagged `integration`; `make test` excludes the tag and `make test-integration` selects it. No additional test framework is required.
- **Alternatives:** pytest with markers (more features, an extra dependency).
- **Consequences:** Fast tests replace Keycloak with a fake key set. Integration tests use a test-only client, so DES-IDP-09 exists only outside production.
- **Implementation note (step 1):** Fast tests run on in-memory SQLite through `gradian.settings_test`, so `make test` needs no containers and no `.env`. Integration tests run inside the `core` container against PostgreSQL and the real Keycloak.

### DEC-14 Project groups are an allocation, not Core tables

- **Status:** Chosen (project owner). Replaces the earlier assumption that groups are rows with a membership table (Q2 is confirmed: groups are the student teams that build the group services; Q3 is moot).
- **Realizes:** DES-DATA-07, DES-REG-07.
- **Decision:** Every user is valid for every group's service, so the Core Service does not record who belongs to which group. A group exists only as an allocation made by the seed: its own users of every role to develop with, listed in `build/credentials/group-N.csv`, and its own Keycloak client `group-N` (DEC-20). Group services find people through `GET /api/v1/internal/users` and `/internal/users/{sub}`.
- **Alternatives:** `ProjectGroup` and `GroupMembership` tables with endpoints and an admin (built first and then removed: nothing used membership for access, and keeping it would suggest a restriction the system does not apply); Keycloak groups (would put course administration into the identity provider and into every token).
- **Consequences:** No membership to change after seeding (SYS-DATA-08 is withdrawn). If a group service needs to limit what a team sees, it keeps its own data keyed by `sub`. If the system ever needs real groups, they belong in the feature that uses them.

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

### DEC-17 Rely on external components for behaviour they own

- **Status:** Chosen (requested by the project owner).
- **Realizes:** supports SYS-NFR-08, changes how SYS-AUTH-01, 04, 05, 09, SYS-ID-01, SYS-OPS-06, SYS-NFR-01 and SYS-NFR-05 are verified.
- **Decision:** Where Keycloak or Django implements a behaviour and tests it themselves (sign-in, remember me, brute-force lockout, registration being off, HTTPS hardening, default language and time zone), we configure the component and mark the requirement `EXT` in the test plan. We do not write an automated test that restates the configuration. The MANUAL checklist confirms the behaviour once on a clean machine. SYS-NFR-08 was reworded to allow this: a requirement needs a test or an `EXT` mark.
- **Alternatives:** Test the configuration (tests duplicate the settings, and every new required variable had to be added to the tests as well); an integration test per behaviour against the real Keycloak (valuable but slow, and it tests Keycloak, not our code).
- **Consequences:** Fewer tests to maintain. Code we write on top of these components stays tested. A mistake in our configuration is caught by the manual checklist and by use, not by `make test`. `scripts/req_coverage.py` lists the externally relied-on requirements so the reliance is visible.

### DEC-18 Public and internal addresses for Keycloak

- **Status:** Chosen (made by the project owner).
- **Realizes:** DES-IDP-01, DES-IDP-06.
- **Decision:** Two addresses, each used for what it can do. `KEYCLOAK_PUBLIC_URL` (default `http://localhost:8080`) is what browsers use; Compose gives it to Keycloak as `KC_HOSTNAME`, so it is the `iss` claim of every token whichever address a client used to fetch the token, and the Core Service derives `KEYCLOAK_ISSUER` from it. `KEYCLOAK_URL` (default `http://keycloak:8080`) is how the Core Service and the tools reach Keycloak inside the Compose network, for the signing keys and the Admin API. Verified against Keycloak 26.0.8: a request through the internal name reports the public issuer, and the console stays on the public address.
- **Alternatives:** One address for everything (`http://keycloak:8080`): one variable, but every browser needs a hosts-file entry, the console and sign-in redirect to a name that does not resolve without it, and the published port is fixed to 8080; a separately configured issuer (a third variable that must agree with the other two).
- **Consequences:** No hosts-file step. `localhost` is never used by a container to reach Keycloak (inside a container it is the container itself). The published Keycloak port must match the port in `KEYCLOAK_PUBLIC_URL`. The integration test that compares the issuer Keycloak reports with the one the Core Service derives catches a mismatch between `KC_HOSTNAME` and the public address.

### DEC-19 Monorepo

- **Status:** Chosen (made by the project owner).
- **Decision:** The repository root holds `backend/` (everything in this document set, with its own Makefile, Compose file and `.env`) and `frontend/` (React and TypeScript). Commands are run from `backend/`. The repository layout drawing in 02 Design describes the contents of `backend/`.
- **Consequences:** Backend tooling and the Docker `tools` service see only `backend/`. A root README should point to both parts. Contracts between the two (sign-in flow, role names, API base path) are decided in the backend documents and recorded in the handoff.

### DEC-20 One Keycloak client per group service

- **Status:** Proposed (the handoff's default; open for the project owner).
- **Realizes:** DES-IDP-04, DES-REG-07.
- **Decision:** The seed generates one confidential client `group-N` per group, with a service account holding the realm role `service` and an audience mapper adding `gradian-core`, so a client-credentials token is accepted by the Core Service. Each client id is also added to the audience of the signed-in user's token (mappers on `gradian-web`), so a group service can check that a token was meant for it (DES-REG-05). Client secrets are derived from `SEED_DEFAULT_PASSWORD` and the client id, and appear only in the git-ignored realm file and `build/credentials/group-N-service.csv`.
- **Alternatives:** One shared client for all groups (fewer entries, but one leaked secret exposes every group and no token says which group called).
- **Consequences:** User tokens carry one audience entry per group (11 at 10 groups). The realm grows by ten clients and ten service accounts. The Core Service does not yet limit a group to its own members: `azp` identifies the caller if that is wanted later. A deployed environment needs its own secrets; seeding is refused in production.

### DEC-21 Self-registration, with student as the default role

- **Status:** Chosen (project owner). Replaces the earlier rule that accounts exist only by seeding or by an administrator, and that an account with no panel role is refused.
- **Realizes:** DES-IDP-02, DES-IDP-08, DES-IDP-10, DES-AUTH-02, DES-AUTH-07.
- **Decision:** Keycloak's registration is on, on the themed page. A registrant becomes a student. The default is applied in the Core Service: a person whose token has no panel role is a student, and the first time Core sees such a person it grants the realm role `student` in Keycloak, so that group services reading `realm_access.roles` see it from the next token.
- **Alternatives:** Keycloak's default role or a default group holding `student` (rejected after checking how Keycloak builds tokens: a default role is a composite that every user's token carries, so every consultant would also be a student and Core would refuse them as ambiguous); a custom Keycloak extension that assigns the role at registration (heavy: Java code to build and maintain).
- **Consequences:** Registration is open to anyone, and mobile numbers are not verified (Q8): someone can register a number that is not theirs, and brute-force or sign-up abuse protection is Keycloak's default only. An SMS code or a CAPTCHA would be a later feature. The first token of a new person lacks the `student` role, so a group service that insists on seeing it must wait for a token refresh. In Keycloak 26.0.8 the `prompt=create` parameter does not open the registration page; the frontend uses the `registrations` endpoint (returned by `/auth/config`). Verified against Keycloak 26.0.8: the whole flow from the form to a token.

### DEC-22 Account administration through the Core API

- **Status:** Chosen (project owner).
- **Realizes:** DES-ADM-01 to DES-ADM-04.
- **Decision:** Administrators create accounts and change roles through `/api/v1/admin/users`. The Core Service writes to Keycloak through its service account, first, and updates its cache after Keycloak accepts the change (as in DEC-08).
- **Alternatives:** Only the Keycloak console (works today, but the Gradian admin panel cannot offer it, and the cache would learn of changes only at the next sign-in); a Keycloak plugin (heavy).
- **Consequences:** The admin panel can manage people without Keycloak access. A role change reaches a token already issued only when it expires, at most ten minutes (DEC-06). A change spans several Keycloak calls: creating an account that cannot be given its role is rolled back, but a role change that fails halfway can leave a person with a changed attribute and the old role, which is harmless and can be repeated. Administrators cannot change their own role or status, so the system cannot be left without an administrator by accident.
