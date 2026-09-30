# make all          -> core (keycloak + backend) + all ten teams
# make core         -> core only
# make 3            -> core + team 3
# make teams 1 6 5  -> core + teams 1, 6 and 5
# make down         -> stop everything
# make logs         -> follow core logs
# make test         -> run core tests
# Starting a selection stops the teams not in it.

TEAMS := 1 2 3 4 5 6 7 8 9 10
NET := gradian
ENVS := .env $(foreach n,$(TEAMS),teams/team$(n)/.env)
team = docker compose -f teams/team$(1)/docker-compose.yml

# $(1) = team numbers to run
define start
	docker network inspect $(NET) >/dev/null 2>&1 || docker network create $(NET)
	docker compose up -d --build
	$(foreach n,$(TEAMS),$(if $(filter $(n),$(1)),$(call team,$(n)) up -d --build,$(call team,$(n)) down) && ) true
endef

.PHONY: all core teams down logs test $(TEAMS)

all: $(ENVS)
	$(call start,$(TEAMS))

core: $(ENVS)
	$(call start,)

# `make teams 1 6 5`: the numbers after `teams` are its arguments, not separate targets.
ifeq ($(firstword $(MAKECMDGOALS)),teams)
teams: $(ENVS)
	$(call start,$(filter $(TEAMS),$(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))))
$(TEAMS): ; @:
else
$(TEAMS): $(ENVS)
	$(call start,$@)
endif

down: $(ENVS)
	$(foreach n,$(TEAMS),$(call team,$(n)) down && ) docker compose down

logs:
	docker compose logs -f

test:
	.venv/bin/python manage.py test

# Create a missing .env from its .env.example with a fresh secret key. Never overwrites an existing .env.
$(ENVS): %.env: | %.env.example
	sed "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')|" $*.env.example > $@
