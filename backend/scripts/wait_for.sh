#!/usr/bin/env bash
# Start (if needed) and wait until Keycloak and Core report healthy.
# Usage: scripts/wait_for.sh [timeout-seconds]      Env: COMPOSE (default "docker compose")
set -euo pipefail

timeout="${1:-240}"
compose="${COMPOSE:-docker compose}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# `up --wait` blocks until every started service's health check passes, and fails on timeout.
# shellcheck disable=SC2086
$compose up -d --wait --wait-timeout "$timeout" keycloak core
