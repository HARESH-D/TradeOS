#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/backend/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Backend virtual environment not found. Create backend/.venv and install requirements-dev.txt." >&2
  exit 1
fi

echo "[1/8] Python quality"
"$PYTHON_BIN" -m ruff check "$ROOT_DIR/backend/app" "$ROOT_DIR/backend/tests"

echo "[2/8] Python security analysis"
"$PYTHON_BIN" -m bandit -r "$ROOT_DIR/backend/app" -ll -ii

echo "[3/8] Backend tests"
"$PYTHON_BIN" -m pytest -q "$ROOT_DIR/backend/tests"

echo "[4/8] Python module compilation"
"$PYTHON_BIN" -m compileall -q "$ROOT_DIR/backend/app"

echo "[5/8] Python dependency audit"
"$PYTHON_BIN" -m pip_audit --local

echo "[6/8] Frontend type and production build"
npm --prefix "$ROOT_DIR/frontend" run lint
npm --prefix "$ROOT_DIR/frontend" run build

echo "[7/8] Frontend dependency audit"
npm --prefix "$ROOT_DIR/frontend" audit --audit-level=moderate

echo "[8/8] Compose validation"
docker compose -f "$ROOT_DIR/docker-compose.yml" config --quiet
docker compose \
  --env-file "$ROOT_DIR/deploy/oracle/.env.production.example" \
  -f "$ROOT_DIR/deploy/oracle/docker-compose.prod.yml" \
  config --quiet

echo "TradeOS quality gate passed."
