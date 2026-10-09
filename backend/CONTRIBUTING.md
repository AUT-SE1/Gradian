# Contributing

Rules for working on the Core Service (`core/`) and the repository scripts (`scripts/`), both in the
`backend/` folder of the monorepo. Run `make` from `backend/`.
Requirements, design and decisions live in [`docs/backend/`](docs/backend/); this file is only
about how we write and check code.

## Setup

Everything runs in Docker. You need Docker Engine, the Docker Compose v2 plugin (`docker compose`)
and `make`. You do not need Python on your machine, whatever its version.

    make check           # lint + typecheck + test; run this before every push

The first run builds the `tools` image (Python 3.13 with the pinned dev dependencies from
`core/requirements-dev.txt`); later runs reuse it. Tools run as your user, so files they create
(migrations, formatted code) belong to you. If you change a requirements file, the next `make`
target rebuilds the image automatically.

Editor support is optional. To get completion and inline type errors, create a local virtualenv
with Python 3.13 and install `core/requirements-dev.txt` into it; `make` never uses it.

## The checks

| Command | What it does | Changes files |
| --- | --- | --- |
| `make check` | `lint`, `typecheck`, `test` and `schema` | No |
| `make format` | `ruff format`, then `ruff check --fix` | **Yes** |
| `make migrations` | `makemigrations` after a model change | **Yes** |
| `make itest` | Starts the system if needed, then the tests tagged `integration` | No |

`make check` is made of steps you can run alone: `lint` (`ruff check`, `ruff format --check`,
`.env.example` check, `makemigrations --check`, requirement-coverage report), `typecheck` (`mypy` in
strict mode over `core/` and `scripts/`), `test` (fast tests and the script tests) and `schema`
(OpenAPI export and validation).

`make check` is the one command CI should run on every push, and it must pass before a change is
merged. A typical loop is: write code, `make format`, then `make check`.

Everything is configured in [`core/pyproject.toml`](core/pyproject.toml). Do not add per-developer
settings elsewhere, and do not loosen a rule to make a check pass without agreeing it in review.

### Linting and formatting (ruff)

Ruff is the only linter and the only formatter: no black, isort or flake8. Line length is 100.
Generated migrations are excluded. Rules are listed in `pyproject.toml`; the notable ones:

- `S` (bandit): no `assert` in application code, no weak crypto, no shell injection. Tests may
  use `assert` and fake secrets.
- `T20`: no `print()` in application code. Use `logging.getLogger("gradian.<area>")`.
- `PTH`: use `pathlib`, not `os.path`.

When a rule is wrong for one line, suppress that rule on that line with a reason:
`# noqa: S603  # arguments are fixed, no user input`. Never use a blanket `# noqa`.

### Strict typing (mypy)

Every function, method and test is fully annotated. `strict = true` is on for the whole repository,
tests and scripts included, together with `django-stubs` and `djangorestframework-stubs`.

- Annotate parameters and return types, including `-> None` and test methods.
- Avoid `Any`. When it is unavoidable (for example a decoded JSON body), keep it at the edge and
  narrow it right away with `isinstance` or a `TypedDict`/dataclass.
- Prefer `dataclass(frozen=True)`, `TypedDict`, `Protocol` and `StrEnum`/`TextChoices` over loose
  dicts and strings.
- `# type: ignore[code]` is allowed only with the specific error code and a reason after it:
  `# type: ignore[arg-type]  # deliberately the wrong key type`. `warn_unused_ignores` is on, so a
  stale ignore fails the check.
- Do not turn off a strict flag, add `ignore_errors`, or exclude a file to silence an error.
- Django generics such as `ModelAdmin[Profile]` work at runtime because settings call
  `django_stubs_ext.monkeypatch()`.

### Tests

- Fast tests extend `tests.helpers.base.ApiTestCase` (fake Keycloak keys from `gradian_testing`, stubbed Admin API) or
  Django's `TestCase`/`SimpleTestCase`. They need no stack and never touch the network.
- Tests that need the running stack extend `IntegrationTestCase` (tag `integration`) and live in a
  `tests/integration/` folder.
- Tie every test to the requirement it checks with `@covers("SYS-AUTH-02")` from
  `gradian_testing.covers`. This also adds a tag, so one requirement's tests run with
  `--tag=req-SYS-AUTH-02`.
- `make lint` lists requirements without a test. Making that report fail (`--strict` in
  `scripts/req_coverage.py`) is for once the system is complete.
- Only tag a test with a requirement it really verifies. A test that exercises part of a
  requirement belongs to the test-plan level it matches (see `docs/backend/04-test-plan.md`).
- A test must not depend on the contents of your `.env`.
- Do not write a test that only restates a setting or the realm file: it duplicates the decision it
  checks and breaks whenever that decision changes. Behaviour that Keycloak or Django implements is
  marked `EXT` in the test plan instead (DEC-17). Test the code we write on top of it.

## Shared packages

Code that Core and the group services both need lives in `packages/` (see
[`packages/README.md`](packages/README.md)), not in `core/`. `make check` lints, type-checks and tests it
with Core; its tests live in `packages/<package>/src/<module>/tests/`. Import from the package
(`gradian_auth`, `gradian_keycloak`, `gradian_testing`), never copy a module back into `core/`. A change to
something a package's README documents is a change for every service that installs it: keep it
compatible, or say so in the pull request and bump the version.

## Conventions

- **Comments.** Comment only to explain why something is done, never what the next line does.
  No filler: no separator or banner lines (`# ----`, `# ====`, `# ****`), no section headings in
  comments, no ASCII art, no commented-out code, no decorative blank comment lines. Group code with
  blank lines and good names instead. A Makefile target gets its one-line `##` help text and
  nothing more. This applies to every file type, including Makefiles, YAML, TOML, shell and
  `.env.example`.
- **Layout.** Follow `docs/backend/02-design.md`: Django project in `core/`, apps beside
  `gradian/`, scripts in `scripts/`. Business logic lives in plain modules (`accounts/mobile.py`,
  `accounts/roles.py`, ...) so it can be unit-tested without a database; views stay thin.
- **Docker only.** Nothing in the Makefile may need Python or any other language runtime on the
  host. Tools run in the `tools` container, the service in the `core` container.
- **Settings and secrets.** Read environment variables only through `gradian/env.py`
  (`require`, `get`, `flag`, `csv`) with a literal name, and list every new variable in
  `.env.example` (an optional one can be listed commented out). `make lint` fails if the two
  disagree. Never commit a secret.
- **Errors.** Raise a subclass of `gradian_auth.errors.ApiError` with a stable English
  `default_code`, and add its Persian message with `register_messages` next to the class. Every response has the
  shape `{"code", "message", "details"}`.
- **Logging.** Use the `gradian.*` loggers with an `event` key in `extra`. Log field names, never
  values, and never tokens or passwords. Do not use `created`, `name`, `message` or other
  `LogRecord` attribute names as `extra` keys; logging raises `KeyError` for them.
- **Identity.** Keycloak owns identity fields. Never add an editable copy; the Core `Profile`
  is a read cache (DES-ID-01).
- **Migrations.** Commit them. After changing a model run `make migrations`, then `make lint`;
  `makemigrations --check` fails when a migration is missing.
- **Makefile.** It only orders steps. Logic belongs in `scripts/` or a `manage.py` command so it
  also runs without `make` (DES-OPS-05).
- **Commits and reviews.** Small, focused changes. Say which requirement or design item a change
  serves (for example `SYS-ID-05`). Update the decision log (`docs/backend/03-decisions.md`) when a
  decision changes; requirements and design change only with the TA's agreement.
