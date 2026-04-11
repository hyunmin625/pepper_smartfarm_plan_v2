#!/usr/bin/env python3
"""Validate farm_case candidate JSONL samples."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_FILES = [Path("data/examples/farm_case_candidate_samples.jsonl")]
REQUIRED_FIELDS = {
    "case_id",
    "farm_id",
    "zone_id",
    "source_type",
    "crop_type",
    "growth_stage",
    "sensor_tags",
    "risk_tags",
    "action_taken",
    "outcome",
    "review_status",
    "chunk_summary",
}
ALLOWED_CROP_TYPES = {"red_pepper", "dried_red_pepper"}
ALLOWED_SENSOR_QUALITY = {"good", "partial", "bad"}
ALLOWED_OUTCOMES = {"success", "partial_success", "failure", "unknown"}
ALLOWED_REVIEW_STATUS = {"draft", "reviewed", "approved", "rejected"}
ALLOWED_TRUST_LEVELS = {"low", "medium", "high"}
ARRAY_FIELDS = {
    "growth_stage",
    "sensor_tags",
    "risk_tags",
    "action_taken",
    "cultivation_type",
    "operation_tags",
    "causality_tags",
    "visual_tags",
    "sensor_window_refs",
    "operation_log_refs",
    "ai_decision_refs",
}
NON_EMPTY_ARRAY_FIELDS = {"growth_stage", "sensor_tags", "risk_tags", "action_taken"}


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


def parse_datetime(value: str, prefix: str, field_name: str, errors: list[str]) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{prefix}: {field_name} must be a valid ISO 8601 datetime")
        return None


def validate_string_array(value: Any, prefix: str, field_name: str, *, allow_empty: bool) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if not isinstance(value, list):
        return [f"{prefix}: {field_name} must be an array"]
    if not allow_empty and not value:
        errors.append(f"{prefix}: {field_name} must be a non-empty array")
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{prefix}: {field_name}[{index}] must be a non-empty string")
    return errors


def validate_row(path: Path, line_number: int, row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}:{line_number}"

    missing = sorted(REQUIRED_FIELDS - set(row))
    if missing:
        errors.append(f"{prefix}: missing fields {missing}")
        return errors

    if row.get("source_type") != "farm_case":
        errors.append(f"{prefix}: source_type must be farm_case")
    if row.get("crop_type") not in ALLOWED_CROP_TYPES:
        errors.append(f"{prefix}: crop_type must be one of {sorted(ALLOWED_CROP_TYPES)}")
    if "sensor_quality" in row and row["sensor_quality"] not in ALLOWED_SENSOR_QUALITY:
        errors.append(f"{prefix}: sensor_quality must be one of {sorted(ALLOWED_SENSOR_QUALITY)}")
    if row.get("outcome") not in ALLOWED_OUTCOMES:
        errors.append(f"{prefix}: outcome must be one of {sorted(ALLOWED_OUTCOMES)}")
    if row.get("review_status") not in ALLOWED_REVIEW_STATUS:
        errors.append(f"{prefix}: review_status must be one of {sorted(ALLOWED_REVIEW_STATUS)}")
    if "trust_level" in row and row["trust_level"] not in ALLOWED_TRUST_LEVELS:
        errors.append(f"{prefix}: trust_level must be one of {sorted(ALLOWED_TRUST_LEVELS)}")
    if "confidence" in row:
        confidence = row["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            errors.append(f"{prefix}: confidence must be a number between 0 and 1")

    for field_name in ("case_id", "farm_id", "zone_id", "chunk_summary"):
        value = row.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}: {field_name} must be a non-empty string")
    if isinstance(row.get("chunk_summary"), str) and len(row["chunk_summary"].strip()) < 20:
        errors.append(f"{prefix}: chunk_summary must be at least 20 characters")

    for field_name in ARRAY_FIELDS:
        errors.extend(
            validate_string_array(
                row.get(field_name),
                prefix,
                field_name,
                allow_empty=field_name not in NON_EMPTY_ARRAY_FIELDS,
            )
        )

    start_at = None
    end_at = None
    if "event_start_at" in row:
        if not isinstance(row["event_start_at"], str):
            errors.append(f"{prefix}: event_start_at must be a string")
        else:
            start_at = parse_datetime(row["event_start_at"], prefix, "event_start_at", errors)
    if "event_end_at" in row:
        if not isinstance(row["event_end_at"], str):
            errors.append(f"{prefix}: event_end_at must be a string")
        else:
            end_at = parse_datetime(row["event_end_at"], prefix, "event_end_at", errors)
    if start_at and end_at and end_at < start_at:
        errors.append(f"{prefix}: event_end_at must be later than or equal to event_start_at")

    if row.get("review_status") == "approved":
        if not isinstance(row.get("reviewer"), str) or not row["reviewer"].strip():
            errors.append(f"{prefix}: approved row must include reviewer")
        approved_at = row.get("approved_at")
        if not isinstance(approved_at, str) or not approved_at.strip():
            errors.append(f"{prefix}: approved row must include approved_at")
        else:
            parse_datetime(approved_at, prefix, "approved_at", errors)

    if row.get("sensor_quality") == "bad" and row.get("review_status") == "approved":
        errors.append(f"{prefix}: sensor_quality=bad row cannot be approved")
    if row.get("outcome") == "unknown" and row.get("review_status") == "approved":
        errors.append(f"{prefix}: outcome=unknown row cannot be approved")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="*", default=[str(path) for path in DEFAULT_FILES])
    args = parser.parse_args()

    paths = [Path(path) for path in args.files]
    all_errors: list[str] = []
    id_counter: Counter[str] = Counter()
    row_count = 0

    for path in paths:
        rows = load_jsonl(path)
        row_count += len(rows)
        for line_number, row in rows:
            case_id = row.get("case_id")
            if isinstance(case_id, str):
                id_counter[case_id] += 1
            all_errors.extend(validate_row(path, line_number, row))

    duplicates = sorted(identifier for identifier, count in id_counter.items() if count > 1)
    for duplicate in duplicates:
        all_errors.append(f"farm_case: duplicate case_id {duplicate}")

    for error in all_errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"files: {len(paths)}")
    print(f"rows: {row_count}")
    print(f"duplicate_case_ids: {len(duplicates)}")
    print(f"errors: {len(all_errors)}")
    raise SystemExit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
