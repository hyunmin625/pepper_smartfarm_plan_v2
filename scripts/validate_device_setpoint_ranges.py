#!/usr/bin/env python3
"""Validate device setpoint bounds in the sensor catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "data/examples/sensor_catalog_seed.json"

EXPECTED_PARAMETERS = {
    "circulation_fan": {"run_state", "speed_pct"},
    "vent_window": {"position_pct"},
    "shade_curtain": {"position_pct"},
    "irrigation_valve": {"run_state", "duration_seconds"},
    "heater": {"run_state", "stage"},
    "co2_doser": {"run_state", "dose_pct"},
    "nutrient_mixer": {"recipe_id", "mix_volume_l"},
    "source_water_valve": {"run_state"},
    "dehumidifier": {"run_state", "stage"},
    "dry_fan": {"run_state", "speed_pct"},
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    args = parser.parse_args()

    catalog = load_json(Path(args.catalog))
    devices = catalog.get("devices", [])
    errors: list[str] = []

    for index, device in enumerate(devices, start=1):
        if not isinstance(device, dict):
            errors.append(f"devices[{index}] must be an object")
            continue
        device_id = device.get("device_id", f"devices[{index}]")
        device_type = device.get("device_type")
        bounds = device.get("setpoint_bounds")
        if not isinstance(bounds, list) or not bounds:
            errors.append(f"{device_id}: setpoint_bounds must be a non-empty array")
            continue

        seen_parameters: set[str] = set()
        for bound_index, bound in enumerate(bounds, start=1):
            prefix = f"{device_id}.setpoint_bounds[{bound_index}]"
            if not isinstance(bound, dict):
                errors.append(f"{prefix}: must be an object")
                continue
            parameter = bound.get("parameter")
            value_type = bound.get("value_type")
            if not isinstance(parameter, str) or not parameter:
                errors.append(f"{prefix}: parameter must be a non-empty string")
                continue
            if parameter in seen_parameters:
                errors.append(f"{prefix}: duplicate parameter {parameter}")
            seen_parameters.add(parameter)
            if value_type not in {"binary", "integer", "number", "enum"}:
                errors.append(f"{prefix}: invalid value_type {value_type}")
                continue

            if value_type in {"binary", "enum"}:
                allowed_values = bound.get("allowed_values")
                if not isinstance(allowed_values, list) or not allowed_values:
                    errors.append(f"{prefix}: allowed_values is required for {value_type}")
            else:
                minimum = bound.get("min")
                maximum = bound.get("max")
                if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
                    errors.append(f"{prefix}: min/max are required for numeric value_type")
                elif minimum > maximum:
                    errors.append(f"{prefix}: min {minimum} is greater than max {maximum}")

                recommended_min = bound.get("recommended_min")
                recommended_max = bound.get("recommended_max")
                if isinstance(recommended_min, (int, float)) and isinstance(minimum, (int, float)) and recommended_min < minimum:
                    errors.append(f"{prefix}: recommended_min {recommended_min} is below min {minimum}")
                if isinstance(recommended_max, (int, float)) and isinstance(maximum, (int, float)) and recommended_max > maximum:
                    errors.append(f"{prefix}: recommended_max {recommended_max} exceeds max {maximum}")
                if isinstance(recommended_min, (int, float)) and isinstance(recommended_max, (int, float)) and recommended_min > recommended_max:
                    errors.append(f"{prefix}: recommended_min {recommended_min} is greater than recommended_max {recommended_max}")

        expected = EXPECTED_PARAMETERS.get(device_type)
        if expected is not None and seen_parameters != expected:
            errors.append(f"{device_id}: expected parameters {sorted(expected)}, got {sorted(seen_parameters)}")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"catalog_path: {args.catalog}")
    print(f"devices: {len(devices)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
