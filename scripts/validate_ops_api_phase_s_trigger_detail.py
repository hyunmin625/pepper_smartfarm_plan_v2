#!/usr/bin/env python3
"""Smoke-verify the Phase S automation trigger detail drawer.

Phase S wires the ``GET /automation/triggers/{id}`` endpoint (Phase R-3)
to the dashboard UI so operators can inspect the rule + linked
DecisionRecord + device_commands + alerts for a single trigger without
leaving the automation view.

Checks:

1. Dashboard HTML carries every Phase S hook (drawer shell, JS handlers,
   detail button on trigger rows).
2. A trigger with no linked decision (status=approval_pending) returns a
   sane payload where ``decision`` is null but ``rule`` is populated.
3. Seeding a ``decision_id`` on the trigger makes the detail endpoint
   surface the linked DecisionRecord with its device_commands / alerts
   (via the Phase R-1 ``AutomationRuleTriggerRecord.decision`` backref).

Uses a SQLite-backed Settings fixture so this smoke runs without the
shared Postgres database — complements the Postgres-only
``validate_ops_api_automation_phase_r.py``.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import (  # noqa: E402
    AlertRecord,
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    DecisionRecord,
    DeviceCommandRecord,
    ZoneRecord,
    utc_now,
)
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


DASHBOARD_HTML_HOOKS = [
    'id="automationTriggerDetailDrawer"',
    'id="automationTriggerDetailBody"',
    'id="automationTriggerDetailTitle"',
    'id="automationTriggerDetailError"',
    "async function openAutomationTriggerDetail",
    "function closeAutomationTriggerDetail",
    "function renderAutomationTriggerDetail",
    'onclick="openAutomationTriggerDetail(',
    "linked decision",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_phase_s_trigger_detail] SKIP: set OPS_API_DATABASE_URL "
            "or OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


@contextmanager
def _scoped_smoke_run(suffix: str):
    base_url = _resolve_base_postgres_url()
    session_factory = build_session_factory(base_url)
    init_db(session_factory)
    try:
        yield base_url, session_factory
    finally:
        session = session_factory()
        try:
            session.query(AlertRecord).filter(
                AlertRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(AutomationRuleRecord).filter(
                AutomationRuleRecord.rule_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(DecisionRecord).filter(
                DecisionRecord.request_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(ZoneRecord).filter(
                ZoneRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()


def _make_settings(tmp_root: Path, database_url: str) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="phase_s")
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


def _seed_rule_and_trigger(
    session_factory,
    *,
    suffix: str,
    with_linked_decision: bool,
) -> tuple[int, int | None]:
    """Return (trigger_pk, decision_pk_or_None).

    For the no-decision case we leave ``decision_id`` null; for the
    linked case we insert a synthetic DecisionRecord + a DeviceCommand +
    an Alert so the detail endpoint has a full chain to surface.
    """

    zone_id = f"gh-01-zone-a-{suffix}"
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
                    description="phase s smoke synthetic",
                    metadata_json="{}",
                )
            )
            session.commit()
        variant = "linked" if with_linked_decision else "pending"
        rule = AutomationRuleRecord(
            rule_id=f"phase-s-smoke-{suffix}-{variant}",
            name=f"phase s smoke {suffix} {variant}",
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

        decision_pk: int | None = None
        if with_linked_decision:
            decision = DecisionRecord(
                request_id=f"automation-phase-s-{suffix}-{secrets.token_hex(2)}",
                zone_id=zone_id,
                task_type="automation_rule",
                runtime_mode="approval",
                status="approved_executed",
                model_id="automation_runner",
                prompt_version="automation_runner_v1",
                raw_output_json="{}",
                parsed_output_json="{}",
                validated_output_json="{}",
                zone_state_json="{}",
                citations_json="[]",
                retrieval_context_json="{}",
                audit_path="",
                validator_reason_codes_json="[]",
            )
            session.add(decision)
            session.flush()
            decision_pk = decision.id
            session.add(
                DeviceCommandRecord(
                    decision_id=decision.id,
                    command_kind="device_command",
                    target_id="gh-01-zone-a--vent-window--01",
                    action_type="adjust_vent",
                    status="acknowledged",
                    payload_json="{}",
                    adapter_result_json="{}",
                )
            )
            session.add(
                AlertRecord(
                    decision_id=decision.id,
                    zone_id=zone_id,
                    alert_type="automation_dispatched",
                    severity="info",
                    status="active",
                    summary="smoke alert",
                    validator_reason_codes_json="[]",
                    payload_json="{}",
                )
            )
            session.commit()

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
                        "target_id": "gh-01-zone-a--vent-window--01",
                    },
                    "payload": {"position_pct": 0},
                    "priority": 10,
                    "approval_required": True,
                }
            ),
            status="dispatched" if with_linked_decision else "approval_pending",
            runtime_mode="approval",
            decision_id=decision_pk,
            note="smoke",
            reviewed_by="smoke-operator" if with_linked_decision else None,
            reviewed_at=utc_now() if with_linked_decision else None,
            review_reason="smoke approves" if with_linked_decision else "",
        )
        session.add(trigger)
        session.commit()
        session.refresh(trigger)
        return trigger.id, decision_pk
    finally:
        session.close()


def main() -> int:
    suffix = secrets.token_hex(4)
    with _scoped_smoke_run(suffix) as (db_url, session_factory):
        with tempfile.TemporaryDirectory(prefix="ops-api-phase-s-") as tmp:
            tmp_root = Path(tmp)
            settings = _make_settings(tmp_root, db_url)

            app = create_app(settings=settings)
            client = TestClient(app)

            print("[1] GET /dashboard — Phase S UI hooks")
            res = client.get("/dashboard")
            _assert(res.status_code == 200, f"/dashboard status 200 (got {res.status_code})")
            html = res.text
            for hook in DASHBOARD_HTML_HOOKS:
                _assert(hook in html, f"dashboard html contains `{hook}`")

            print()
            print("[2] GET /automation/triggers/{id} — pending trigger, no decision link")
            trigger_pending_pk, _ = _seed_rule_and_trigger(
                session_factory, suffix=suffix, with_linked_decision=False
            )
            res = client.get(f"/automation/triggers/{trigger_pending_pk}")
            _assert(res.status_code == 200, "detail endpoint 200 for pending trigger")
            payload = res.json()["data"]
            _assert(payload["id"] == trigger_pending_pk, "payload id matches")
            _assert(payload["status"] == "approval_pending", "status propagated")
            _assert(payload["rule"] is not None, "rule sub-object populated")
            _assert(
                payload["rule"]["rule_id"].startswith("phase-s-smoke-"),
                "rule.rule_id propagated",
            )
            _assert(payload["decision"] is None, "decision null when no FK yet")

            print()
            print("[3] GET /automation/triggers/{id} — dispatched trigger surfaces decision chain")
            trigger_linked_pk, decision_pk = _seed_rule_and_trigger(
                session_factory, suffix=suffix, with_linked_decision=True
            )
            res = client.get(f"/automation/triggers/{trigger_linked_pk}")
            _assert(res.status_code == 200, "detail endpoint 200 for dispatched trigger")
            payload = res.json()["data"]
            _assert(payload["decision"] is not None, "decision populated via backref")
            decision = payload["decision"]
            _assert(decision["id"] == decision_pk, "decision.id matches seeded pk")
            _assert(
                decision["task_type"] == "automation_rule",
                "decision.task_type = automation_rule",
            )
            _assert(
                decision["model_id"] == "automation_runner",
                "decision.model_id = automation_runner",
            )
            _assert(
                len(decision["device_commands"]) == 1,
                "one device_command surfaced",
            )
            _assert(
                decision["device_commands"][0]["action_type"] == "adjust_vent",
                "device_command.action_type round-trips",
            )
            _assert(len(decision["alerts"]) == 1, "one alert surfaced")
            _assert(
                decision["alerts"][0]["alert_type"] == "automation_dispatched",
                "alert.alert_type round-trips",
            )

            print()
            print("[4] GET /automation/triggers/99999999 — 404 on unknown id")
            res = client.get("/automation/triggers/99999999")
            _assert(res.status_code == 404, "unknown trigger returns 404")

    print()
    print("all Phase S invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
