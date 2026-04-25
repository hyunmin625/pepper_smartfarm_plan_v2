#!/usr/bin/env python3
"""Validate shadow-mode case JSONL files before ops-api ingestion."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_TASK_TYPES = {
    "state_judgement",
    "climate_risk",
    "rootzone_diagnosis",
    "nutrient_risk",
    "sensor_fault",
    "pest_disease_risk",
    "harvest_drying",
    "safety_policy",
    "action_recommendation",
    "forbidden_action",
    "failure_response",
    "robot_task_prioritization",
}
ALLOWED_FORBIDDEN_DECISIONS = {"block", "approval_required", "allow"}
REQUIRED_TOP_LEVEL_FIELDS = {"request_id", "task_type", "metadata", "context", "output", "observed"}
REQUIRED_METADATA_FIELDS = {"model_id", "prompt_id", "dataset_id", "eval_set_id", "retrieval_profile_id"}
REQUIRED_CONTEXT_FIELDS = {"farm_id", "zone_id", "task_type", "summary"}
REAL_REQUEST_ID_RE = re.compile(r"^prod-shadow-(\d{8})-\d{3,}$")
REAL_EVAL_SET_RE = re.compile(r"^shadow-prod-(\d{8})$")
REAL_CASE_FILE_RE = re.compile(r"^shadow_mode_cases_(\d{8})(?:_part\d+)?\.jsonl$")
SEED_OR_OFFLINE_EVAL_IDS = {
    "shadow_seed_day0",
    "blind_holdout50_offline_shadow_replay",
    "shadow-day-20260412",
}

CaseRow = tuple[Path, int, dict[str, Any]]


def load_case_file(path: Path) -> list[CaseRow]:
    rows: list[CaseRow] = []
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


def load_case_files(paths: list[Path]) -> list[CaseRow]:
    rows: list[CaseRow] = []
    for path in paths:
        rows.extend(load_case_file(path))
    return rows


def load_existing_request_ids(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict) and isinstance(row.get("request_id"), str):
                    ids.add(row["request_id"])
    return ids


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_array(value: Any, *, allow_empty: bool = True) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and all(_non_empty_string(item) for item in value)


def _validate_required_strings(mapping: dict[str, Any], fields: set[str], prefix: str) -> list[str]:
    errors: list[str] = []
    for field in sorted(fields):
        if not _non_empty_string(mapping.get(field)):
            errors.append(f"{prefix}: {field} must be a non-empty string")
    return errors


def _date_from_real_case_file(path: Path) -> str | None:
    match = REAL_CASE_FILE_RE.match(path.name)
    return match.group(1) if match else None


def validate_case_row(
    path: Path,
    line_number: int,
    row: dict[str, Any],
    *,
    real_case: bool,
    real_eval_set_prefix: str,
    expected_date: str | None = None,
) -> list[str]:
    prefix = f"{path}:{line_number}"
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(row))
    if missing:
        return [f"{prefix}: missing fields {missing}"]

    request_id = row.get("request_id")
    task_type = row.get("task_type")
    request_date: str | None = None
    if not _non_empty_string(request_id):
        errors.append(f"{prefix}: request_id must be a non-empty string")
    elif real_case:
        request_match = REAL_REQUEST_ID_RE.match(request_id)
        if not request_match:
            errors.append(f"{prefix}: request_id must match prod-shadow-YYYYMMDD-NNN for real ops cases")
        else:
            request_date = request_match.group(1)

    if task_type not in ALLOWED_TASK_TYPES:
        errors.append(f"{prefix}: unsupported task_type {task_type!r}")

    metadata = row.get("metadata")
    context = row.get("context")
    output = row.get("output")
    observed = row.get("observed")
    if not isinstance(metadata, dict):
        errors.append(f"{prefix}: metadata must be an object")
        metadata = {}
    if not isinstance(context, dict):
        errors.append(f"{prefix}: context must be an object")
        context = {}
    if not isinstance(output, dict):
        errors.append(f"{prefix}: output must be an object")
        output = {}
    if not isinstance(observed, dict):
        errors.append(f"{prefix}: observed must be an object")
        observed = {}

    errors.extend(_validate_required_strings(metadata, REQUIRED_METADATA_FIELDS, f"{prefix}: metadata"))
    errors.extend(_validate_required_strings(context, REQUIRED_CONTEXT_FIELDS, f"{prefix}: context"))

    if context.get("task_type") != task_type:
        errors.append(f"{prefix}: context.task_type must match task_type")

    eval_set_id = str(metadata.get("eval_set_id") or "")
    if real_case:
        eval_set_date: str | None = None
        eval_set_match = REAL_EVAL_SET_RE.match(eval_set_id)
        if real_eval_set_prefix and not eval_set_match:
            errors.append(f"{prefix}: real ops eval_set_id must match shadow-prod-YYYYMMDD")
        elif eval_set_match:
            eval_set_date = eval_set_match.group(1)
        file_date = _date_from_real_case_file(path)
        expected_dates = {
            label: value
            for label, value in (
                ("--expected-date", expected_date),
                ("case filename", file_date),
                ("request_id", request_date),
                ("metadata.eval_set_id", eval_set_date),
            )
            if value
        }
        if len(set(expected_dates.values())) > 1:
            detail = ", ".join(f"{label}={value}" for label, value in expected_dates.items())
            errors.append(f"{prefix}: real ops date values must match ({detail})")
        farm_id = str(context.get("farm_id") or "")
        if "demo" in farm_id.lower():
            errors.append(f"{prefix}: real ops case must not use demo farm_id")
        if eval_set_id in SEED_OR_OFFLINE_EVAL_IDS or "seed" in eval_set_id.lower() or "offline" in eval_set_id.lower():
            errors.append(f"{prefix}: real ops case must not use seed/offline eval_set_id")
        if not isinstance(observed.get("operator_agreement"), bool):
            errors.append(f"{prefix}: real ops observed.operator_agreement must be a boolean")

    if task_type == "forbidden_action":
        decision = output.get("decision")
        if decision not in ALLOWED_FORBIDDEN_DECISIONS:
            errors.append(f"{prefix}: output.decision must be one of {sorted(ALLOWED_FORBIDDEN_DECISIONS)}")
        if decision in {"block", "approval_required"} and not _non_empty_string(output.get("blocked_action_type")):
            errors.append(f"{prefix}: output.blocked_action_type is required when decision blocks or escalates")
        operator_decision = observed.get("operator_decision")
        if operator_decision not in ALLOWED_FORBIDDEN_DECISIONS:
            errors.append(f"{prefix}: observed.operator_decision must be one of {sorted(ALLOWED_FORBIDDEN_DECISIONS)}")
        if operator_decision == "block" and not _non_empty_string(observed.get("operator_blocked_action_type")):
            errors.append(f"{prefix}: observed.operator_blocked_action_type is required when operator_decision=block")
    elif task_type == "robot_task_prioritization":
        if not isinstance(output.get("robot_tasks"), list):
            errors.append(f"{prefix}: output.robot_tasks must be an array")
        if "operator_robot_task_types" not in observed:
            errors.append(f"{prefix}: observed.operator_robot_task_types is required for robot_task_prioritization")
        elif not _string_array(observed.get("operator_robot_task_types"), allow_empty=True):
            errors.append(f"{prefix}: observed.operator_robot_task_types must be an array of strings")
    else:
        if not isinstance(output.get("recommended_actions"), list):
            errors.append(f"{prefix}: output.recommended_actions must be an array")
        if "operator_action_types" not in observed:
            errors.append(f"{prefix}: observed.operator_action_types is required")
        elif not _string_array(observed.get("operator_action_types"), allow_empty=True):
            errors.append(f"{prefix}: observed.operator_action_types must be an array of strings")

    if "operator_action_types" in observed and not _string_array(observed.get("operator_action_types"), allow_empty=True):
        errors.append(f"{prefix}: observed.operator_action_types must be an array of strings")
    if "operator_robot_task_types" in observed and not _string_array(
        observed.get("operator_robot_task_types"), allow_empty=True
    ):
        errors.append(f"{prefix}: observed.operator_robot_task_types must be an array of strings")
    if "operator_agreement" in observed and not isinstance(observed.get("operator_agreement"), bool):
        errors.append(f"{prefix}: observed.operator_agreement must be a boolean when present")
    if not isinstance(observed.get("critical_disagreement"), bool):
        errors.append(f"{prefix}: observed.critical_disagreement must be a boolean")
    if not isinstance(observed.get("manual_override_used"), bool):
        errors.append(f"{prefix}: observed.manual_override_used must be a boolean")
    if not _non_empty_string(observed.get("growth_stage")):
        errors.append(f"{prefix}: observed.growth_stage must be a non-empty string")

    requires_citations = context.get("requires_citations") is True
    if requires_citations and not isinstance(output.get("citations"), list):
        errors.append(f"{prefix}: output.citations must be an array when context.requires_citations=true")

    return errors


def validate_case_rows(
    rows: list[CaseRow],
    *,
    real_case: bool = False,
    existing_request_ids: set[str] | None = None,
    real_eval_set_prefix: str = "shadow-prod-",
    expected_date: str | None = None,
) -> list[str]:
    errors: list[str] = []
    request_ids: Counter[str] = Counter()
    for path, line_number, row in rows:
        request_id = row.get("request_id")
        if isinstance(request_id, str):
            request_ids[request_id] += 1
        errors.extend(
            validate_case_row(
                path,
                line_number,
                row,
                real_case=real_case,
                real_eval_set_prefix=real_eval_set_prefix,
                expected_date=expected_date,
            )
        )

    for request_id, count in sorted(request_ids.items()):
        if count > 1:
            errors.append(f"duplicate request_id in input files: {request_id}")

    existing_request_ids = existing_request_ids or set()
    for request_id in sorted(set(request_ids) & existing_request_ids):
        errors.append(f"request_id already exists in audit log: {request_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-file", action="append", required=True)
    parser.add_argument("--existing-audit-log", action="append", default=[])
    parser.add_argument("--real-case", action="store_true", help="Apply real ops case rules.")
    parser.add_argument(
        "--real-eval-set-prefix",
        default="shadow-prod-",
        help="Required eval_set_id prefix when --real-case is enabled. Use empty string to disable.",
    )
    parser.add_argument(
        "--expected-date",
        default=None,
        help="Required YYYYMMDD value for real-case filename/request_id/eval_set_id consistency.",
    )
    args = parser.parse_args()

    case_paths = [Path(path) for path in args.cases_file]
    rows = load_case_files(case_paths)
    existing_ids = load_existing_request_ids([Path(path) for path in args.existing_audit_log])
    errors = validate_case_rows(
        rows,
        real_case=args.real_case,
        existing_request_ids=existing_ids,
        real_eval_set_prefix=args.real_eval_set_prefix,
        expected_date=args.expected_date,
    )

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(
        json.dumps(
            {
                "case_files": [path.as_posix() for path in case_paths],
                "case_rows": len(rows),
                "unique_request_ids": len({row["request_id"] for _, _, row in rows if isinstance(row.get("request_id"), str)}),
                "real_case": args.real_case,
                "existing_audit_logs": args.existing_audit_log,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
