.DEFAULT_GOAL := help

ALL_TEAMS       := 1 2 3 4 5 6 7 8 9 10
TEAMS           ?=
NET             ?= gradian
COMPOSE         ?= docker compose
CORE_SERVICE    ?= core
EXEC_FLAGS      ?=
CMD             ?=
FIXTURES        ?= profiles services landing widgets
INTEGRATION_CMD ?= python manage.py test --tag=integration --keepdb -v2

CORE_ENV   := .env
HOST_USER  := $(shell id -u):$(shell id -g)
RUN_TOOLS   = $(COMPOSE) run --rm -T --user $(HOST_USER) -e HOME=/tmp
CORE_TOOLS  = $(RUN_TOOLS) tools
ROOT_TOOLS  = $(RUN_TOOLS) -w /repo tools
PY_PATHS   := . ../scripts ../packages
MYPY_PATHS := . ../scripts $(addprefix ../,$(wildcard packages/*/src))

TOOLS_INPUTS := docker-compose.yml core/Dockerfile $(wildcard core/requirements*.txt) \
                $(wildcard core/pyproject.toml) $(wildcard packages/*/pyproject.toml)
TOOLS_HASH   := $(shell cat $(TOOLS_INPUTS) | (sha256sum 2>/dev/null || shasum -a 256) | cut -c1-12)
TOOLS_STAMP  := build/.images-$(TOOLS_HASH)
TOOLS_DEPS   := $(CORE_ENV) network tools-image

ifeq ($(TEAMS),all)
  SELECTED := $(ALL_TEAMS)
else
  SELECTED := $(filter $(ALL_TEAMS),$(TEAMS))
  ifneq ($(filter-out $(ALL_TEAMS),$(TEAMS)),)
    $(error Unknown team(s): $(filter-out $(ALL_TEAMS),$(TEAMS)). Valid: $(ALL_TEAMS) or "all")
  endif
endif

ALL_ENVS := $(CORE_ENV) $(foreach n,$(ALL_TEAMS),teams/team$(n)/.env)
team_cmd  = $(COMPOSE) -f teams/team$(1)/docker-compose.yml
team_each = @set -e; for n in $(1); do echo "==> team $$n: $(2)"; $(call team_cmd,$$n) $(2); done

.PHONY: help start stop reset check itest users format logs shell django-shell manage \
        env network tools-image seed realm up bootstrap lint typecheck test schema migrations packages dev-frontend check-service baseline perf

help: ## Show this help
	@echo "Usage: make <target> [VAR=value]"
	@echo ""
	@echo "Main targets, the ones you normally run:"
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## [^(]/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Steps they are made of, to run one on its own:"
	@awk 'BEGIN {FS = ":.*## \\(step\\) "} /^[a-z-]+:.*## \(step\) / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Variables: TEAMS=\"1 6 5\"|all (teams to start), CMD=\"...\" (for manage), COMPOSE, EXEC_FLAGS"
	@echo "Only Docker, Docker Compose v2 and make are needed on the host."

start: up bootstrap ## Start everything with demo data [seed realm up bootstrap]

stop: $(ALL_ENVS) ## Stop and remove the containers, keep the data
	$(call team_each,$(ALL_TEAMS),stop)
	$(COMPOSE) --profile dev-frontend stop

reset: $(ALL_ENVS) ## Wipe all data, then start clean [stop, then start]
	$(call team_each,$(ALL_TEAMS),down)
	$(COMPOSE) --profile dev-frontend down -v
	$(MAKE) start

check: lint typecheck test schema ## All static checks and fast tests, before every push [lint typecheck test schema]

itest: start ## Tests that need the running system [start, then the integration tests]
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) $(INTEGRATION_CMD)

dev-frontend: up ## Serve a throwaway sign-in tester on http://localhost:5173 (see dev-frontend/README.md)
	$(COMPOSE) --profile dev-frontend up -d dev-frontend

perf: $(TOOLS_DEPS) ## Load test: 50 concurrent users against /me and the panel endpoints, p95 must stay within 300 ms (needs the stack)
	$(ROOT_TOOLS) python scripts/perf_load.py --url http://core:8000 $(ARGS)

check-service: $(TOOLS_DEPS) ## Check that a group service follows the integration rules: make check-service URL=http://team1:8001 [ARGS=...]
	@test -n "$(URL)" || { echo "error: give URL=, for example http://team1:8001" >&2; exit 2; }
	$(ROOT_TOOLS) python scripts/check_service.py --url $(URL) $(ARGS)

