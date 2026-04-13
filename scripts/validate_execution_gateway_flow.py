#!/usr/bin/env python3
"""Validate execution-gateway normalization and guard flow with sample inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest
from execution_gateway.guards import (
    CooldownManager,
    DuplicateDetector,
    evaluate_control_override,
    evaluate_device_command,
)
from plc_adapter.device_catalog import load_device_catalog
from plc_adapter.device_profiles import load_profile_registry


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    catalog = load_device_catalog()
    registry = load_profile_registry()
    device_rows = load_jsonl(REPO_ROOT / "data/examples/device_command_request_samples.jsonl")
    override_rows = load_jsonl(REPO_ROOT / "data/examples/control_override_request_samples.jsonl")

    errors: list[str] = []

    heater_pending = DeviceCommandRequest.from_dict(device_rows[2])
    _, heater_decision = evaluate_device_command(
        heater_pending,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if heater_decision.allow_dispatch or "approval_pending" not in heater_decision.reasons:
        errors.append("heater_pending should be blocked by approval_pending")

    fan_request = DeviceCommandRequest.from_dict(device_rows[0])
    _, fan_decision = evaluate_device_command(
        fan_request,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(active_keys={"device:gh-01-zone-a--circulation-fan--01:adjust_fan"}),
    )
    if fan_decision.allow_dispatch or "cooldown_active" not in fan_decision.reasons:
        errors.append("fan_request should be blocked by cooldown_active")

    worker_present_request = DeviceCommandRequest.from_dict(
        {
            **device_rows[0],
            "request_id": "cmd-worker-interlock",
            "operator_context": {
                "manual_override": False,
                "operator_present": True,
            },
        }
    )
    _, worker_present_decision = evaluate_device_command(
        worker_present_request,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if worker_present_decision.allow_dispatch or "hard_guard_worker_present" not in worker_present_decision.reasons:
        errors.append("worker_present_request should be blocked by hard_guard_worker_present")

    blocked_sensor_request = DeviceCommandRequest.from_dict(
        {
            **device_rows[0],
            "request_id": "cmd-sensor-quality-blocked",
            "sensor_quality": {
                "overall": "bad",
                "automation_gate": "blocked",
            },
        }
    )
    _, blocked_sensor_decision = evaluate_device_command(
        blocked_sensor_request,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if blocked_sensor_decision.allow_dispatch or "hard_guard_sensor_quality_blocked" not in blocked_sensor_decision.reasons:
        errors.append("blocked_sensor_request should be blocked by hard_guard_sensor_quality_blocked")

    irrigation_path_request = DeviceCommandRequest.from_dict(
        {
            **device_rows[0],
            "request_id": "cmd-irrigation-path-degraded",
            "action_type": "short_irrigation",
            "device_id": "gh-01-zone-b--irrigation-valve--01",
            "parameters": {"run_state": "open", "duration_seconds": 120},
            "irrigation_path_degraded": True,
        }
    )
    _, irrigation_path_decision = evaluate_device_command(
        irrigation_path_request,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if irrigation_path_decision.allow_dispatch or "policy_precheck:HSV-04" not in irrigation_path_decision.reasons:
        errors.append("irrigation_path_request should be blocked by HSV-04 precheck")

    fertigation_conflict_request = DeviceCommandRequest.from_dict(
        {
            **device_rows[0],
            "request_id": "cmd-rootzone-conflict-fertigation",
            "zone_id": "gh-01-nutrient-room",
            "device_id": "gh-01-nutrient-room--nutrient-mixer--01",
            "action_type": "adjust_fertigation",
            "parameters": {"recipe_id": "default-recipe", "mix_volume_l": 50},
            "approval_required": False,
            "approval_context": {
                "approval_status": "not_required",
                "approver_id": None,
                "approved_at": None,
            },
            "policy_snapshot": {
                "policy_result": "pass",
                "policy_ids": [],
            },
            "rootzone_sensor_conflict": True,
            "rootzone_control_interpretable": False,
        }
    )
    _, fertigation_conflict_decision = evaluate_device_command(
        fertigation_conflict_request,
        catalog=catalog,
        registry=registry,
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if (
        fertigation_conflict_decision.allow_dispatch
        or fertigation_conflict_decision.policy_result != "approval_required"
        or "policy_precheck:HSV-09" not in fertigation_conflict_decision.reasons
        or "approval_pending" not in fertigation_conflict_decision.reasons
    ):
        errors.append("fertigation_conflict_request should escalate to approval_required via HSV-09")

    duplicate_detector = DuplicateDetector()
    _, first_duplicate_decision = evaluate_control_override(
        ControlOverrideRequest.from_dict(override_rows[0]),
        duplicates=duplicate_detector,
        cooldowns=CooldownManager(),
    )
    _, second_duplicate_decision = evaluate_control_override(
        ControlOverrideRequest.from_dict(override_rows[0]),
        duplicates=duplicate_detector,
        cooldowns=CooldownManager(),
    )
    if not first_duplicate_decision.allow_dispatch:
        errors.append("first estop request should be dispatchable")
    if second_duplicate_decision.allow_dispatch or "duplicate_request" not in second_duplicate_decision.reasons:
        errors.append("second estop request should be blocked as duplicate")

    _, reentry_decision = evaluate_control_override(
        ControlOverrideRequest.from_dict(override_rows[-1]),
        duplicates=DuplicateDetector(),
        cooldowns=CooldownManager(),
    )
    if not reentry_decision.allow_dispatch:
        errors.append("approved auto_mode_reentry_request should be dispatchable")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print("checked_cases: 8")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
