#!/usr/bin/env python3
"""Validate Phase Q automation dispatch flush.

Exercises ``dispatch_approved_triggers`` directly and via
``AutomationRunner.run_once`` with a dispatcher:

1. A trigger sitting at ``status='approved'`` transitions to
   ``dispatched`` (or ``blocked_guard``/``dispatch_fault`` based on the
   dispatcher verdict) and a linked synthetic DecisionRecord +
   DeviceCommandRecord are persisted.
2. Running the runner tick with a dispatcher causes the same flush as
   a direct module call (so operators don't need to hit an extra API).
3. Triggers at any other status are untouched.

Runs on the shared ``pepper_ops`` database using suffix-scoped cleanup.
"""

from __future__ import annotations

import json
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
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402

from ops_api.automation_dispatcher import dispatch_approved_triggers  # noqa: E402
from ops_api.automation_runner import AutomationRunner  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import (  # noqa: E402
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    DecisionRecord,
    DeviceCommandRecord,
    SensorReadingRecord,
    utc_now,
)
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_automation_dispatch] SKIP: set OPS_API_DATABASE_URL or "
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
            session.query(DecisionRecord).filter(
                DecisionRecord.request_id.like(f"automation-%{suffix}%")
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
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="phase_q")
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


def _seed_approved_trigger(session_factory, *, suffix: str) -> tuple[int, int]:
    session = session_factory()
    try:
        rule = AutomationRuleRecord(
            rule_id=f"q-smoke-{suffix}-{secrets.token_hex(2)}",
            name=f"q smoke {suffix}",
            description="",
            zone_id=f"gh-01-zone-a-{suffix}",
            sensor_key="air_temp_c",
            operator="gt",
            threshold_value=30.0,
            threshold_min=None,
            threshold_max=None,
            hysteresis_value=None,
            cooldown_minutes=60,
            target_device_type="vent_window",
            target_device_id="gh-01-zone-a--vent-window--01",
            target_action="adjust_vent",
            action_payload_json=json.dumps({"position_pct": 0}),
            priority=10,
            enabled=1,
            runtime_mode_gate="approval",
            owner_role="operator",
            created_by="smoke",
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        trigger = AutomationRuleTriggerRecord(
            rule_id=rule.id,
            zone_id=f"gh-01-zone-a-{suffix}",
            sensor_key="air_temp_c",
            matched_value=32.5,
            sensor_snapshot_json=json.dumps({"air_temp_c": 32.5}),
            proposed_action_json=json.dumps(
                {
                    "action_type": "adjust_vent",
                    "target": {
                        "target_type": "vent_window",
                        "target_id": "gh-01-zone-a--vent-window--01",
                    },
                    "trigger": {
                        "source": "automation_rule",
                        "rule_id": rule.rule_id,
                        "sensor_key": "air_temp_c",
                        "matched_value": 32.5,
                        "operator": "gt",
                    },
                    "payload": {"position_pct": 0},
                    "priority": 10,
                    "approval_required": True,
                }
            ),
            status="approved",
            runtime_mode="approval",
            decision_id=None,
            note="",
            reviewed_by="smoke-operator",
            reviewed_at=utc_now() - timedelta(seconds=5),
            review_reason="smoke approves",
        )
        session.add(trigger)
        session.commit()
        session.refresh(trigger)
        return rule.id, trigger.id
    finally:
        session.close()


def test_direct_dispatch(db_url: str, suffix: str) -> None:
    print("[test] dispatch_approved_triggers flushes approved row")
    with tempfile.TemporaryDirectory() as tmp:
        settings = _make_settings(Path(tmp), db_url)
        session_factory = build_session_factory(settings.database_url)
        rule_pk, trigger_pk = _seed_approved_trigger(session_factory, suffix=suffix)

        dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
        session = session_factory()
        try:
            summaries = dispatch_approved_triggers(session, dispatcher)
        finally:
            session.close()

        scoped = [s for s in summaries if s.trigger_id == trigger_pk]
        _assert(len(scoped) == 1, "summary captured for seeded trigger")
        _assert(
            scoped[0].status in {"dispatched", "blocked_guard", "dispatch_fault"},
            f"status transitioned to terminal (got {scoped[0].status})",
        )
        _assert(scoped[0].decision_id is not None, "synthetic DecisionRecord created")

        verify = session_factory()
        try:
            refreshed = verify.get(AutomationRuleTriggerRecord, trigger_pk)
            _assert(refreshed is not None, "trigger still present")
            _assert(refreshed.status != "approved", "trigger moved off approved")
            _assert(refreshed.decision_id is not None, "trigger.decision_id linked")

            decision = verify.get(DecisionRecord, refreshed.decision_id)
            _assert(decision is not None, "synthetic DecisionRecord row exists")
            _assert(decision.task_type == "automation_rule", "task_type tagged")
            _assert(decision.model_id == "automation_runner", "model_id tagged")

            cmd_rows = (
                verify.query(DeviceCommandRecord)
                .filter(DeviceCommandRecord.decision_id == decision.id)
                .all()
            )
            _assert(len(cmd_rows) == 1, "one DeviceCommandRecord written")
            _assert(
                cmd_rows[0].action_type == "adjust_vent",
                "command captures action_type",
            )
        finally:
            verify.close()


def test_runner_tick_flushes(db_url: str, suffix: str) -> None:
    print("[test] AutomationRunner tick flushes approved trigger via dispatcher")
    with tempfile.TemporaryDirectory() as tmp:
        settings = _make_settings(Path(tmp), db_url)
        session_factory = build_session_factory(settings.database_url)
        rule_pk, trigger_pk = _seed_approved_trigger(session_factory, suffix=suffix)

        dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
        runner = AutomationRunner(
            session_factory=session_factory,
            settings=settings,
            dispatcher=dispatcher,
        )
        results = runner.run_once()
        dispatched = [
            s for tick in results for s in tick.dispatched if s.trigger_id == trigger_pk
        ]
        _assert(len(dispatched) == 1, "runner tick emitted dispatch summary")

        verify = session_factory()
        try:
            refreshed = verify.get(AutomationRuleTriggerRecord, trigger_pk)
            _assert(refreshed.status != "approved", "trigger status advanced")
            _assert(refreshed.decision_id is not None, "decision linked")
        finally:
            verify.close()


def test_non_approved_rows_untouched(db_url: str, suffix: str) -> None:
    print("[test] dispatcher ignores non-approved triggers")
    with tempfile.TemporaryDirectory() as tmp:
        settings = _make_settings(Path(tmp), db_url)
        session_factory = build_session_factory(settings.database_url)
        session = session_factory()
        try:
            rule = AutomationRuleRecord(
                rule_id=f"q-noop-{suffix}-{secrets.token_hex(2)}",
                name="noop",
                description="",
                zone_id=f"gh-01-zone-a-{suffix}",
                sensor_key="air_temp_c",
                operator="gt",
                threshold_value=30.0,
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
            pending = AutomationRuleTriggerRecord(
                rule_id=rule.id,
                zone_id=rule.zone_id,
                sensor_key="air_temp_c",
                matched_value=31.0,
                sensor_snapshot_json="{}",
                proposed_action_json="{}",
                status="approval_pending",
                runtime_mode="approval",
            )
            session.add(pending)
            session.commit()
            session.refresh(pending)
            pending_pk = pending.id
        finally:
            session.close()

        dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
        session = session_factory()
        try:
            summaries = dispatch_approved_triggers(session, dispatcher)
        finally:
            session.close()

        _assert(
            all(s.trigger_id != pending_pk for s in summaries),
            "pending trigger not touched by dispatcher",
        )

        verify = session_factory()
        try:
            refreshed = verify.get(AutomationRuleTriggerRecord, pending_pk)
            _assert(
                refreshed.status == "approval_pending",
                "pending status preserved",
            )
        finally:
            verify.close()


def main() -> int:
    tests = [
        ("direct_dispatch", test_direct_dispatch),
        ("runner_tick_flushes", test_runner_tick_flushes),
        ("non_approved_untouched", test_non_approved_rows_untouched),
    ]
    for _name, fn in tests:
        with _scoped_smoke_run() as (db_url, suffix):
            fn(db_url, suffix)
    print("[validate_ops_api_automation_dispatch] all invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
