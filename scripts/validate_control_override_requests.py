#!/usr/bin/env python3
"""Validate control override requests against safety transition rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/examples/control_override_request_samples.jsonl"

OVERRIDE_TYPES = {
    "emergency_stop_latch",
    "emergency_stop_reset_request",
    "manual_override_start",
    "manual_override_release",
    "safe_mode_entry",
    "auto_mode_reentry_request",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    errors: list[str] = []
    seen_request_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            errors.append(f"{prefix}: request_id must be a non-empty string")
            continue
        if request_id in seen_request_ids:
            errors.append(f"{prefix}: duplicate request_id {request_id}")
        seen_request_ids.add(request_id)

        if row.get("schema_version") != "control_override_request.v1":
            errors.append(f"{prefix}: schema_version must be control_override_request.v1")

        override_type = row.get("override_type")
        if override_type not in OVERRIDE_TYPES:
            errors.append(f"{prefix}: invalid override_type {override_type}")
            continue

        requested_by = row.get("requested_by", {})
        actor_type = requested_by.get("actor_type")
        approval_required = bool(row.get("approval_required"))
        approval_context = row.get("approval_context", {})
        approval_status = approval_context.get("approval_status")
        operator_context = row.get("operator_context", {})
        preconditions = row.get("preconditions", {})

        if override_type in {"manual_override_start", "manual_override_release"} and actor_type != "operator":
            errors.append(f"{prefix}: {override_type} must be requested by operator")

        if override_type == "emergency_stop_latch" and actor_type not in {"operator", "system_monitor", "policy_engine"}:
            errors.append(f"{prefix}: emergency_stop_latch actor_type {actor_type} is not allowed")

        if override_type in {"emergency_stop_reset_request", "manual_override_release", "auto_mode_reentry_request"}:
            if not approval_required:
                errors.append(f"{prefix}: {override_type} must set approval_required=true")
            if approval_status != "approved":
                errors.append(f"{prefix}: {override_type} requires approval_status=approved")

        if override_type == "manual_override_start" and operator_context.get("operator_present") is not True:
            errors.append(f"{prefix}: manual_override_start requires operator_present=true")

        if override_type == "manual_override_release":
            if preconditions.get("manual_override_cleared") is not True:
                errors.append(f"{prefix}: manual_override_release requires manual_override_cleared=true")

        if override_type == "emergency_stop_reset_request":
            if preconditions.get("estop_cleared") is not True:
                errors.append(f"{prefix}: emergency_stop_reset_request requires estop_cleared=true")

        if override_type == "auto_mode_reentry_request":
            for key in ("state_sync_completed", "manual_override_cleared", "estop_cleared"):
                if preconditions.get(key) is not True:
                    errors.append(f"{prefix}: auto_mode_reentry_request requires {key}=true")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
