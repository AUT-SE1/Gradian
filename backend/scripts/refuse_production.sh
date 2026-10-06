#!/usr/bin/env bash
# Refuse to run demo-data tasks when ENVIRONMENT=production (DES-DATA-06, SYS-DATA-07).
# Usage: scripts/refuse_production.sh <task name>
# ENVIRONMENT is taken from the process environment, else from .env, else "development".
set -euo pipefail

task="${1:-this task}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

environment="${ENVIRONMENT:-}"
if [[ -z "$environment" && -f "$root/.env" ]]; then
  environment="$(sed -n 's/^ENVIRONMENT=//p' "$root/.env" | tail -n 1 | tr -d '[:space:]')"
fi

if [[ "${environment:-development}" == "production" ]]; then
  echo "error: '$task' creates demo accounts and a shared password and is refused when ENVIRONMENT=production." >&2
  exit 1
fi
