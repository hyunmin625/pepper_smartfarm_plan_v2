#!/usr/bin/env python3
"""Validate zone state payload samples for the canonical state schema layer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/examples/zone_state_payload_samples.jsonl"

GROWTH_STAGES = {
    "pre_planting",
    "nursery",
    "transplanting",
    "establishment",
    "vegetative_growth",
    "flowering",
    "fruit_set",
    "fruit_expansion",
    "coloring",
    "harvest",
    "drying",
    "storage",
    "season_end",
    "unknown",
}
DEVICE_TYPES = {"fan", "shade", "vent", "irrigation_valve", "fertigation_unit", "heater", "co2_unit", "dehumidifier", "robot", "other"}
DEVICE_MODES = {"manual", "auto", "approval", "disabled", "unknown"}
EVENT_TYPES = {"irrigation", "fertigation", "shade_change", "vent_change", "manual_override", "alarm", "spray", "worker_entry", "robot_event", "note"}
CONSTRAINT_SEVERITIES = {"info", "warning", "approval_required", "hard_block"}


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    errors: list[str] = []

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"

        if row.get("schema_version") != "state.v1":
            errors.append(f"{prefix}: schema_version must be state.v1")

        if "weather_context" in row:
            errors.append(f"{prefix}: weather_context must not exist; use current_state.outside_weather")

        crop = row.get("crop")
        if not isinstance(crop, dict) or crop.get("crop_type") not in {"red_pepper", "dried_red_pepper"}:
            errors.append(f"{prefix}: crop.crop_type is invalid")

        if row.get("growth_stage") not in GROWTH_STAGES:
            errors.append(f"{prefix}: growth_stage is invalid")

        current_state = row.get("current_state")
        if not isinstance(current_state, dict):
            errors.append(f"{prefix}: current_state must be an object")
        else:
            for key in ("environment", "rootzone", "outside_weather"):
                value = current_state.get(key)
                if not isinstance(value, dict) or not value:
                    errors.append(f"{prefix}: current_state.{key} must be a non-empty object")

        derived_features = row.get("derived_features")
        if not isinstance(derived_features, dict) or derived_features.get("schema_version") != "features.v1":
            errors.append(f"{prefix}: derived_features.schema_version must be features.v1")

        sensor_quality = row.get("sensor_quality")
        if not isinstance(sensor_quality, dict) or sensor_quality.get("schema_version") != "sensor_quality.v1":
            errors.append(f"{prefix}: sensor_quality.schema_version must be sensor_quality.v1")

        device_status = row.get("device_status")
        if not isinstance(device_status, list) or not device_status:
            errors.append(f"{prefix}: device_status must be a non-empty array")
        else:
            for device_index, device in enumerate(device_status, start=1):
                if not isinstance(device, dict):
                    errors.append(f"{prefix}: device_status[{device_index}] must be an object")
                    continue
                if device.get("device_type") not in DEVICE_TYPES:
                    errors.append(f"{prefix}: device_status[{device_index}].device_type is invalid")
                if device.get("mode") not in DEVICE_MODES:
                    errors.append(f"{prefix}: device_status[{device_index}].mode is invalid")

        recent_events = row.get("recent_events")
        if not isinstance(recent_events, list):
            errors.append(f"{prefix}: recent_events must be an array")
        else:
            for event_index, event in enumerate(recent_events, start=1):
                if not isinstance(event, dict):
                    errors.append(f"{prefix}: recent_events[{event_index}] must be an object")
                    continue
                if event.get("event_type") not in EVENT_TYPES:
                    errors.append(f"{prefix}: recent_events[{event_index}].event_type is invalid")

        constraints = row.get("active_constraints")
        if not isinstance(constraints, list):
            errors.append(f"{prefix}: active_constraints must be an array")
        else:
            for constraint_index, constraint in enumerate(constraints, start=1):
                if not isinstance(constraint, dict):
                    errors.append(f"{prefix}: active_constraints[{constraint_index}] must be an object")
                    continue
                if constraint.get("severity") not in CONSTRAINT_SEVERITIES:
                    errors.append(f"{prefix}: active_constraints[{constraint_index}].severity is invalid")

        retrieved_context = row.get("retrieved_context")
        if not isinstance(retrieved_context, list) or not retrieved_context:
            errors.append(f"{prefix}: retrieved_context must be a non-empty array")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
