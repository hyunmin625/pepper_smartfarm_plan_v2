#!/usr/bin/env python3
"""Validate ops-api against a real PostgreSQL URL when available."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from ops_api.app import create_app  # noqa: E402
from ops_api.config import load_settings  # noqa: E402
from ops_api.models import DeviceRecord, PolicyRecord, SensorRecord, ZoneRecord  # noqa: E402


def _resolve_postgres_url() -> str | None:
    for name in ("OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"):
        value = os.getenv(name, "").strip()
        if value.startswith("postgresql://") or value.startswith("postgresql+"):
            return value
    return None


def main() -> int:
    errors: list[str] = []
    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "postgres URL is not configured",
                    "expected_env": ["OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    try:
        import psycopg  # noqa: F401
    except Exception:
        try:
            import psycopg2  # noqa: F401
        except Exception:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "reason": "postgres driver is missing",
                        "required_drivers": ["psycopg", "psycopg2"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

    with tempfile.TemporaryDirectory(prefix="ops-api-postgres-smoke-") as tmp_dir:
        runtime_mode_path = Path(tmp_dir) / "runtime_mode.json"
        os.environ["OPS_API_DATABASE_URL"] = postgres_url
        os.environ["OPS_API_RUNTIME_MODE_PATH"] = str(runtime_mode_path)
        os.environ["OPS_API_LLM_PROVIDER"] = "stub"
        os.environ["OPS_API_MODEL_ID"] = "pepper-ops-local-stub"
        app = create_app(load_settings())
        services = app.state.services
        session = services.session_factory()
        try:
            zone_count = session.query(ZoneRecord).count()
            sensor_count = session.query(SensorRecord).count()
            device_count = session.query(DeviceRecord).count()
            policy_count = session.query(PolicyRecord).count()
            if zone_count < 1:
                errors.append("expected seeded zones on postgres")
            if sensor_count < 1:
                errors.append("expected seeded sensors on postgres")
            if device_count < 1:
                errors.append("expected seeded devices on postgres")
            if policy_count < 1:
                errors.append("expected seeded policies on postgres")

            print(
                json.dumps(
                    {
                        "errors": errors,
                        "status": "ok" if not errors else "failed",
                        "seeded_counts": {
                            "zones": zone_count,
                            "sensors": sensor_count,
                            "devices": device_count,
                            "policies": policy_count,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
