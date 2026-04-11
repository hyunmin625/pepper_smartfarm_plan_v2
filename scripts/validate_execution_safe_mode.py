#!/usr/bin/env python3
"""Validate safe mode entry on repeated adapter runtime faults."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from execution_gateway.contracts import DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402
from plc_adapter.transports import InMemoryPlcTagTransport  # noqa: E402


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
    heater_request = {
        **device_rows[2],
        "approval_required": False,
        "approval_context": {
            "approval_status": "approved",
            "approver_id": "operator-01",
            "approved_at": "2026-04-11T21:14:50+09:00",
        },
        "policy_snapshot": {
            "policy_result": "pass",
            "policy_ids": ["policy-heating-approval"],
        },
    }
    blocked_fan_request = {
        **device_rows[0],
        "request_id": "cmd-zone-b-fan-after-safe-mode",
        "zone_id": "gh-01-zone-b",
        "device_id": "gh-01-zone-b--circulation-fan--01",
    }

    with tempfile.TemporaryDirectory(prefix="execution-safe-mode-") as tmp_dir:
        audit_path = Path(tmp_dir) / "dispatch_audit.jsonl"
        os.environ["EXECUTION_GATEWAY_AUDIT_LOG_PATH"] = str(audit_path)
        transport = InMemoryPlcTagTransport(
            write_failures_before_success={"placeholder://gh-01-main-plc": 4}
        )
        dispatcher = ExecutionDispatcher.default(
            adapter_kind="plc_tag_modbus_tcp",
            transport=transport,
        )

        first_timeout = dispatcher.dispatch_device_command(
            DeviceCommandRequest.from_dict({**heater_request, "request_id": "cmd-heater-timeout-001"})
        )
        dispatcher.duplicates.seen_keys.clear()
        second_timeout = dispatcher.dispatch_device_command(
            DeviceCommandRequest.from_dict({**heater_request, "request_id": "cmd-heater-timeout-002"})
        )
        blocked_fan = dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(blocked_fan_request))

        zone_state = dispatcher.control_state.get("zone", "gh-01-zone-b").as_dict()
        site_state = dispatcher.control_state.get("site", "gh-01").as_dict()

        errors: list[str] = []
        if first_timeout.status != "dispatch_fault" or "adapter_timeout" not in first_timeout.reasons:
            errors.append("first timeout dispatch was not classified as adapter_timeout")
        if second_timeout.status != "dispatch_fault" or "adapter_timeout" not in second_timeout.reasons:
            errors.append("second timeout dispatch was not classified as adapter_timeout")
        if not zone_state["safe_mode_active"]:
            errors.append("zone safe_mode_active was not latched after repeated timeouts")
        if not site_state["safe_mode_active"]:
            errors.append("site safe_mode_active was not latched after repeated timeouts")
        if blocked_fan.status != "rejected" or "safe_mode_active" not in blocked_fan.reasons:
            errors.append("blocked fan request was not rejected by safe_mode_active")

        summary = {
            "first_timeout_status": first_timeout.status,
            "second_timeout_status": second_timeout.status,
            "blocked_fan_status": blocked_fan.status,
            "zone_state": zone_state,
            "site_state": site_state,
            "errors": errors,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
