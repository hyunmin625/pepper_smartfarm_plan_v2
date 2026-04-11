#!/usr/bin/env python3
"""Small demo for execution-gateway dispatch flow."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest
from execution_gateway.dispatch import ExecutionDispatcher


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    device_rows = load_jsonl(REPO_ROOT / "data/examples/device_command_request_samples.jsonl")
    override_rows = load_jsonl(REPO_ROOT / "data/examples/control_override_request_samples.jsonl")

    with tempfile.TemporaryDirectory(prefix="execution-gateway-demo-") as tmp_dir:
        os.environ["EXECUTION_GATEWAY_AUDIT_LOG_PATH"] = str(Path(tmp_dir) / "dispatch_audit.jsonl")
        dispatcher = ExecutionDispatcher.default(adapter_kind="mock")

        estop_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(override_rows[0]))
        blocked_fan_result = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(device_rows[0]))
        release_manual_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(override_rows[2]))
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
        auto_reentry_result = dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(override_rows[-1]))

        result = {
            "estop_latch": estop_result.as_dict(),
            "fan_blocked_by_estop": blocked_fan_result.as_dict(),
            "manual_override_release": release_manual_result.as_dict(),
            "estop_reset": reset_estop_result.as_dict(),
            "source_water_dispatch": source_water_result.as_dict(),
            "auto_mode_reentry": auto_reentry_result.as_dict(),
            "control_state_snapshot": {
                key: value.as_dict()
                for key, value in dispatcher.control_state.states.items()
            },
            "audit_log_path": os.environ["EXECUTION_GATEWAY_AUDIT_LOG_PATH"],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
