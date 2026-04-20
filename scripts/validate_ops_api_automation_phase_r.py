#!/usr/bin/env python3
"""Validate Phase R automation ↔ decision cross-visibility.

Exercises three invariants that only become testable after Phase R wires
the AutomationRuleTriggerRecord ↔ DecisionRecord backref and the
automation_rule task_type into the shadow window summary:

1. After Phase Q dispatch, ``trigger.decision`` and
   ``decision.automation_triggers`` navigate in both directions.
2. ``collect_automation_stats`` counts triggers inside a window and
   reports status distribution + linked DecisionRecord count, and
   ``build_window_summary`` surfaces ``task_type_distribution`` +
   ``automation_stats`` on the returned dict.
3. ``GET /automation/triggers/{trigger_id}`` returns the linked
   synthetic DecisionRecord with its device_commands / alerts children,
   proving the backref is usable from HTTP.

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

from fastapi.testclient import TestClient  # noqa: E402

from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.automation_dispatcher import dispatch_approved_triggers  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import (  # noqa: E402
    AlertRecord,
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    DecisionRecord,
    DeviceCommandRecord,
    SensorReadingRecord,
    ZoneRecord,
    utc_now,
)
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402
from ops_api.shadow_mode import (  # noqa: E402
    build_window_summary,
    build_window_summary_from_paths,
    collect_automation_stats,
)


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_automation_phase_r] SKIP: set OPS_API_DATABASE_URL or "
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
            session.query(AlertRecord).filter(
                AlertRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(AutomationRuleRecord).filter(
                AutomationRuleRecord.rule_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(SensorReadingRecord).filter(
                SensorReadingRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(DecisionRecord).filter(
                DecisionRecord.request_id.like(f"automation-%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(ZoneRecord).filter(
                ZoneRecord.zone_id.like(f"%{suffix}%")
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
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="phase_r")
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


def _seed_approved_trigger(
    session_factory,
    *,
    suffix: str,
) -> tuple[int, int, str]:
    zone_id = f"gh-01-zone-a-{suffix}"
    # Catalog-known device id so the execution_gateway mock adapter can
    # actually accept the command; the suffix lives on the zone_id for
    # cleanup scoping, not on the device_id.
    device_id = "gh-01-zone-a--vent-window--01"
    session = session_factory()
    try:
        existing_zone = (
            session.query(ZoneRecord).filter(ZoneRecord.zone_id == zone_id).one_or_none()
        )
        if existing_zone is None:
            session.add(
                ZoneRecord(
                    zone_id=zone_id,
                    zone_type="greenhouse",
                    priority="normal",
                    description="phase r smoke synthetic",
                    metadata_json="{}",
                )
            )
            session.commit()
        rule = AutomationRuleRecord(
            rule_id=f"r-smoke-{suffix}-{secrets.token_hex(2)}",
            name=f"phase r smoke {suffix}",
            description="",
            zone_id=zone_id,
            sensor_key="air_temp_c",
            operator="gt",
            threshold_value=30.0,
            threshold_min=None,
            threshold_max=None,
            hysteresis_value=None,
            cooldown_minutes=60,
            target_device_type="vent_window",
            target_device_id=device_id,
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
            zone_id=zone_id,
            sensor_key="air_temp_c",
            matched_value=32.5,
            sensor_snapshot_json=json.dumps({"air_temp_c": 32.5}),
            proposed_action_json=json.dumps(
                {
                    "action_type": "adjust_vent",
                    "target": {
                        "target_type": "vent_window",
                        "target_id": device_id,
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
        return rule.id, trigger.id, zone_id
    finally:
        session.close()


def _dispatch(session_factory, trigger_pk: int) -> None:
    dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
    session = session_factory()
    try:
        dispatch_approved_triggers(session, dispatcher, trigger_ids=[trigger_pk])
    finally:
        session.close()


def test_bidirectional_backref(db_url: str, suffix: str) -> None:
    print("[test] trigger.decision ↔ decision.automation_triggers navigate both ways")
    with tempfile.TemporaryDirectory() as tmp:
        _settings = _make_settings(Path(tmp), db_url)
        session_factory = build_session_factory(db_url)
        _rule_pk, trigger_pk, _zone_id = _seed_approved_trigger(
            session_factory, suffix=suffix
        )
        _dispatch(session_factory, trigger_pk)

        session = session_factory()
        try:
            refreshed = session.get(AutomationRuleTriggerRecord, trigger_pk)
            _assert(refreshed is not None, "trigger row still present")
            _assert(
                refreshed.decision_id is not None,
                "decision_id FK populated by dispatcher",
            )
            linked_decision = refreshed.decision
            _assert(
                linked_decision is not None,
                "trigger.decision backref loads DecisionRecord",
            )
            _assert(
                linked_decision.task_type == "automation_rule",
                "linked decision carries automation_rule task_type",
            )
            _assert(
                linked_decision.model_id == "automation_runner",
                "linked decision carries automation_runner model_id",
            )

            reverse = linked_decision.automation_triggers
            _assert(
                any(t.id == trigger_pk for t in reverse),
                "decision.automation_triggers includes the source trigger",
            )
        finally:
            session.close()


def test_shadow_window_automation_stats(db_url: str, suffix: str) -> None:
    print("[test] collect_automation_stats + build_window_summary surface triggers")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        _settings = _make_settings(tmp_root, db_url)
        session_factory = build_session_factory(db_url)
        window_start_dt = utc_now() - timedelta(minutes=5)
        _rule_pk, trigger_pk, _zone_id = _seed_approved_trigger(
            session_factory, suffix=suffix
        )
        _dispatch(session_factory, trigger_pk)
        window_end_dt = utc_now() + timedelta(minutes=5)

        session = session_factory()
        try:
            stats = collect_automation_stats(
                session,
                window_start=window_start_dt.isoformat(),
                window_end=window_end_dt.isoformat(),
            )
        finally:
            session.close()

        _assert(stats["trigger_count"] >= 1, "stats include our seeded trigger")
        _assert(stats["linked_decision_count"] >= 1, "linked_decision_count counts dispatched trigger")
        statuses = dict(stats["status_distribution"])
        _assert(
            any(
                status in statuses
                for status in ("dispatched", "blocked_guard", "dispatch_fault")
            ),
            "status distribution includes a terminal status",
        )

        # Build a single synthetic shadow row tagged automation_rule so the
        # task_type_distribution aggregator has something to report. Writing
        # one row directly to a JSONL file avoids dragging in a full
        # LLMDecisionEnvelope just to check the distribution key.
        shadow_path = tmp_root / "shadow.jsonl"
        shadow_row = {
            "request_id": f"shadow-auto-{suffix}",
            "created_at": utc_now().isoformat(),
            "task_type": "automation_rule",
            "eval_set_id": "phase_r_smoke",
            "zone_id": _zone_id,
            "growth_stage": "vegetative",
            "model_id": "automation_runner",
            "prompt_id": "automation_runner_v1",
            "operator_agreement": True,
            "critical_disagreement": False,
            "citation_required": False,
            "citation_present": False,
            "schema_pass": True,
            "retrieval_hit": True,
            "validator_decision": "pass",
            "blocked_action_recommendation_count": 0,
            "approval_missing_count": 0,
            "manual_override_used": False,
        }
        shadow_path.write_text(
            json.dumps(shadow_row, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        summary = build_window_summary_from_paths(
            [shadow_path],
            automation_stats=stats,
        )
        task_type_dist = dict(summary["task_type_distribution"])
        _assert(
            task_type_dist.get("automation_rule") == 1,
            "task_type_distribution counts automation_rule row",
        )
        _assert(
            summary["automation_stats"]["trigger_count"] == stats["trigger_count"],
            "build_window_summary echoes injected automation_stats",
        )

        # Default path (no automation_stats forwarded) must still include the
        # field with zero counts so downstream consumers never see a KeyError.
        bare = build_window_summary([shadow_row], [str(shadow_path)])
        _assert(
            bare["automation_stats"]["trigger_count"] == 0,
            "automation_stats defaults to zero counts when omitted",
        )


def test_trigger_detail_endpoint(db_url: str, suffix: str) -> None:
    print("[test] GET /automation/triggers/{id} surfaces linked decision + commands")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = _make_settings(tmp_root, db_url)
        session_factory = build_session_factory(db_url)
        _rule_pk, trigger_pk, _zone_id = _seed_approved_trigger(
            session_factory, suffix=suffix
        )
        _dispatch(session_factory, trigger_pk)

        app = create_app(settings=settings)
        with TestClient(app) as client:
            response = client.get(f"/automation/triggers/{trigger_pk}")
            _assert(response.status_code == 200, "detail endpoint returns 200")
            payload = response.json()["data"]
            _assert(payload["id"] == trigger_pk, "payload id matches seeded trigger")
            _assert(payload["rule"] is not None, "rule sub-object included")
            _assert(
                payload["decision"] is not None,
                "decision sub-object populated via backref",
            )
            decision = payload["decision"]
            _assert(
                decision["task_type"] == "automation_rule",
                "detail decision.task_type = automation_rule",
            )
            _assert(
                decision["model_id"] == "automation_runner",
                "detail decision.model_id = automation_runner",
            )
            _assert(
                isinstance(decision["device_commands"], list)
                and len(decision["device_commands"]) == 1,
                "exactly one DeviceCommandRecord surfaced",
            )
            _assert(
                decision["device_commands"][0]["action_type"] == "adjust_vent",
                "device command action_type round-trips through detail endpoint",
            )

            missing = client.get("/automation/triggers/99999999")
            _assert(missing.status_code == 404, "unknown trigger id returns 404")


def main() -> int:
    tests = [
        ("bidirectional_backref", test_bidirectional_backref),
        ("shadow_window_automation_stats", test_shadow_window_automation_stats),
        ("trigger_detail_endpoint", test_trigger_detail_endpoint),
    ]
    for _name, fn in tests:
        with _scoped_smoke_run() as (db_url, suffix):
            fn(db_url, suffix)
    print("[validate_ops_api_automation_phase_r] all invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
