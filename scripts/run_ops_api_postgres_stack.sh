#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
HOST="${OPS_API_HOST:-127.0.0.1}"
PORT="${OPS_API_PORT:-8000}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

if [[ -z "${OPS_API_DATABASE_URL:-}" ]]; then
  echo "OPS_API_DATABASE_URL must be set to a PostgreSQL URL." >&2
  exit 1
fi

"$PYTHON_BIN" "$ROOT_DIR/scripts/ensure_ops_api_postgres_db.py"
"$PYTHON_BIN" "$ROOT_DIR/scripts/apply_ops_api_migrations.py"
"$PYTHON_BIN" "$ROOT_DIR/scripts/bootstrap_ops_api_reference_data.py"

PYTHONPATH_ENTRIES=(
  "$ROOT_DIR/ops-api"
  "$ROOT_DIR/state-estimator"
  "$ROOT_DIR/llm-orchestrator"
  "$ROOT_DIR/execution-gateway"
  "$ROOT_DIR/policy-engine"
  "$ROOT_DIR/plc-adapter"
  "$ROOT_DIR/sensor-ingestor"
)

if [[ -n "${PYTHONPATH:-}" ]]; then
  PYTHONPATH_ENTRIES+=("$PYTHONPATH")
fi

export PYTHONPATH
PYTHONPATH="$(IFS=:; printf '%s' "${PYTHONPATH_ENTRIES[*]}")"

exec "$PYTHON_BIN" -m uvicorn ops_api.app:create_app \
  --factory \
  --host "$HOST" \
  --port "$PORT" \
  --log-level info
