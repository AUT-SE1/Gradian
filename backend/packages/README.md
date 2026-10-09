# Gradian packages

Shared Python packages for every Django service of the platform: Core, and the group services.
Install them instead of copying code.

| Package | Import | Guide | Needed by |
| --- | --- | --- | --- |
| `gradian-keycloak` | `gradian_keycloak` | [README](gradian-keycloak/README.md) | everything that talks to Keycloak |
| `gradian-auth` | `gradian_auth` | [README](gradian-auth/README.md) | **every service that has users** |
| `gradian-testing` | `gradian_testing` | [README](gradian-testing/README.md) | tests only |

`gradian-auth` depends on `gradian-keycloak`, `gradian-testing` on both. They are not on PyPI, so
always install them in one `pip` command. A group service almost always wants just these two:

    pip install <path>/gradian-keycloak "<path>/gradian-auth[drf]"   # [drf] only with Django REST Framework

Start with the [gradian-auth quickstart](gradian-auth/README.md#quickstart-plain-django). The
frontend team's guide is [docs/05-frontend-guide.md](../docs/05-frontend-guide.md).

## Install in a service of this repository (Docker)

The skeletons in `teams/teamN/` already do this. Compose passes this folder as a named build
context, and the Dockerfile installs from it:

```yaml
# teams/teamN/docker-compose.yml
build:
  context: .
  additional_contexts:
    packages: ../../packages
```

```dockerfile
# teams/teamN/Dockerfile
COPY --from=packages . /tmp/packages
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /tmp/packages/gradian-keycloak /tmp/packages/gradian-auth
```

Your `requirements.txt` still pins Django, `requests`, `PyJWT` and `cryptography` (and
`djangorestframework` if you use it). Then set the Keycloak variables from `.env.example`.

## Install in a service in another repository

Build the wheels in this repository and copy them next to your service:

    make packages                 # writes backend/build/wheels/*.whl
    pip install --no-index --find-links vendor/wheels gradian-auth

or install straight from Git, pinned to a tag:

    pip install "gradian-keycloak @ git+https://<host>/<repo>.git@<tag>#subdirectory=backend/packages/gradian-keycloak" \
                "gradian-auth @ git+https://<host>/<repo>.git@<tag>#subdirectory=backend/packages/gradian-auth"

Pin one version across all your services; see Versioning.

## Working on the packages

Core and the `tools` container install them editable and mount `./packages` into `/packages`, so an
edit shows up without a rebuild. Outside Docker:

    pip install -e packages/gradian-keycloak -e "packages/gradian-auth[drf]" -e "packages/gradian-testing[drf]"
    python packages/run_tests.py            # or a label: gradian_auth.tests.test_tokens

`make check` lints, type-checks (strict) and tests them with Core. The tests of a package live in its
own `tests/` folder and are left out of the wheel.

Layout of a package (`src` layout):

    gradian-auth/
        pyproject.toml
        README.md
        src/gradian_auth/        modules, py.typed
        src/gradian_auth/tests/

## Versioning

Versions follow `MAJOR.MINOR.PATCH`, and the three packages are released together. While the major
version is 0, a minor bump may break the API: read the change before upgrading. A change that
removes or renames anything in a guide needs the agreement of the groups that use it (DES-API-03
applies the same rule to the HTTP API). Bump `version` in the `pyproject.toml` files and
`__version__` in each package.
