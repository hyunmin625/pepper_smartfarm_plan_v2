#!/usr/bin/env python3
"""Validate Phase P-3 automation trigger review endpoints.

Exercises:

1. GET /automation/triggers?status=approval_pending returns only the
   pending rows (newer first).
2. POST /automation/triggers/{id}/approve transitions the row to
   ``approved`` and stamps reviewed_by / reviewed_at.
3. POST /automation/triggers/{id}/reject transitions another row to
   ``rejected`` with review_reason captured.
4. Approving a row that is not ``approval_pending`` returns 409.
5. Approving a non-existent trigger returns 404.

Runs against the configured ``pepper_ops`` database via the same
suffix-scoped cleanup pattern as
``scripts/validate_ops_api_automation_runner.py``.
"""

from __future__ import annotations

import os
import secrets
import sys
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.automation_runner import AutomationRunner  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import (  # noqa: E402
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    SensorReadingRecord,
    utc_now,
)
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_automation_review] SKIP: set OPS_API_DATABASE_URL or "
            "OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


@contextmanager
def _scoped_smoke_run():
    base_url = _resolve_base_postgres_url()
    suffix = secrets.token_hex(4)
    session_factory = build_session_factory(base_url)
    init_db(session_factory)
    try:
        yield base_url, suffix
    finally:
        session = session_factory()
        try:
            session.query(AutomationRuleRecord).filter(
                AutomationRuleRecord.rule_id.like(f"%{suffix}")
            ).delete(synchronize_session=False)
            session.query(SensorReadingRecord).filter(
                SensorReadingRecord.zone_id.like(f"%{suffix}")
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _make_settings(tmp_root: Path, database_url: str) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="p3")
    return Settings(
        database_url=database_url,
        runtime_mode_path=mode_path,
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_root / "shadow.jsonl",
        validator_audit_log_path=tmp_root / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        retriever_type="keyword",
        retriever_rag_index_path="",
        automation_enabled=False,
    )