users: $(TOOLS_DEPS) ## Write the seeded users' sign-in details and the group service credentials to build/credentials/
	@./scripts/refuse_production.sh users
	$(ROOT_TOOLS) python scripts/seed_credentials.py

format: $(TOOLS_DEPS) ## Apply ruff formatting and fixes (changes files)
	$(CORE_TOOLS) ruff format $(PY_PATHS)
	$(CORE_TOOLS) ruff check --fix $(PY_PATHS)

logs: ## Follow the core logs
	$(COMPOSE) logs -f

django-shell: up ## Open a Django shell in the core container
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py shell

shell: up ## Open a bash shell in the core container
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) bash


manage: up ## Run manage.py in the core container: make manage CMD="sync_keycloak_users"
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py $(CMD)

env: $(ALL_ENVS) ## (step) Create every missing .env from its .env.example, with fresh secrets

network: ## (step) Create the shared Docker network
	@docker network inspect $(NET) >/dev/null 2>&1 || docker network create $(NET)

tools-image: $(TOOLS_STAMP) ## (step) Build the tools and core images, only when their inputs changed

$(TOOLS_STAMP): $(TOOLS_INPUTS)
	@mkdir -p build
	$(COMPOSE) build tools core
	@rm -f build/.tools-image build/.images-*
	@touch $@

seed: $(TOOLS_DEPS) ## (step) Generate the fixtures (users, services, landing, widgets) from seed/
	@./scripts/refuse_production.sh seed
	$(ROOT_TOOLS) python scripts/seed_generate.py

realm: $(TOOLS_DEPS) ## (step) Render build/realm-gradian.json, the Keycloak import file
	@./scripts/refuse_production.sh realm
	@mkdir -p build
	$(ROOT_TOOLS) python scripts/render_realm.py

up: $(ALL_ENVS) realm ## (step) Start core, Keycloak, the database and TEAMS
	$(COMPOSE) up -d
	$(call team_each,$(SELECTED),up -d)

bootstrap: seed ## (step) Wait until healthy, migrate, load the fixture
	@./scripts/refuse_production.sh bootstrap
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py migrate --noinput
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py loaddata $(FIXTURES)

lint: $(TOOLS_DEPS) ## (step) ruff, formatting, .env.example, missing migrations, requirement coverage
	$(ROOT_TOOLS) python scripts/check_env_example.py
	$(CORE_TOOLS) ruff check $(PY_PATHS)
	$(CORE_TOOLS) ruff format --check $(PY_PATHS)
	$(CORE_TOOLS) python manage.py makemigrations --check --dry-run
	$(ROOT_TOOLS) python scripts/req_coverage.py --strict

typecheck: $(TOOLS_DEPS) ## (step) mypy in strict mode
	$(CORE_TOOLS) mypy $(MYPY_PATHS)

test: $(TOOLS_DEPS) ## (step) Fast tests, no system needed
	$(CORE_TOOLS) python manage.py test --exclude-tag=integration
	$(CORE_TOOLS) python ../packages/run_tests.py
	$(RUN_TOOLS) -w /repo -e PYTHONPATH=scripts tools python -m unittest discover -s scripts/tests

schema: $(TOOLS_DEPS) ## (step) Export and validate the OpenAPI schema, and check it against the frozen baseline
	@mkdir -p build
	$(CORE_TOOLS) python manage.py spectacular --validate --fail-on-warn --file ../build/openapi.yaml
	$(ROOT_TOOLS) python scripts/api_compat.py docs/openapi-baseline.yaml build/openapi.yaml

baseline: schema ## (step) Freeze the current OpenAPI schema as the baseline later changes are compared with
	cp build/openapi.yaml docs/openapi-baseline.yaml

packages: $(TOOLS_DEPS) ## (step) Build the package wheels into build/wheels/ for services outside this repository
	$(ROOT_TOOLS) python scripts/build_packages.py

migrations: $(TOOLS_DEPS) ## (step) Create migrations after a model change (changes files)
	$(CORE_TOOLS) python manage.py makemigrations

$(ALL_ENVS): %.env: | %.env.example
	@sed -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$(head -c 48 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     -e "s|^KEYCLOAK_CORE_CLIENT_SECRET=.*|KEYCLOAK_CORE_CLIENT_SECRET=$$(head -c 32 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     $*.env.example > $@
	@echo "Created $@ from $*.env.example"
