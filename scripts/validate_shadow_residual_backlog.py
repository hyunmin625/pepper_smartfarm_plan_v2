#!/usr/bin/env python3
"""Validate real shadow residual backlog JSONL files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "shadow_residual_backlog_schema.json"
RESIDUAL_ID_RE = re.compile(r"^shadow-residual-\d{8}-\d{3}$")
TOP_LEVEL_FIELDS = {
    "residual_id",
    "source_window_id",
    "source_case_request_id",
    "source_report_path",
    "zone_id",
    "task_type",
    "owner",
    "severity",
    "status",
    "failure_modes",
    "expected_fix",
    "evidence",
    "created_at",
    "updated_at",
}
EXPECTED_FIX_FIELDS = {"fix_type", "summary", "target_paths"}
EVIDENCE_FIELDS = {
    "model_output_summary",
    "operator_expected_summary",
    "validator_reason_codes",
    "citations",
    "notes",
}

BacklogRow = tuple[Path, int, dict[str, Any]]


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[BacklogRow]:
    rows: list[BacklogRow] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append((path, line_number, row))
    return rows


def load_backlog_files(paths: list[Path]) -> list[BacklogRow]:
    rows: list[BacklogRow] = []
    for path in paths:
        rows.extend(load_jsonl(path))
    return rows


def load_source_case_ids(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        for _, _, row in load_jsonl(path):
            request_id = row.get("request_id")
            if isinstance(request_id, str) and request_id:
                ids.add(request_id)
    return ids


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_array(value: Any, *, allow_empty: bool = True) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and all(_non_empty_string(v) for v in value)


def _nullable_string(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _valid_datetime(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_row(
    path: Path,
    line_number: int,
    row: dict[str, Any],
    *,
    schema: dict[str, Any],
    known_source_case_ids: set[str] | None = None,
) -> list[str]:
    prefix = f"{path}:{line_number}"
    errors: list[str] = []

    required = set(schema.get("required") or [])
    missing = sorted(required - set(row))
    if missing:
        errors.append(f"{prefix}: missing required fields {missing}")

    unknown = sorted(set(row) - TOP_LEVEL_FIELDS)
    if unknown:
        errors.append(f"{prefix}: unknown top-level fields {unknown}")

    if not _non_empty_string(row.get("residual_id")) or not RESIDUAL_ID_RE.match(str(row.get("residual_id") or "")):
        errors.append(f"{prefix}: residual_id must match shadow-residual-YYYYMMDD-NNN")
    for field in ("source_window_id", "source_case_request_id"):
        if not _non_empty_string(row.get(field)):
            errors.append(f"{prefix}: {field} must be a non-empty string")

    known_source_case_ids = known_source_case_ids or set()
    if known_source_case_ids and row.get("source_case_request_id") not in known_source_case_ids:
        errors.append(f"{prefix}: source_case_request_id not found in provided source case files")

    enums = schema.get("properties") or {}
    for field in ("owner", "severity", "status"):
        allowed = set((enums.get(field) or {}).get("enum") or [])
        if row.get(field) not in allowed:
            errors.append(f"{prefix}: {field} must be one of {sorted(allowed)}")

    if not _nullable_string(row.get("source_report_path")):
        errors.append(f"{prefix}: source_report_path must be a string or null")
    if not _nullable_string(row.get("zone_id")):
        errors.append(f"{prefix}: zone_id must be a string or null")
    if not _nullable_string(row.get("task_type")):
        errors.append(f"{prefix}: task_type must be a string or null")
    if not _string_array(row.get("failure_modes"), allow_empty=False):
        errors.append(f"{prefix}: failure_modes must be a non-empty array of strings")
    elif len(row["failure_modes"]) != len(set(row["failure_modes"])):
        errors.append(f"{prefix}: failure_modes must be unique")

    expected_fix = row.get("expected_fix")
    if not isinstance(expected_fix, dict):
        errors.append(f"{prefix}: expected_fix must be an object")
    else:
        unknown_fix = sorted(set(expected_fix) - EXPECTED_FIX_FIELDS)
        if unknown_fix:
            errors.append(f"{prefix}: expected_fix unknown fields {unknown_fix}")
        fix_type = expected_fix.get("fix_type")
        allowed_fix_types = set(
            ((enums.get("expected_fix") or {}).get("properties") or {}).get("fix_type", {}).get("enum") or []
        )
        if fix_type not in allowed_fix_types:
            errors.append(f"{prefix}: expected_fix.fix_type must be one of {sorted(allowed_fix_types)}")
        if not _non_empty_string(expected_fix.get("summary")):
            errors.append(f"{prefix}: expected_fix.summary must be a non-empty string")
        target_paths = expected_fix.get("target_paths", [])
        if not _string_array(target_paths, allow_empty=True):
            errors.append(f"{prefix}: expected_fix.target_paths must be an array of strings")

    evidence = row.get("evidence", {})
    if evidence is not None and not isinstance(evidence, dict):
        errors.append(f"{prefix}: evidence must be an object or omitted")
    elif isinstance(evidence, dict):
        unknown_evidence = sorted(set(evidence) - EVIDENCE_FIELDS)
        if unknown_evidence:
            errors.append(f"{prefix}: evidence unknown fields {unknown_evidence}")
        for field in ("model_output_summary", "operator_expected_summary", "notes"):
            if field in evidence and not _nullable_string(evidence.get(field)):
                errors.append(f"{prefix}: evidence.{field} must be a string or null")
        for field in ("validator_reason_codes", "citations"):
            if field in evidence and not _string_array(evidence.get(field), allow_empty=True):
                errors.append(f"{prefix}: evidence.{field} must be an array of strings")

    if not _valid_datetime(row.get("created_at")) or row.get("created_at") is None:
        errors.append(f"{prefix}: created_at must be an ISO date-time string")
    if not _valid_datetime(row.get("updated_at")):
        errors.append(f"{prefix}: updated_at must be an ISO date-time string or null")
    return errors


def validate_rows(
    rows: list[BacklogRow],
    *,
    schema: dict[str, Any],
    known_source_case_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    residual_ids: Counter[str] = Counter()
    for path, line_number, row in rows:
        residual_id = row.get("residual_id")
        if isinstance(residual_id, str):
            residual_ids[residual_id] += 1
        errors.extend(
            validate_row(
                path,
                line_number,
                row,
                schema=schema,
                known_source_case_ids=known_source_case_ids,
            )
        )
    for residual_id, count in sorted(residual_ids.items()):
        if count > 1:
            errors.append(f"duplicate residual_id in input files: {residual_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backlog-file", action="append", required=True)
    parser.add_argument(
        "--source-cases-file",
        action="append",
        default=[],
        help="Optional shadow case JSONL file(s); source_case_request_id must exist in them when provided.",
    )
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    args = parser.parse_args()

    schema = load_schema(Path(args.schema))
    backlog_paths = [Path(path) for path in args.backlog_file]
    source_case_paths = [Path(path) for path in args.source_cases_file]
    rows = load_backlog_files(backlog_paths)
    known_source_ids = load_source_case_ids(source_case_paths) if source_case_paths else None
    errors = validate_rows(rows, schema=schema, known_source_case_ids=known_source_ids)
    result = {
        "backlog_files": [str(path) for path in backlog_paths],
        "backlog_rows": len(rows),
        "unique_residual_ids": len({row.get("residual_id") for _, _, row in rows}),
        "source_case_files": [str(path) for path in source_case_paths],
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
