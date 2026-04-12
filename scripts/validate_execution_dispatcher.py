#!/usr/bin/env python3
"""Validate execution-gateway dispatcher and control-state transitions."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    device_rows = load_jsonl(REPO_ROOT / "data/examples/device_command_request_samples.jsonl")
    override_rows = load_jsonl(REPO_ROOT / "data/examples/control_override_request_samples.jsonl")

    with tempfile.TemporaryDirectory(prefix="execution-dispatcher-") as tmp_dir:
        audit_path = Path(tmp_dir) / "dispatch_audit.jsonl"
        os.environ["EXECUTION_GATEWAY_AUDIT_LOG_PATH"] = str(audit_path)
        dispatcher = ExecutionDispatcher.default(adapter_kind="mock")

        estop_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(override_rows[0]))
        fan_result = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(device_rows[0]))
        reset_estop_request = {
            **override_rows[2],
            "request_id": "override-reset-001",
            "scope_type": "zone",
            "scope_id": "gh-01-zone-a",
            "override_type": "emergency_stop_reset_request",
            "preconditions": {},
        }
        reset_estop_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(reset_estop_request))
        source_water_result = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(device_rows[1]))
        worker_present_request = {
            **device_rows[0],
            "request_id": "cmd-worker-interlock-dispatch",
            "operator_context": {
                "manual_override": False,
                "operator_present": True,
            },
        }
        worker_present_result = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(worker_present_request))
        auto_reentry_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(override_rows[-1]))

        audit_rows = load_jsonl(audit_path)
        errors: list[str] = []
        if estop_result.status != "state_updated":
            errors.append("estop_result did not update state")
        if fan_result.status != "rejected" or "estop_active" not in fan_result.reasons:
            errors.append("fan_result was not blocked by estop state")
        if reset_estop_result.status != "state_updated":
            errors.append("estop reset did not update state")
        if source_water_result.status != "acknowledged":
            errors.append("source water dispatch did not reach adapter")
        if worker_present_result.status != "rejected" or "hard_guard_worker_present" not in worker_present_result.reasons:
            errors.append("worker_present_result was not blocked by hard safety guard")
        if auto_reentry_result.status != "state_updated":
            errors.append("auto mode reentry did not update state")
        if len(audit_rows) != 6:
            errors.append(f"expected 6 audit rows, found {len(audit_rows)}")

        summary = {
            "checked_cases": 6,
            "audit_rows": len(audit_rows),
            "zone_a_state": dispatcher.control_state.get("zone", "gh-01-zone-a").as_dict(),
            "site_state": dispatcher.control_state.get("site", "gh-01").as_dict(),
            "errors": errors,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