def _seed_rule(
    session_factory,
    *,
    suffix: str,
    sensor_key: str,
    threshold: float,
) -> int:
    session = session_factory()
    try:
        rule = AutomationRuleRecord(
            rule_id=f"p3-smoke-{suffix}-{secrets.token_hex(2)}",
            name=f"p3 smoke {suffix} {sensor_key}",
            description="",
            zone_id=f"gh-01-zone-a-{suffix}",
            sensor_key=sensor_key,
            operator="gt",
            threshold_value=threshold,
            threshold_min=None,
            threshold_max=None,
            hysteresis_value=None,
            cooldown_minutes=60,
            target_device_type="roof_vent",
            target_device_id=None,
            target_action="close_vent",
            action_payload_json="{}",
            priority=10,
            enabled=1,
            runtime_mode_gate="approval",
            owner_role="operator",
            created_by="smoke",
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule.id
    finally:
        session.close()


def _seed_reading(
    session_factory,
    *,
    suffix: str,
    sensor_key: str,
    value: float,
) -> None:
    session = session_factory()
    try:
        measured_at = utc_now() - timedelta(seconds=1)
        reading = SensorReadingRecord(
            measured_at=measured_at,
            ingested_at=measured_at,
            site_id="gh-01",
            zone_id=f"gh-01-zone-a-{suffix}",
            record_kind="sensor",
            source_id="p3-smoke",
            source_type="climate",
            metric_name=sensor_key,
            metric_value_double=value,
            metric_value_text=None,
            unit=None,
            quality_flag="good",
            transport_status="ok",
            source="smoke",
            metadata_json="{}",
        )
        session.add(reading)
        session.commit()
    finally:
        session.close()


def _run_tick_return_trigger_ids(session_factory, settings, rule_pks: list[int]) -> list[int]:
    runner = AutomationRunner(session_factory=session_factory, settings=settings)
    runner.run_once()
    session = session_factory()
    try:
        rows = (
            session.query(AutomationRuleTriggerRecord)
            .filter(AutomationRuleTriggerRecord.rule_id.in_(rule_pks))
            .order_by(AutomationRuleTriggerRecord.id.asc())
            .all()
        )
        return [r.id for r in rows]
    finally:
        session.close()


def test_trigger_list_and_review_flow(db_url: str, suffix: str) -> None:
    print("[test] approve/reject cycle and filtered list")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = _make_settings(tmp_root, db_url)
        session_factory = build_session_factory(settings.database_url)

        rule_pk_a = _seed_rule(
            session_factory, suffix=suffix, sensor_key="air_temp_c", threshold=30.0
        )
        rule_pk_b = _seed_rule(
            session_factory,
            suffix=suffix,
            sensor_key="rh_pct",
            threshold=70.0,
        )
        _seed_reading(
            session_factory, suffix=suffix, sensor_key="air_temp_c", value=32.5
        )
        _seed_reading(
            session_factory, suffix=suffix, sensor_key="rh_pct", value=85.0
        )
        trigger_ids = _run_tick_return_trigger_ids(
            session_factory, settings, rule_pks=[rule_pk_a, rule_pk_b]
        )
        _assert(len(trigger_ids) == 2, "two pending triggers seeded")

        app = create_app(settings=settings)
        zone = f"gh-01-zone-a-{suffix}"
        with TestClient(app) as client:
            response = client.get(
                "/automation/triggers",
                params={"status": "approval_pending", "zone_id": zone, "limit": 50},
            )
            _assert(response.status_code == 200, "list endpoint returns 200")
            payload = response.json()
            scoped = [
                t for t in payload["data"]["triggers"] if t["id"] in trigger_ids
            ]
            _assert(len(scoped) == 2, "filter returns our two triggers")
            _assert(
                all(t["status"] == "approval_pending" for t in scoped),
                "all filtered rows are approval_pending",
            )

            approve_id = trigger_ids[0]
            reject_id = trigger_ids[1]

            approve_resp = client.post(
                f"/automation/triggers/{approve_id}/approve",
                json={"reason": "smoke approves this rule"},
            )
            _assert(approve_resp.status_code == 200, "approve returns 200")
            approved = approve_resp.json()["data"]
            _assert(approved["status"] == "approved", "trigger row now approved")
            _assert(approved["reviewed_by"], "reviewed_by stamped")
            _assert(approved["reviewed_at"] is not None, "reviewed_at stamped")
            _assert(
                approved["review_reason"] == "smoke approves this rule",
                "review_reason captured",
            )

            reject_resp = client.post(
                f"/automation/triggers/{reject_id}/reject",
                json={"reason": "false positive"},
            )
            _assert(reject_resp.status_code == 200, "reject returns 200")
            rejected = reject_resp.json()["data"]
            _assert(rejected["status"] == "rejected", "trigger row now rejected")
            _assert(
                rejected["review_reason"] == "false positive",
                "reject reason captured",
            )

            repeat = client.post(
                f"/automation/triggers/{approve_id}/approve",
                json={"reason": ""},
            )
            _assert(
                repeat.status_code == 409,
                "re-approving already-approved trigger returns 409",
            )

            missing = client.post(
                "/automation/triggers/999999999/approve",
                json={"reason": ""},
            )
            _assert(
                missing.status_code == 404,
                "approving unknown trigger returns 404",
            )

            pending_only = client.get(
                "/automation/triggers",
                params={"status": "approval_pending", "zone_id": zone},
            )
            remaining = [
                t for t in pending_only.json()["data"]["triggers"]
                if t["id"] in trigger_ids
            ]
            _assert(
                remaining == [],
                "no remaining approval_pending rows for this zone",
            )


def main() -> int:
    with _scoped_smoke_run() as (db_url, suffix):
        test_trigger_list_and_review_flow(db_url, suffix)
    print("[validate_ops_api_automation_review] all invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
