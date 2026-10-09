.DEFAULT_GOAL := help

ALL_TEAMS       := 1 2 3 4 5 6 7 8 9 10
TEAMS           ?=
NET             ?= gradian
COMPOSE         ?= docker compose
CORE_SERVICE    ?= core
EXEC_FLAGS      ?=
CMD             ?=
FIXTURES        ?= profiles
INTEGRATION_CMD ?= python manage.py test --tag=integration --keepdb -v2

CORE_ENV   := .env
HOST_USER  := $(shell id -u):$(shell id -g)
RUN_TOOLS   = $(COMPOSE) run --rm -T --user $(HOST_USER) -e HOME=/tmp
CORE_TOOLS  = $(RUN_TOOLS) tools
ROOT_TOOLS  = $(RUN_TOOLS) -w /repo tools
PY_PATHS   := . ../scripts

TOOLS_INPUTS := docker-compose.yml core/Dockerfile $(wildcard core/requirements*.txt) \
                $(wildcard core/pyproject.toml)
TOOLS_STAMP  := build/.tools-image
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

.PHONY: help start stop reset check itest users format logs shell manage \
        env network tools-image seed realm up bootstrap lint typecheck test schema migrations

help: ## Show this help
	@echo "Usage: make <target> [VAR=value]"
	@echo ""
	@echo "Main targets, the ones you normally run:"
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## [^(]/ {printf "  %-11s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Steps they are made of, to run one on its own:"
	@awk 'BEGIN {FS = ":.*## \\(step\\) "} /^[a-z-]+:.*## \(step\) / {printf "  %-11s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Variables: TEAMS=\"1 6 5\"|all (teams to start), CMD=\"...\" (for manage), COMPOSE, EXEC_FLAGS"
	@echo "Only Docker, Docker Compose v2 and make are needed on the host."

start: up bootstrap ## Start everything with demo data [seed realm up bootstrap]

stop: $(ALL_ENVS) ## Stop and remove the containers, keep the data
	$(call team_each,$(ALL_TEAMS),down)
	$(COMPOSE) down

reset: $(ALL_ENVS) ## Wipe all data, then start clean [stop, then start]
	$(call team_each,$(ALL_TEAMS),down)
	$(COMPOSE) down -v
	$(MAKE) start

check: lint typecheck test schema ## All static checks and fast tests, before every push [lint typecheck test schema]

itest: start ## Tests that need the running system [start, then the integration tests]
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) $(INTEGRATION_CMD)

users: $(TOOLS_DEPS) ## Write the per-group sign-in files to build/credentials/
	@./scripts/refuse_production.sh users
	$(ROOT_TOOLS) python scripts/seed_credentials.py

format: $(TOOLS_DEPS) ## Apply ruff formatting and fixes (changes files)
	$(CORE_TOOLS) ruff format $(PY_PATHS)
	$(CORE_TOOLS) ruff check --fix $(PY_PATHS)

logs: ## Follow the core logs
	$(COMPOSE) logs -f

shell: up ## Open a Django shell in the core container
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py shell

manage: up ## Run manage.py in the core container: make manage CMD="sync_keycloak_users"
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py $(CMD)

env: $(ALL_ENVS) ## (step) Create every missing .env from its .env.example, with fresh secrets

network: ## (step) Create the shared Docker network
	@docker network inspect $(NET) >/dev/null 2>&1 || docker network create $(NET)

tools-image: $(TOOLS_STAMP) ## (step) Build the tools image, only when its inputs changed

$(TOOLS_STAMP): $(TOOLS_INPUTS)
	@mkdir -p build
	$(COMPOSE) build tools
	@touch $@

seed: $(TOOLS_DEPS) ## (step) Generate the user fixture from seed/
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
	$(ROOT_TOOLS) python scripts/req_coverage.py

typecheck: $(TOOLS_DEPS) ## (step) mypy in strict mode
	$(CORE_TOOLS) mypy $(PY_PATHS)

test: $(TOOLS_DEPS) ## (step) Fast tests, no system needed
	$(CORE_TOOLS) python manage.py test --exclude-tag=integration
	$(RUN_TOOLS) -w /repo -e PYTHONPATH=scripts tools python -m unittest discover -s scripts/tests

schema: $(TOOLS_DEPS) ## (step) Export and validate the OpenAPI schema to build/openapi.yaml
	@mkdir -p build
	$(CORE_TOOLS) python manage.py spectacular --validate --fail-on-warn --file ../build/openapi.yaml

migrations: $(TOOLS_DEPS) ## (step) Create migrations after a model change (changes files)
	$(CORE_TOOLS) python manage.py makemigrations

$(ALL_ENVS): %.env: | %.env.example
	@sed -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$(head -c 48 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     -e "s|^KEYCLOAK_CORE_CLIENT_SECRET=.*|KEYCLOAK_CORE_CLIENT_SECRET=$$(head -c 32 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     $*.env.example > $@
	@echo "Created $@ from $*.env.example"
