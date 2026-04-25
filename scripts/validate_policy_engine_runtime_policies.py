#!/usr/bin/env python3
# Validate policy-engine runtime DSL rules and precheck wiring.

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from policy_engine import evaluate_device_policy_precheck, evaluate_policy_rules, load_enabled_policy_rules  # noqa: E402
from policy_engine.evaluator import RUNTIME_POLICY_STAGES  # noqa: E402


def _expect(case_id: str, report, *, result: str, policy_id: str, errors: list[str]) -> None:
    if report.policy_result != result:
        errors.append(f"{case_id}: expected policy_result={result} got {report.policy_result}")
    if policy_id not in report.policy_ids:
        errors.append(f"{case_id}: missing policy_id={policy_id}; got {report.policy_ids}")


def main() -> int:
    errors: list[str] = []
    runtime_rules = load_enabled_policy_rules(stages=RUNTIME_POLICY_STAGES)
    if len(runtime_rules) < 9:
        errors.append(f"expected at least 9 runtime policy rules, got {len(runtime_rules)}")

    cases = {
        "night_irrigation": (
            {
                "request_id": "runtime-policy-001",
                "action_type": "short_irrigation",
                "parameters": {"duration_seconds": 120},
                "local_hour": 22,
            },
            "approval_required",
            "POL-SCHED-NIGHT-IRRIGATION",
        ),
        "overwet_irrigation": (
            {
                "request_id": "runtime-policy-002",
                "action_type": "short_irrigation",
                "parameters": {"duration_seconds": 120},
                "substrate_moisture_pct": 88,
            },
            "blocked",
            "POL-HARD-OVERWET-IRRIGATION",
        ),
        "sensor_quality_block": (
            {
                "request_id": "runtime-policy-003",
                "action_type": "adjust_fan",
                "sensor_quality": {"overall": "bad", "automation_gate": "blocked"},
            },
            "blocked",
            "POL-HARD-SENSOR-QUALITY",
        ),
        "wind_vent_block": (
            {
                "request_id": "runtime-policy-004",
                "action_type": "adjust_vent",
                "external_wind_m_s": 13,
            },
            "blocked",
            "POL-HARD-WIND-VENT",
        ),
        "robot_worker_block": (
            {
                "request_id": "runtime-policy-005",
                "action_type": "create_robot_task",
                "operator_context": {"operator_present": True},
            },
            "blocked",
            "POL-ROBOT-WORKER-SAFETY",
        ),
        "device_readback_block": (
            {
                "request_id": "runtime-policy-006",
                "action_type": "adjust_shade",
                "device_readback_degraded": True,
            },
            "blocked",
            "POL-HARD-DEVICE-READBACK",
        ),
        "high_risk_approval": (
            {
                "request_id": "runtime-policy-007",
                "action_type": "adjust_co2",
            },
            "approval_required",
            "POL-APPROVAL-HIGH-RISK",
        ),
        "range_irrigation_block": (
            {
                "request_id": "runtime-policy-008",
                "action_type": "short_irrigation",
                "parameters": {"duration_seconds": 1200},
            },
            "blocked",
            "POL-RANGE-IRRIGATION-PULSE",
        ),
        "setpoint_delta_approval": (
            {
                "request_id": "runtime-policy-009",
                "action_type": "adjust_vent",
                "setpoint_delta_pct": 40,
            },
            "approval_required",
            "POL-RANGE-SETPOINT-DELTA",
        ),
    }

    case_reports: dict[str, dict] = {}
    for case_id, (request, expected_result, expected_policy_id) in cases.items():
        report = evaluate_policy_rules(request)
        _expect(case_id, report, result=expected_result, policy_id=expected_policy_id, errors=errors)
        case_reports[case_id] = report.as_dict()

    precheck_result = evaluate_device_policy_precheck(
        {
            "request_id": "runtime-policy-precheck-001",
            "action_type": "short_irrigation",
            "parameters": {"duration_seconds": 120},
            "local_hour": 23,
            "policy_snapshot": {"policy_result": "pass", "policy_ids": []},
        }
    )
    if precheck_result.policy_result != "approval_required":
        errors.append(f"precheck night irrigation should require approval, got {precheck_result.policy_result}")
    if "POL-SCHED-NIGHT-IRRIGATION" not in precheck_result.policy_ids:
        errors.append("precheck did not include POL-SCHED-NIGHT-IRRIGATION")
    if "policy_precheck:POL-SCHED-NIGHT-IRRIGATION" not in precheck_result.reasons:
        errors.append("precheck did not include runtime policy reason")

    print(
        json.dumps(
            {
                "runtime_rule_count": len(runtime_rules),
                "case_reports": case_reports,
                "precheck_result": precheck_result.__dict__,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
