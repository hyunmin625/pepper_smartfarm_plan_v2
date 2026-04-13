#!/usr/bin/env python3
"""End-to-end smoke: LLM orchestrator -> planner -> execution-gateway.

This script exercises the contract between the llm-orchestrator
validated output and the execution-gateway dispatcher without any
real network or database. Three scenarios are covered against the
same sensor snapshot shape that ``POST /decisions/evaluate-zone``
builds internally:

1. *Stub LLM baseline* – the repository's stub completion client
   returns create_alert + request_human_check for an
   ``action_recommendation`` task. Neither is dispatchable, so the
   planner should emit two ``log_only`` plans and no dispatcher
   invocation should run.

2. *Adjust fan dispatch* – a fixed completion client forces the
   orchestrator to emit an ``adjust_fan`` recommendation. The
   planner must convert it to a device_command targeting a
   real circulation fan in zone-a, and the dispatcher must
   acknowledge it through the mock PLC adapter.

3. *Pause automation override* – a fixed completion client emits
   ``pause_automation``. The planner must convert it to a
   control_override request, and the dispatcher must apply the
   override via ControlStateStore so status becomes
   ``state_updated``.

The smoke asserts observable contract invariants (plan kind,
dispatcher status, audit row shape) so a future refactor that
silently drops one of the hops fails the gate.
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import DispatchAuditSink, ExecutionDispatcher  # noqa: E402
from llm_orchestrator.client import ModelConfig, StubCompletionClient  # noqa: E402
from llm_orchestrator.client import ModelInvocation  # noqa: E402
from llm_orchestrator.service import LLMOrchestratorService, OrchestratorRequest  # noqa: E402
from ops_api.planner import ActionDispatchPlanner  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


@dataclass
class _FixedCompletionClient:
    """Deterministic stub that returns a predetermined validated output.

    Used for scenarios that need dispatchable actions which the repo's
    default StubCompletionClient does not produce.
    """

    model_id: str
    raw_text: str

    def complete(self, *, system_prompt: str, user_message: str) -> ModelInvocation:  # noqa: D401
        return ModelInvocation(
            raw_text=self.raw_text,
            model_id=self.model_id,
            provider="fixed",
            attempts=1,
        )

    def repair_json(self, *, original_output: str, task_type: str) -> ModelInvocation:
        return ModelInvocation(
            raw_text=original_output,
            model_id=self.model_id,
            provider="fixed",
            attempts=1,
            used_repair_prompt=True,
        )


BASE_SNAPSHOT: dict[str, Any] = {
    "scenario_id": "integration-llm-to-execution",
    "zone_id": "gh-01-zone-a",
    "growth_stage": "fruiting",
    "current_state": {
        "air_temp_c": 28.0,
        "rh_pct": 68.0,
        "vpd_kpa": 1.25,
        "substrate_moisture_pct": 52.0,
        "substrate_temp_c": 22.5,
        "feed_ec_ds_m": 2.6,
        "drain_ec_ds_m": 2.75,
        "feed_ph": 5.8,
        "drain_ph": 5.9,
        "co2_ppm": 430,
        "par_umol_m2_s": 380,
    },
    "sensor_quality": {"overall": "good"},
    "device_status": {},
    "weather_context": {},
    "constraints": {},
    "history": [],
}


def _build_zone_state() -> dict[str, Any]:
    snapshot = dict(BASE_SNAPSHOT)
    zone_state = build_zone_state_payload(snapshot)
    state_estimate = estimate_zone_state(snapshot)
    zone_state["state_estimate"] = state_estimate.as_dict()
    zone_state["active_constraints"] = dict(BASE_SNAPSHOT.get("constraints") or {})
    return zone_state


def _make_orchestrator(client) -> LLMOrchestratorService:
    return LLMOrchestratorService(client=client)


def _make_request() -> OrchestratorRequest:
    return OrchestratorRequest(
        request_id="integration-llm-001",
        zone_id="gh-01-zone-a",
        task_type="action_recommendation",
        zone_state=_build_zone_state(),
        prompt_version="sft_v10",
        retrieval_limit=1,
        mode="approval",
    )


def _make_dispatcher(tmp_dir: Path) -> ExecutionDispatcher:
    audit_path = tmp_dir / "dispatch_audit.jsonl"
    dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
    dispatcher.audit_sink = DispatchAuditSink(audit_path)
    return dispatcher


def _dispatch_plans(dispatcher: ExecutionDispatcher, plans: list) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for plan in plans:
        if plan.kind == "device_command":
            result = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(plan.payload))
        elif plan.kind == "control_override":
            result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(plan.payload))
        else:
            result = None
        results.append(
            {
                "plan_kind": plan.kind,
                "plan_action_type": plan.action_type,
                "plan_target_id": plan.target_id,
                "dispatch": result.as_dict() if result is not None else None,
            }
        )
    return results


def _stub_baseline(planner: ActionDispatchPlanner, errors: list[str]) -> dict[str, Any]:
    orchestrator = _make_orchestrator(StubCompletionClient(ModelConfig(provider="stub", model_id="pepper-ops-local-stub")))
    request = _make_request()
    result = orchestrator.evaluate(request)

    action_types = [
        str(a.get("action_type") or "")
        for a in result.validated_output.get("recommended_actions") or []
    ]
    if not action_types:
        errors.append("stub orchestrator should still return recommended_actions")

    plans = planner.plan(
        decision_id=1,
        request_id=request.request_id,
        zone_id=request.zone_id,
        validated_output=result.validated_output,
        zone_state=request.zone_state,
        actor_id="integration-operator",
    )
    plan_kinds = [plan.kind for plan in plans]
    if any(kind != "log_only" for kind in plan_kinds):
        errors.append(
            f"stub baseline should only emit log_only plans, got {plan_kinds}"
        )

    return {
        "model_id": result.model_id,
        "validator_reason_codes": result.validator_reason_codes,
        "action_types": action_types,
        "plan_kinds": plan_kinds,
    }


def _adjust_fan_scenario(
    planner: ActionDispatchPlanner,
    dispatcher: ExecutionDispatcher,
    errors: list[str],
) -> dict[str, Any]:
    fixture = {
        "risk_level": "medium",
        "confidence": 0.6,
        "retrieval_coverage": "not_used",
        "citations": [],
        "follow_up": [{"type": "trend_review", "zone_id": "gh-01-zone-a"}],
        "required_follow_up": [{"type": "operator_review", "zone_id": "gh-01-zone-a"}],
        "recommended_actions": [
            {"action_type": "adjust_fan", "approval_required": False},
        ],
    }
    client = _FixedCompletionClient(
        model_id="pepper-ops-local-fixed",
        raw_text=json.dumps(fixture, ensure_ascii=False),
    )
    orchestrator = _make_orchestrator(client)
    request = _make_request()
    result = orchestrator.evaluate(request)

    plans = planner.plan(
        decision_id=2,
        request_id=request.request_id,
        zone_id=request.zone_id,
        validated_output=result.validated_output,
        zone_state=request.zone_state,
        actor_id="integration-operator",
    )
    if len(plans) != 1 or plans[0].kind != "device_command" or plans[0].action_type != "adjust_fan":
        errors.append(
            f"adjust_fan should produce exactly one device_command plan, got {[p.kind for p in plans]}"
        )
    if plans and not plans[0].target_id.startswith("gh-01-zone-a--circulation-fan"):
        errors.append(
            f"planner should resolve adjust_fan to a zone-a circulation fan, got {plans[0].target_id}"
        )

    dispatched = _dispatch_plans(dispatcher, plans)
    if len(dispatched) != 1:
        errors.append("adjust_fan scenario should dispatch exactly one plan")
    elif dispatched[0]["dispatch"] is None:
        errors.append("adjust_fan plan should reach the dispatcher (non-log_only)")
    else:
        status = dispatched[0]["dispatch"].get("status")
        if status != "acknowledged":
            errors.append(
                f"adjust_fan dispatch should be acknowledged by the mock adapter, got {status}"
            )

    return {
        "validator_reason_codes": result.validator_reason_codes,
        "plan_kinds": [p.kind for p in plans],
        "plan_targets": [p.target_id for p in plans],
        "dispatch_statuses": [
            (row["dispatch"] or {}).get("status") for row in dispatched
        ],
    }


def _pause_automation_scenario(
    planner: ActionDispatchPlanner,
    dispatcher: ExecutionDispatcher,
    errors: list[str],
) -> dict[str, Any]:
    fixture = {
        "risk_level": "high",
        "confidence": 0.7,
        "retrieval_coverage": "not_used",
        "citations": [],
        "follow_up": [{"type": "trend_review", "zone_id": "gh-01-zone-a"}],
        "required_follow_up": [{"type": "operator_review", "zone_id": "gh-01-zone-a"}],
        "recommended_actions": [
            {"action_type": "pause_automation", "approval_required": False},
        ],
    }
    client = _FixedCompletionClient(
        model_id="pepper-ops-local-fixed",
        raw_text=json.dumps(fixture, ensure_ascii=False),
    )
    orchestrator = _make_orchestrator(client)
    request = _make_request()
    result = orchestrator.evaluate(request)

    plans = planner.plan(
        decision_id=3,
        request_id=request.request_id,
        zone_id=request.zone_id,
        validated_output=result.validated_output,
        zone_state=request.zone_state,
        actor_id="integration-operator",
    )
    if len(plans) != 1 or plans[0].kind != "control_override" or plans[0].action_type != "pause_automation":
        errors.append(
            f"pause_automation should produce exactly one control_override plan, got {[p.kind for p in plans]}"
        )

    dispatched = _dispatch_plans(dispatcher, plans)
    if len(dispatched) != 1 or dispatched[0]["dispatch"] is None:
        errors.append("pause_automation plan should reach the dispatcher")
    else:
        status = dispatched[0]["dispatch"].get("status")
        if status != "state_updated":
            errors.append(
                f"pause_automation dispatch should update control state, got {status}"
            )

    return {
        "plan_kinds": [p.kind for p in plans],
        "dispatch_statuses": [
            (row["dispatch"] or {}).get("status") for row in dispatched
        ],
    }


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="llm-to-execution-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        planner = ActionDispatchPlanner()
        dispatcher = _make_dispatcher(tmp_path)

        report: dict[str, Any] = {
            "stub_baseline": _stub_baseline(planner, errors),
            "adjust_fan": _adjust_fan_scenario(planner, dispatcher, errors),
            "pause_automation": _pause_automation_scenario(planner, dispatcher, errors),
        }

        audit_rows: list[dict[str, Any]] = []
        audit_path = dispatcher.audit_sink.path
        if audit_path.exists():
            for line in audit_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    audit_rows.append(json.loads(line))
        report["audit_row_count"] = len(audit_rows)
        report["audit_statuses"] = [row.get("status") for row in audit_rows]
        if report["audit_row_count"] < 2:
            errors.append(
                f"expected at least two dispatcher audit rows, got {report['audit_row_count']}"
            )

        report["errors"] = errors
        report["status"] = "ok" if not errors else "failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
