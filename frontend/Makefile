# Run from frontend/. Requires GNU Make and a POSIX shell (WSL or Git Bash).
# Docker targets need Docker Compose v2; local targets need Node 22.12+ and npm.
.DEFAULT_GOAL := help
.NOTPARALLEL:

SHELL := /bin/sh
NPM ?= npm
COMPOSE ?= docker compose
DEV_PORT ?= 5173
PREVIEW_PORT ?= 4173
PROD_PORT ?= 8081
HOST ?= 0.0.0.0
DEV_COMPOSE = $(COMPOSE) -f docker-compose.yml
PROD_COMPOSE = $(COMPOSE) -f docker-compose.prod.yml

.PHONY: help env network start stop restart logs status shell docker-install \
        docker-check setup install dev build preview lint lint-fix typecheck \
        check clean prod-build prod-start prod-stop prod-logs

help:
	@printf '%s\n' \
	  'Gradian frontend: make <target> [VAR=value]' \
	  '' \
	  'Docker development (no local Node required):' \
	  '  start           Build and start frontend at localhost:5173' \
	  '  stop            Remove frontend containers; keep dependency volume' \
	  '  restart         Restart frontend (use start after Dockerfile changes)' \
	  '  logs            Follow frontend logs (Ctrl+C to leave)' \
	  '  status          Show frontend container status' \
	  '  shell           Open sh in running frontend container' \
	  '  docker-install  Refresh container dependencies after lockfile changes' \
	  '  docker-check    Run lint and production build in a temporary container' \
	  '' \
	  'Local development (Node 22.12+ and npm):' \
	  '  setup           Create missing .env and install locked dependencies' \
	  '  install         npm ci (also use after package-lock.json changes)' \
	  '  dev             Start Vite; Ctrl+C stops it' \
	  '  build           TypeScript check and production build in dist/' \
	  '  preview         Build, then preview at localhost:4173' \
	  '  lint            Check ESLint' \
	  '  lint-fix        Apply available ESLint fixes (changes source files)' \
	  '  typecheck       Check app and Vite TypeScript without emitting JS' \
	  '  check           Run lint, then production build; stop on errors' \
	  '  clean           Remove only local dist/ and TypeScript build cache' \
	  '' \
	  'Local production container (does not publish to a server):' \
	  '  prod-build      Build Nginx production image' \
	  '  prod-start      Build and serve at localhost:8081' \
	  '  prod-stop       Stop production container' \
	  '  prod-logs       Follow production logs' \
	  '' \
	  'Other: env, network' \
	  'Ports: make start DEV_PORT=5174 / make prod-start PROD_PORT=8082' \
	  'Backend is started separately from backend/.'

env:
	@if [ ! -f .env ]; then cp .env.example .env; printf '%s\n' 'Created .env from .env.example'; fi

network:
	@docker network inspect gradian >/dev/null 2>&1 || docker network create gradian

start: env network
	FRONTEND_PORT=$(DEV_PORT) $(DEV_COMPOSE) up -d --build frontend

stop:
	$(DEV_COMPOSE) down

restart:
	$(DEV_COMPOSE) restart frontend

logs:
	$(DEV_COMPOSE) logs -f frontend

status:
	$(DEV_COMPOSE) ps

shell:
	$(DEV_COMPOSE) exec frontend sh

docker-install: env network
	$(DEV_COMPOSE) run --rm --no-deps --build frontend npm ci

docker-check: env network
	$(DEV_COMPOSE) run --rm --no-deps --build -T frontend sh -ec 'npm ci; npm run lint; npm run build'

setup: env install

install:
	$(NPM) ci

dev: env
	$(NPM) run dev -- --host $(HOST) --port $(DEV_PORT) --strictPort

build: env
	$(NPM) run build

preview: build
	$(NPM) run preview -- --host $(HOST) --port $(PREVIEW_PORT) --strictPort

lint:
	$(NPM) run lint

lint-fix:
	$(NPM) run lint -- --fix

typecheck:
	$(NPM) run typecheck

check:
	$(MAKE) lint
	$(MAKE) build

clean:
	node -e "const fs = require('node:fs'); for (const p of ['dist', 'node_modules/.tmp']) fs.rmSync(p, {recursive: true, force: true});"

prod-build: env
	$(PROD_COMPOSE) build frontend

prod-start: env
	FRONTEND_PORT=$(PROD_PORT) $(PROD_COMPOSE) up -d --build frontend

prod-stop:
	$(PROD_COMPOSE) down

prod-logs:
	$(PROD_COMPOSE) logs -f frontend
