.DEFAULT_GOAL := help

ALL_TEAMS    := 1 2 3 4 5 6 7 8 9 10
TEAMS        ?=
NET          ?= gradian
COMPOSE      ?= docker compose
CORE_BACKEND ?= backend
TEST_CMD     ?= python manage.py test --keepdb -v2
EXEC_FLAGS   ?=

ifeq ($(TEAMS),all)
  SELECTED := $(ALL_TEAMS)
else
  SELECTED := $(filter $(ALL_TEAMS),$(TEAMS))
  ifneq ($(filter-out $(ALL_TEAMS),$(TEAMS)),)
    $(error Unknown team(s): $(filter-out $(ALL_TEAMS),$(TEAMS)). Valid: $(ALL_TEAMS) or "all")
  endif
endif

# stop/down: only the given teams (core untouched), or everything if TEAMS is empty
TARGET_TEAMS := $(if $(TEAMS),$(SELECTED),$(ALL_TEAMS))

CORE_ENV      := .env
ALL_ENVS      := $(CORE_ENV) $(foreach n,$(ALL_TEAMS),teams/team$(n)/.env)
SELECTED_ENVS := $(CORE_ENV) $(foreach n,$(SELECTED),teams/team$(n)/.env)

# $(call team_cmd,<n>) / $(call team_each,<list>,<compose args>)
team_cmd  = $(COMPOSE) -f teams/team$(1)/docker-compose.yml
team_each = @set -e; for n in $(1); do echo "==> team $$n: $(2)"; $(call team_cmd,$$n) $(2); done

.PHONY: help network up-core build up rebuild stop down ps logs test test-core

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target> [TEAMS=\"<n> <n> ...\"|all]\n\nTargets:\n"} \
		/^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Variables:"
	@echo "  TEAMS         Team numbers (\"1 6 5\") or \"all\"."
	@echo "                build/up: core + these teams (default: core only)."
	@echo "                stop/down: only these teams, core untouched (default: everything)."
	@echo "  NET           Shared docker network (default: $(NET))"
	@echo "  COMPOSE       Compose command (default: $(COMPOSE))"
	@echo "  EXEC_FLAGS    Extra flags for 'compose exec' in tests, e.g. -T in CI"
	@echo "  TEST_CMD      Command run by test-core (default: $(TEST_CMD))"
	@echo ""
	@echo "Examples:"
	@echo "  make up TEAMS=\"1 6 5\"    core + teams 1, 6, 5; other teams are stopped"
	@echo "  make rebuild TEAMS=all   rebuild and restart core + all teams"
	@echo "  make stop TEAMS=3        stop team 3 only"

network:
	@docker network inspect $(NET) >/dev/null 2>&1 || docker network create $(NET)

up-core: $(CORE_ENV) network
	$(COMPOSE) up -d

build: $(SELECTED_ENVS) ## Build images for core + TEAMS (starts nothing)
	$(COMPOSE) build
	$(call team_each,$(SELECTED),build)

up: $(ALL_ENVS) up-core ## Start core + TEAMS, stop the other teams (no rebuild)
	$(call team_each,$(SELECTED),up -d)
	$(call team_each,$(filter-out $(SELECTED),$(ALL_TEAMS)),stop)

rebuild: ## Build images, then start core + TEAMS
	$(MAKE) build
	$(MAKE) up

stop: $(ALL_ENVS) ## Stop containers, keep them (TEAMS=... for specific teams only)
	$(call team_each,$(TARGET_TEAMS),stop)
	$(if $(TEAMS),,$(COMPOSE) stop)

down: $(ALL_ENVS) ## Stop and remove containers (TEAMS=... for specific teams only)
	$(call team_each,$(TARGET_TEAMS),down)
	$(if $(TEAMS),,$(COMPOSE) down)

ps: $(ALL_ENVS) ## Show containers for core and all teams
	@echo "==> core"; $(COMPOSE) ps
	$(call team_each,$(ALL_TEAMS),ps)

logs: ## Follow core logs
	$(COMPOSE) logs -f

test-core: up-core ## Run core backend tests
	$(COMPOSE) exec $(EXEC_FLAGS) $(CORE_BACKEND) bash -c '$(TEST_CMD)'

test: test-core ## Run all tests

# Create a missing .env from .env.example with a fresh secret; never overwrites.
$(ALL_ENVS): %.env: | %.env.example
	@sed "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')|" $*.env.example > $@
	@echo "Created $@ from $*.env.example"