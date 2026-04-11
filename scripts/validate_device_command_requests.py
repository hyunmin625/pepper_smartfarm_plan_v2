#!/usr/bin/env python3
"""Validate execution-gateway device command requests against catalog/profile/action contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/examples/device_command_request_samples.jsonl"
DEFAULT_ACTION_SCHEMA = REPO_ROOT / "schemas/action_schema.json"
DEFAULT_CATALOG = REPO_ROOT / "data/examples/sensor_catalog_seed.json"
DEFAULT_REGISTRY = REPO_ROOT / "data/examples/device_profile_registry_seed.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


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
    parser.add_argument("--action-schema", default=str(DEFAULT_ACTION_SCHEMA))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    action_schema = load_json(Path(args.action_schema))
    catalog = load_json(Path(args.catalog))
    registry = load_json(Path(args.registry))

    errors: list[str] = []
    seen_request_ids: set[str] = set()

    valid_action_types = set(
        action_schema.get("$defs", {})
        .get("recommended_action", {})
        .get("properties", {})
        .get("action_type", {})
        .get("enum", [])
    )
    device_by_id = {
        item["device_id"]: item
        for item in catalog.get("devices", [])
        if isinstance(item, dict) and isinstance(item.get("device_id"), str)
    }
    profile_by_id = {
        item["profile_id"]: item
        for item in registry.get("device_profiles", [])
        if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
    }

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            errors.append(f"{prefix}: request_id must be a non-empty string")
            continue
        if request_id in seen_request_ids:
            errors.append(f"{prefix}: duplicate request_id {request_id}")
        seen_request_ids.add(request_id)

        if row.get("schema_version") != "device_command_request.v1":
            errors.append(f"{prefix}: schema_version must be device_command_request.v1")

        action_type = row.get("action_type")
        if action_type not in valid_action_types:
            errors.append(f"{prefix}: action_type {action_type} is not valid")

        device_id = row.get("device_id")
        device = device_by_id.get(device_id)
        if device is None:
            errors.append(f"{prefix}: unknown device_id {device_id}")
            continue

        profile_id = device.get("model_profile")
        profile = profile_by_id.get(profile_id)
        if profile is None:
            errors.append(f"{prefix}: device profile {profile_id} not found in registry")
            continue

        if action_type not in set(profile.get("supported_action_types", [])):
            errors.append(f"{prefix}: action_type {action_type} is not supported by profile {profile_id}")

        parameter_bounds = {
            item.get("parameter"): item
            for item in device.get("setpoint_bounds", [])
            if isinstance(item, dict) and isinstance(item.get("parameter"), str)
        }
        parameters = row.get("parameters")
        if not isinstance(parameters, dict):
            errors.append(f"{prefix}: parameters must be an object")
        else:
            for parameter_name, parameter_value in parameters.items():
                bound = parameter_bounds.get(parameter_name)
                if bound is None:
                    errors.append(f"{prefix}: parameter {parameter_name} is not defined in catalog setpoint_bounds")
                    continue
                value_type = bound.get("value_type")
                if value_type in {"binary", "enum"}:
                    allowed_values = set(bound.get("allowed_values", []))
                    if parameter_value not in allowed_values:
                        errors.append(
                            f"{prefix}: parameter {parameter_name} value {parameter_value} is outside allowed_values {sorted(allowed_values)}"
                        )
                elif value_type in {"integer", "number"}:
                    if not isinstance(parameter_value, (int, float)):
                        errors.append(f"{prefix}: parameter {parameter_name} must be numeric")
                        continue
                    minimum = bound.get("min")
                    maximum = bound.get("max")
                    if isinstance(minimum, (int, float)) and parameter_value < minimum:
                        errors.append(f"{prefix}: parameter {parameter_name} value {parameter_value} is below min {minimum}")
                    if isinstance(maximum, (int, float)) and parameter_value > maximum:
                        errors.append(f"{prefix}: parameter {parameter_name} value {parameter_value} exceeds max {maximum}")

        approval_required = row.get("approval_required")
        approval_context = row.get("approval_context", {})
        approval_status = approval_context.get("approval_status")
        if approval_required and approval_status not in {"approved", "pending"}:
            errors.append(f"{prefix}: approval_required request must be approved or pending")

        requested_by = row.get("requested_by")
        if not isinstance(requested_by, dict):
            errors.append(f"{prefix}: requested_by must be an object")
        elif requested_by.get("actor_type") not in {"llm_orchestrator", "operator", "scheduler", "policy_engine"}:
            errors.append(f"{prefix}: requested_by.actor_type is invalid")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
