#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== R09 frontend source contracts =="
node frontend/tests/r04-auth-flow.cjs
node frontend/tests/r06-public-registration.cjs
node frontend/tests/r07-callback.cjs
node frontend/tests/r08-auth-accessibility.cjs
node frontend/tests/r09-registration-contract.cjs

echo "== R09 backend registration contracts =="
python3 backend/scripts/tests/test_registration_identity_rules.py
python3 backend/scripts/tests/test_r05_theme_contract.py
python3 backend/scripts/tests/test_r07_identity_contract.py
python3 backend/scripts/tests/test_r08_theme_accessibility.py
python3 backend/scripts/tests/test_r09_registration_contract.py

echo "== R09 backend script regression =="
(
  cd backend
  PYTHONPATH='scripts:packages/gradian-auth/src:packages/gradian-keycloak/src' \
    python3 -m unittest discover -s scripts/tests -p 'test_*.py'
)

echo "== R09 syntax/config checks =="
python3 -m json.tool backend/keycloak/realm-template.json >/dev/null
python3 -m json.tool backend/keycloak/user-profile.json >/dev/null
python3 -m py_compile \
  backend/core/accounts/authentication.py \
  backend/core/accounts/profiles.py \
  backend/packages/gradian-auth/src/gradian_auth/claims.py \
  backend/packages/gradian-auth/src/gradian_auth/roles.py
node --check frontend/tests/r09-registration-contract.cjs

echo "R09 static preflight passed."
echo "NOTE: This does NOT run npm build/lint, Playwright/Chromium, Docker, Keycloak or live registration."
