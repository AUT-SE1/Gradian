.DEFAULT_GOAL := help

ALL_TEAMS       := 1 2 3 4 5 6 7 8 9 10
TEAMS           ?=
NET             ?= gradian
COMPOSE         ?= docker compose
CORE_SERVICE    ?= core
EXEC_FLAGS      ?=
REQ_STRICT      ?=
CMD             ?=
INTEGRATION_CMD ?= python manage.py test --tag=integration --keepdb -v2

CORE_ENV   := .env
HOST_USER  := $(shell id -u):$(shell id -g)
RUN_TOOLS   = $(COMPOSE) run --rm -T --user $(HOST_USER) -e HOME=/tmp
CORE_TOOLS  = $(RUN_TOOLS) tools
ROOT_TOOLS  = $(RUN_TOOLS) -w /repo tools
PY_PATHS   := . ../scripts

COMPOSE_FILE := docker-compose.yml
TOOLS_INPUTS := $(COMPOSE_FILE) core/Dockerfile \
                $(wildcard core/requirements*.txt) \
                $(wildcard core/pyproject.toml) \
                $(wildcard core/poetry.lock) \
                $(wildcard core/setup.py) $(wildcard core/setup.cfg)

TOOLS_STAMP := build/.tools-image
REALM_JSON  := build/realm-gradian.json

BASE_DEPS  := $(CORE_ENV) network
TOOLS_DEPS := $(BASE_DEPS) tools-image

ifeq ($(TEAMS),all)
  SELECTED := $(ALL_TEAMS)
else
  SELECTED := $(filter $(ALL_TEAMS),$(TEAMS))
  ifneq ($(filter-out $(ALL_TEAMS),$(TEAMS)),)
    $(error Unknown team(s): $(filter-out $(ALL_TEAMS),$(TEAMS)). Valid: $(ALL_TEAMS) or "all")
  endif
endif

TARGET_TEAMS  := $(if $(TEAMS),$(SELECTED),$(ALL_TEAMS))
ALL_ENVS      := $(CORE_ENV) $(foreach n,$(ALL_TEAMS),teams/team$(n)/.env)
SELECTED_ENVS := $(CORE_ENV) $(foreach n,$(SELECTED),teams/team$(n)/.env)

team_cmd  = $(COMPOSE) -f teams/team$(1)/docker-compose.yml
team_each = @set -e; for n in $(1); do echo "==> team $$n: $(2)"; $(call team_cmd,$$n) $(2); done

.PHONY: help env network tools-image lint format typecheck test check check-env-example \
        req-coverage schema migrations seed-render dev-user up-core build up rebuild bootstrap \
        stop down reset ps logs shell manage test-integration

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target> [VAR=value]\n\nTargets:\n"} \
		/^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Variables:"
	@echo "  TEAMS=\"1 6 5\"|all   Teams for build/up (default none) or stop/down (default all)"
	@echo "  REQ_STRICT=1        Make 'lint' fail while a requirement has no test"
	@echo "  CMD=\"...\"           Arguments for 'manage'"
	@echo "  COMPOSE             Compose command (default: $(COMPOSE))"
	@echo "  EXEC_FLAGS          Extra flags for 'compose exec', e.g. -T in CI"
	@echo ""
	@echo "Only Docker, Docker Compose v2 and make are needed on the host."

env: $(CORE_ENV) ## Create .env from .env.example if missing (never overwrites)

tools-image: $(TOOLS_STAMP) ## Build the tools image (rebuilds only when its inputs change)

$(TOOLS_STAMP): $(TOOLS_INPUTS)
	@mkdir -p build
	$(COMPOSE) build tools
	@touch $@

lint: check-env-example $(TOOLS_DEPS) ## Lint, format check, missing migrations, requirement coverage
	$(CORE_TOOLS) ruff check $(PY_PATHS)
	$(CORE_TOOLS) ruff format --check $(PY_PATHS)
	$(CORE_TOOLS) python manage.py makemigrations --check --dry-run
	$(ROOT_TOOLS) python scripts/req_coverage.py $(if $(REQ_STRICT),--strict)

format: $(TOOLS_DEPS) ## Apply ruff formatting and fixes (changes files)
	$(CORE_TOOLS) ruff format $(PY_PATHS)
	$(CORE_TOOLS) ruff check --fix $(PY_PATHS)

typecheck: $(TOOLS_DEPS) ## Type-check everything with mypy in strict mode
	$(CORE_TOOLS) mypy $(PY_PATHS)

