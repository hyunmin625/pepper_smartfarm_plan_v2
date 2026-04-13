#!/usr/bin/env python3
"""Validate system event samples for the canonical event contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/examples/system_event_samples.jsonl"

EVENT_TYPES = {
    "sensor.snapshot.updated",
    "zone.state.updated",
    "action.requested",
    "action.blocked",
    "action.executed",
    "robot.task.created",
    "robot.task.failed",
    "alert.created",
    "approval.requested",
}
SOURCE_SERVICES = {
    "sensor_ingestor",
    "state_estimator",
    "llm_orchestrator",
    "policy_engine",
    "ops_api",
    "execution_gateway",
    "plc_adapter",
    "robot_task_manager",
}
SEVERITIES = {"info", "warning", "error", "critical"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(item)
    return rows


def require_keys(payload: dict, keys: tuple[str, ...], prefix: str, errors: list[str]) -> None:
    for key in keys:
        if key not in payload:
            errors.append(f"{prefix}: missing payload.{key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    errors: list[str] = []
    seen_event_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"
        event_id = row.get("event_id")

        if row.get("schema_version") != "system_event.v1":
            errors.append(f"{prefix}: schema_version must be system_event.v1")

        if not isinstance(event_id, str) or not event_id:
            errors.append(f"{prefix}: event_id must be a non-empty string")
            continue
        if event_id in seen_event_ids:
            errors.append(f"{prefix}: duplicate event_id {event_id}")
        seen_event_ids.add(event_id)

        event_type = row.get("event_type")
        if event_type not in EVENT_TYPES:
            errors.append(f"{prefix}: event_type is invalid")
            continue

        if row.get("source_service") not in SOURCE_SERVICES:
            errors.append(f"{prefix}: source_service is invalid")
        if row.get("severity") not in SEVERITIES:
            errors.append(f"{prefix}: severity is invalid")

        payload = row.get("payload")
        if not isinstance(payload, dict):
            errors.append(f"{prefix}: payload must be an object")
            continue

        if event_type == "sensor.snapshot.updated":
            require_keys(payload, ("sensor_id", "sensor_type", "measurement_fields", "observed_at", "quality_flag"), prefix, errors)
        elif event_type == "zone.state.updated":
            require_keys(payload, ("state_ref",), prefix, errors)
            state_ref = payload.get("state_ref")
            if not isinstance(state_ref, dict) or state_ref.get("schema_version") != "state.v1":
                errors.append(f"{prefix}: payload.state_ref.schema_version must be state.v1")
        elif event_type == "action.requested":
            require_keys(payload, ("decision_id", "policy_result", "command_request"), prefix, errors)
            command_request = payload.get("command_request")
            if not isinstance(command_request, dict) or command_request.get("schema_version") != "device_command_request.v1":
                errors.append(f"{prefix}: payload.command_request.schema_version must be device_command_request.v1")
        elif event_type == "action.blocked":
            require_keys(payload, ("decision_id", "action_id", "policy_result", "reason_codes"), prefix, errors)
            if payload.get("policy_result") not in {"blocked", "approval_required"}:
                errors.append(f"{prefix}: payload.policy_result is invalid for action.blocked")
        elif event_type == "action.executed":
            require_keys(payload, ("decision_id", "request_id", "device_id", "execution_status"), prefix, errors)
        elif event_type == "robot.task.created":
            require_keys(payload, ("decision_id", "candidate", "robot_task"), prefix, errors)
        elif event_type == "robot.task.failed":
            require_keys(payload, ("task_id", "candidate_id", "failure_code", "reason"), prefix, errors)
        elif event_type == "alert.created":
            require_keys(payload, ("alert_id", "alert_type", "status", "summary"), prefix, errors)
        elif event_type == "approval.requested":
            require_keys(payload, ("decision_id", "approval_id", "approval_scope", "approval_reason"), prefix, errors)

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
