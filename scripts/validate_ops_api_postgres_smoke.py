#!/usr/bin/env python3
"""Validate ops-api against a real PostgreSQL URL when available.

When `OPS_API_POSTGRES_SMOKE_URL` (or `OPS_API_DATABASE_URL`) points at a
reachable PostgreSQL instance, this script exercises the ops-api startup,
seed bootstrap, and key write/read round-trips that would surface JSONB/
TIMESTAMP drift if the hand-written migration and the SQLAlchemy ORM
disagreed on column types. When no URL is available the script reports
`blocked` and exits 0 so it stays safe to wire into default CI sweeps.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from sqlalchemy import desc, select  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings, load_settings  # noqa: E402
from ops_api.models import (  # noqa: E402
    AlertRecord,
    DecisionRecord,
    DeviceRecord,
    PolicyRecord,
    RobotTaskRecord,
    SensorRecord,
    ZoneRecord,
)


def _resolve_postgres_url() -> str | None:
    for name in ("OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"):
        value = os.getenv(name, "").strip()
        if value.startswith("postgresql://") or value.startswith("postgresql+"):
            return value
    return None


def _blocked(reason: str, extra: dict[str, Any] | None = None) -> int:
    payload: dict[str, Any] = {"status": "blocked", "reason": reason}
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _exercise_write_round_trip(session_factory, errors: list[str]) -> dict[str, Any]:
    """Insert decision/alert/robot_task rows and fetch them back.

    This is the part that catches JSONB/TIMESTAMPTZ drift: if the SQL
    migration uses JSONB but the ORM writes plain Text, the insert will
    fail on real PostgreSQL with a type mismatch. On sqlite the mismatch
    is silent, which is why this path only runs when a real postgres URL
    is provided.
    """
    session = session_factory()
    round_trip: dict[str, Any] = {}
    try:
        zone_row = session.execute(select(ZoneRecord).limit(1)).scalar_one_or_none()
        if zone_row is None:
            errors.append("postgres round trip requires at least one seeded zone")
            return round_trip
        zone_id = zone_row.zone_id

        suffix = uuid.uuid4().hex[:12]
        decision = DecisionRecord(
            request_id=f"pg-smoke-{suffix}",
            zone_id=zone_id,
            task_type="action_recommendation",
            runtime_mode="shadow",
            status="evaluated",
            model_id="pepper-ops-local-stub",
            prompt_version="sft_v10",
            raw_output_json=json.dumps({"raw_text": "pg smoke"}, ensure_ascii=False),
            parsed_output_json=json.dumps({"decision": "pass"}, ensure_ascii=False),
            validated_output_json=json.dumps(
                {"decision": "pass", "recommended_actions": []},
                ensure_ascii=False,
            ),
            zone_state_json=json.dumps(
                {"current_state": {"summary": "pg smoke"}},
                ensure_ascii=False,
            ),
            citations_json=json.dumps([], ensure_ascii=False),
            retrieval_context_json=json.dumps([], ensure_ascii=False),
            audit_path="/tmp/pg-smoke-audit.jsonl",
            validator_reason_codes_json=json.dumps([], ensure_ascii=False),
        )
        session.add(decision)
        session.flush()

        alert = AlertRecord(
            decision_id=decision.id,
            zone_id=zone_id,
            alert_type="smoke",
            severity="low",
            status="open",
            summary="pg smoke alert",
            validator_reason_codes_json=json.dumps(["SMOKE-1"], ensure_ascii=False),
            payload_json=json.dumps({"source": "pg_smoke"}, ensure_ascii=False),
        )
        session.add(alert)

        robot_task = RobotTaskRecord(
            decision_id=decision.id,
            zone_id=zone_id,
            candidate_id=None,
            task_type="smoke_inspection",
            priority="low",
            approval_required=False,
            status="pending",
            reason="pg smoke",
            target_json=json.dumps({"zone_id": zone_id}, ensure_ascii=False),
            payload_json=json.dumps({"source": "pg_smoke"}, ensure_ascii=False),
        )
        session.add(robot_task)

        session.commit()
        round_trip["decision_id"] = decision.id
        round_trip["alert_id"] = alert.id
        round_trip["robot_task_id"] = robot_task.id
    except Exception as exc:
        session.rollback()
        errors.append(f"round trip insert failed: {exc}")
        return round_trip
    finally:
        session.close()

    session = session_factory()
    try:
        reread = session.execute(
            select(DecisionRecord).where(DecisionRecord.id == round_trip.get("decision_id"))
        ).scalar_one_or_none()
        if reread is None:
            errors.append("inserted decision should be selectable")
            return round_trip
        validated = json.loads(reread.validated_output_json)
        if validated.get("decision") != "pass":
            errors.append("decision.validated_output_json did not round-trip")
        if not isinstance(reread.created_at, datetime):
            errors.append("decision.created_at should materialize as datetime")

        latest_alert = session.execute(
            select(AlertRecord).order_by(desc(AlertRecord.id)).limit(1)
        ).scalar_one_or_none()
        if latest_alert is None or json.loads(latest_alert.payload_json).get("source") != "pg_smoke":
            errors.append("alert.payload_json did not round-trip")

        latest_robot = session.execute(
            select(RobotTaskRecord).order_by(desc(RobotTaskRecord.id)).limit(1)
        ).scalar_one_or_none()
        if latest_robot is None or json.loads(latest_robot.target_json).get("zone_id") != reread.zone_id:
            errors.append("robot_task.target_json did not round-trip")

        # Clean up so repeated runs don't leak smoke rows
        if latest_robot is not None:
            session.delete(latest_robot)
        if latest_alert is not None:
            session.delete(latest_alert)
        session.delete(reread)
        session.commit()
    finally:
        session.close()

    return round_trip


def main() -> int:
    errors: list[str] = []
    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        return _blocked(
            "postgres URL is not configured",
            {"expected_env": ["OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"]},
        )

    try:
        import psycopg  # noqa: F401
    except Exception:
        try:
            import psycopg2  # noqa: F401
        except Exception:
            return _blocked(
                "postgres driver is missing",
                {"required_drivers": ["psycopg", "psycopg2"]},
            )

    with tempfile.TemporaryDirectory(prefix="ops-api-postgres-smoke-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        settings = Settings(
            database_url=postgres_url,
            runtime_mode_path=tmp_path / "runtime_mode.json",
            auth_mode="disabled",
            auth_tokens_json="",
            shadow_audit_log_path=tmp_path / "shadow.jsonl",
            validator_audit_log_path=tmp_path / "validator.jsonl",
            llm_provider="stub",
            llm_model_id="pepper-ops-local-stub",
            llm_prompt_version="sft_v10",
            llm_timeout_seconds=5.0,
            llm_max_retries=1,
        )
        app = create_app(settings=settings)
        services = app.state.services
        session = services.session_factory()
        seeded: dict[str, int] = {}
        try:
            seeded = {
                "zones": session.query(ZoneRecord).count(),
                "sensors": session.query(SensorRecord).count(),
                "devices": session.query(DeviceRecord).count(),
                "policies": session.query(PolicyRecord).count(),
            }
            if seeded["zones"] < 1:
                errors.append("expected seeded zones on postgres")
            if seeded["sensors"] < 1:
                errors.append("expected seeded sensors on postgres")
            if seeded["devices"] < 1:
                errors.append("expected seeded devices on postgres")
            if seeded["policies"] < 1:
                errors.append("expected seeded policies on postgres")
        finally:
            session.close()

        round_trip = _exercise_write_round_trip(services.session_factory, errors)

    print(
        json.dumps(
            {
                "errors": errors,
                "status": "ok" if not errors else "failed",
                "database_url_kind": "postgres",
                "seeded_counts": seeded,
                "round_trip": round_trip,
                "checked_at": datetime.now(UTC).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