test: $(TOOLS_DEPS) ## Fast tests, no stack needed
	$(CORE_TOOLS) python manage.py test --exclude-tag=integration
	$(RUN_TOOLS) -w /repo -e PYTHONPATH=scripts tools python -m unittest discover -s scripts/tests

check: lint typecheck test ## Lint, typecheck and test: what CI runs on every push

check-env-example: $(TOOLS_DEPS) ## Fail if .env.example misses a variable the settings read
	$(ROOT_TOOLS) python scripts/check_env_example.py

req-coverage: $(TOOLS_DEPS) ## List requirements that no test claims
	$(ROOT_TOOLS) python scripts/req_coverage.py $(if $(REQ_STRICT),--strict)

schema: $(TOOLS_DEPS) ## Export and validate the OpenAPI schema to build/openapi.yaml
	@mkdir -p build
	$(CORE_TOOLS) python manage.py spectacular --validate --fail-on-warn --file ../build/openapi.yaml

migrations: $(TOOLS_DEPS) ## Create migrations after a model change
	$(CORE_TOOLS) python manage.py makemigrations

seed-render: $(REALM_JSON) ## Render build/realm-gradian.json, the Keycloak realm import file
	@:

$(REALM_JSON): $(BASE_DEPS) scripts/render_realm.py
	@./scripts/refuse_production.sh seed-render
	@mkdir -p build
	$(ROOT_TOOLS) python scripts/render_realm.py

dev-user: $(TOOLS_DEPS) ## Create a demo user in Keycloak: MOBILE=09120000001 ROLES=student
	@./scripts/refuse_production.sh dev-user
	$(ROOT_TOOLS) python scripts/dev_user.py --mobile "$(MOBILE)" \
		$(if $(ROLES),--roles "$(ROLES)") $(if $(CONSULTANT_TYPE),--consultant-type "$(CONSULTANT_TYPE)") \
		$(if $(FIRST_NAME),--first-name "$(FIRST_NAME)") $(if $(LAST_NAME),--last-name "$(LAST_NAME)") \
		$(if $(EMAIL),--email "$(EMAIL)") $(if $(PASSWORD),--password "$(PASSWORD)")

network:
	@docker network inspect $(NET) >/dev/null 2>&1 || docker network create $(NET)

up-core: $(CORE_ENV) network seed-render
	$(COMPOSE) up -d

build: $(SELECTED_ENVS) tools-image ## Build images for core + TEAMS (starts nothing)
	$(COMPOSE) build
	$(call team_each,$(SELECTED),build)

up: $(ALL_ENVS) up-core ## Start core + TEAMS, stop the other teams (no rebuild)
	$(call team_each,$(SELECTED),up -d)
	$(call team_each,$(filter-out $(SELECTED),$(ALL_TEAMS)),stop)

rebuild: ## Build images, then start core + TEAMS
	$(MAKE) build
	$(MAKE) up

bootstrap: ## Wait until healthy, then run migrations
	@./scripts/refuse_production.sh bootstrap
	COMPOSE="$(COMPOSE)" ./scripts/wait_for.sh
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py migrate --noinput

stop: $(ALL_ENVS) ## Stop containers, keep them (TEAMS=... for specific teams only)
	$(call team_each,$(TARGET_TEAMS),stop)
	$(if $(TEAMS),,$(COMPOSE) stop)

down: $(ALL_ENVS) ## Stop and remove containers (TEAMS=... for specific teams only)
	$(call team_each,$(TARGET_TEAMS),down)
	$(if $(TEAMS),,$(COMPOSE) down)

reset: ## Wipe database and Keycloak data, then start clean and bootstrap
	$(call team_each,$(ALL_TEAMS),down)
	$(COMPOSE) down -v
	$(MAKE) up
	$(MAKE) bootstrap

ps: $(ALL_ENVS) ## Show containers for core and all teams
	@echo "==> core"; $(COMPOSE) ps
	$(call team_each,$(ALL_TEAMS),ps)

logs: ## Follow core logs
	$(COMPOSE) logs -f

shell: ## Open a Django shell in the core container
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py shell

manage: ## Run manage.py in the core container: make manage CMD="sync_keycloak_users --dry-run"
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) python manage.py $(CMD)

test-integration: ## Tests tagged "integration", against the running stack
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_SERVICE) $(INTEGRATION_CMD)

$(ALL_ENVS): %.env: | %.env.example
	@sed -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$(head -c 48 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     -e "s|^KEYCLOAK_CORE_CLIENT_SECRET=.*|KEYCLOAK_CORE_CLIENT_SECRET=$$(head -c 32 /dev/urandom | base64 | tr -d '=+/\n')|" \
	     $*.env.example > $@
	@echo "Created $@ from $*.env.example"