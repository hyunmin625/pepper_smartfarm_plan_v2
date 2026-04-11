#!/usr/bin/env python3
"""Validate synthetic sensor scenarios JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_FILE = Path("data/examples/synthetic_sensor_scenarios.jsonl")
REQUIRED_FIELDS = {
    "scenario_id",
    "category",
    "zone_id",
    "growth_stage",
    "summary",
    "current_state",
    "derived_features",
    "sensor_quality",
    "expected_focus",
}


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append((line_number, row))
    return rows


def validate_row(path: Path, line_number: int, row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}:{line_number}"
    missing = sorted(REQUIRED_FIELDS - set(row))
    if missing:
        return [f"{prefix}: missing fields {missing}"]

    for field_name in ("scenario_id", "category", "zone_id", "growth_stage", "summary"):
        value = row.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}: {field_name} must be a non-empty string")

    for field_name in ("current_state", "derived_features", "sensor_quality"):
        value = row.get(field_name)
        if not isinstance(value, dict) or not value:
            errors.append(f"{prefix}: {field_name} must be a non-empty object")

    expected_focus = row.get("expected_focus")
    if not isinstance(expected_focus, list) or not expected_focus:
        errors.append(f"{prefix}: expected_focus must be a non-empty array")
    else:
        for index, item in enumerate(expected_focus, start=1):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"{prefix}: expected_focus[{index}] must be a non-empty string")

    sensor_quality = row.get("sensor_quality")
    if isinstance(sensor_quality, dict):
        overall = sensor_quality.get("overall")
        if not isinstance(overall, str) or not overall.strip():
            errors.append(f"{prefix}: sensor_quality.overall must be a non-empty string")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(DEFAULT_FILE))
    args = parser.parse_args()

    path = Path(args.file)
    rows = load_jsonl(path)
    all_errors: list[str] = []
    scenario_counter: Counter[str] = Counter()

    for line_number, row in rows:
        scenario_id = row.get("scenario_id")
        if isinstance(scenario_id, str):
            scenario_counter[scenario_id] += 1
        all_errors.extend(validate_row(path, line_number, row))

    duplicates = sorted(identifier for identifier, count in scenario_counter.items() if count > 1)
    for duplicate in duplicates:
        all_errors.append(f"synthetic_scenarios: duplicate scenario_id {duplicate}")

    for error in all_errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"file: {path}")
    print(f"rows: {len(rows)}")
    print(f"duplicate_scenario_ids: {len(duplicates)}")
    print(f"errors: {len(all_errors)}")
    raise SystemExit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
