#!/usr/bin/env python3
"""Validate training/eval JSONL files used by the planning repository."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_SAMPLE_TASK_TYPES = {
    "qa_reference",
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
    "alert_report",
}

ALLOWED_EVAL_TASK_TYPES = {
    "state_judgement",
    "action_recommendation",
    "forbidden_action",
    "failure_response",
    "robot_task_prioritization",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical", "unknown"}
ALLOWED_DECISIONS = {"block", "approval_required", "allow"}
ALLOWED_CHECK_TYPES = {
    "sensor_recheck",
    "visual_inspection",
    "device_readback",
    "operator_confirm",
    "trend_review",
    "lab_test",
    "other",
}

DEFAULT_SAMPLE_FILES = [
    Path("data/examples/state_judgement_samples.jsonl"),
    Path("data/examples/forbidden_action_samples.jsonl"),
    Path("data/examples/qa_reference_samples.jsonl"),
    Path("data/examples/action_recommendation_samples.jsonl"),
    Path("data/examples/failure_response_samples.jsonl"),
    Path("data/examples/robot_task_samples.jsonl"),
    Path("data/examples/reporting_samples.jsonl"),
]

DEFAULT_EVAL_FILES = [
    Path("evals/expert_judgement_eval_set.jsonl"),
    Path("evals/action_recommendation_eval_set.jsonl"),
    Path("evals/forbidden_action_eval_set.jsonl"),
    Path("evals/failure_response_eval_set.jsonl"),
    Path("evals/robot_task_eval_set.jsonl"),
]


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


def validate_follow_up(items: Any, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(items, list) or not items:
        return [f"{prefix}: follow_up must be a non-empty array"]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{prefix}: follow_up[{index}] must be an object")
            continue
        if item.get("check_type") not in ALLOWED_CHECK_TYPES:
            errors.append(f"{prefix}: follow_up[{index}].check_type must be one of {sorted(ALLOWED_CHECK_TYPES)}")
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            errors.append(f"{prefix}: follow_up[{index}].description must be a non-empty string")
    return errors


def validate_citations(items: Any, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(items, list):
        return [f"{prefix}: citations must be an array"]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{prefix}: citations[{index}] must be an object")
            continue
        if not isinstance(item.get("chunk_id"), str) or not item["chunk_id"].strip():
            errors.append(f"{prefix}: citations[{index}].chunk_id must be a non-empty string")
        if not isinstance(item.get("document_id"), str) or not item["document_id"].strip():
            errors.append(f"{prefix}: citations[{index}].document_id must be a non-empty string")
    return errors


def validate_sample_row(path: Path, line_number: int, row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}:{line_number}"
    required = {"sample_id", "task_type", "input", "preferred_output"}
    missing = sorted(required - set(row))
    if missing:
        errors.append(f"{prefix}: missing fields {missing}")
        return errors

    if row["task_type"] not in ALLOWED_SAMPLE_TASK_TYPES:
        errors.append(f"{prefix}: unsupported task_type {row['task_type']}")
    if not isinstance(row["input"], dict):
        errors.append(f"{prefix}: input must be an object")
    if not isinstance(row["preferred_output"], dict):
        errors.append(f"{prefix}: preferred_output must be an object")
        return errors

    output = row["preferred_output"]
    task_type = row["task_type"]

    if task_type == "qa_reference":
        if not isinstance(output.get("answer"), str) or not output["answer"].strip():
            errors.append(f"{prefix}: qa_reference preferred_output.answer must be a non-empty string")
        errors.extend(validate_citations(output.get("citations"), prefix))
    elif task_type == "forbidden_action":
        if output.get("decision") not in ALLOWED_DECISIONS:
            errors.append(f"{prefix}: forbidden_action decision must be one of {sorted(ALLOWED_DECISIONS)}")
        if not isinstance(output.get("blocked_action_type"), str) or not output["blocked_action_type"].strip():
            errors.append(f"{prefix}: forbidden_action blocked_action_type must be a non-empty string")
        errors.extend(validate_follow_up(output.get("required_follow_up"), prefix))
        errors.extend(validate_citations(output.get("citations"), prefix))
    elif task_type == "robot_task_prioritization":
        tasks = output.get("robot_tasks")
        if not isinstance(tasks, list):
            errors.append(f"{prefix}: robot_task_prioritization robot_tasks must be an array")
        errors.extend(validate_follow_up(output.get("follow_up"), prefix))
        errors.extend(validate_citations(output.get("citations"), prefix))
    elif task_type == "alert_report":
        if not isinstance(output.get("report_type"), str) or not output["report_type"].strip():
            errors.append(f"{prefix}: alert_report report_type must be a non-empty string")
        if not isinstance(output.get("title"), str) or not output["title"].strip():
            errors.append(f"{prefix}: alert_report title must be a non-empty string")
        if not isinstance(output.get("sections"), list) or not output["sections"]:
            errors.append(f"{prefix}: alert_report sections must be a non-empty array")
        errors.extend(validate_citations(output.get("citations"), prefix))
    else:
        if output.get("risk_level") not in ALLOWED_RISK_LEVELS:
            errors.append(f"{prefix}: risk_level must be one of {sorted(ALLOWED_RISK_LEVELS)}")
        errors.extend(validate_follow_up(output.get("follow_up"), prefix))
        if "citations" in output:
            errors.extend(validate_citations(output.get("citations"), prefix))
        if task_type in {"state_judgement", "climate_risk", "rootzone_diagnosis", "nutrient_risk", "sensor_fault", "pest_disease_risk", "harvest_drying", "safety_policy", "action_recommendation", "failure_response"}:
            if not isinstance(output.get("recommended_actions"), list):
                errors.append(f"{prefix}: recommended_actions must be an array")

    return errors


def validate_eval_row(path: Path, line_number: int, row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}:{line_number}"
    required = {"eval_id", "category", "expected"}
    missing = sorted(required - set(row))
    if missing:
        errors.append(f"{prefix}: missing fields {missing}")
        return errors

    task_type = row.get("task_type", row["category"])
    if task_type not in ALLOWED_EVAL_TASK_TYPES and task_type not in ALLOWED_SAMPLE_TASK_TYPES:
        errors.append(f"{prefix}: unsupported task_type {task_type}")
    if not isinstance(row["expected"], dict) or not row["expected"]:
        errors.append(f"{prefix}: expected must be a non-empty object")
        return errors
    expected = row["expected"]
    if "risk_level" in expected and expected["risk_level"] not in ALLOWED_RISK_LEVELS:
        errors.append(f"{prefix}: expected.risk_level must be one of {sorted(ALLOWED_RISK_LEVELS)}")
    if "decision" in expected and expected["decision"] not in ALLOWED_DECISIONS:
        errors.append(f"{prefix}: expected.decision must be one of {sorted(ALLOWED_DECISIONS)}")
    return errors


def validate_files(paths: list[Path], *, kind: str) -> int:
    all_errors: list[str] = []
    id_counter: Counter[str] = Counter()

    for path in paths:
        rows = load_jsonl(path)
        for line_number, row in rows:
            row_id = row.get("sample_id") if kind == "sample" else row.get("eval_id")
            if isinstance(row_id, str):
                id_counter[row_id] += 1
            if kind == "sample":
                all_errors.extend(validate_sample_row(path, line_number, row))
            else:
                all_errors.extend(validate_eval_row(path, line_number, row))

    duplicates = sorted(identifier for identifier, count in id_counter.items() if count > 1)
    for duplicate in duplicates:
        all_errors.append(f"{kind}: duplicate id {duplicate}")

    for error in all_errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"{kind}_files: {len(paths)}")
    print(f"{kind}_rows: {sum(len(load_jsonl(path)) for path in paths)}")
    print(f"{kind}_duplicate_ids: {len(duplicates)}")
    print(f"{kind}_errors: {len(all_errors)}")
    return 1 if all_errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-files", nargs="*", default=[str(path) for path in DEFAULT_SAMPLE_FILES])
    parser.add_argument("--eval-files", nargs="*", default=[str(path) for path in DEFAULT_EVAL_FILES])
    args = parser.parse_args()

    sample_status = validate_files([Path(path) for path in args.sample_files], kind="sample")
    eval_status = validate_files([Path(path) for path in args.eval_files], kind="eval")
    raise SystemExit(1 if sample_status or eval_status else 0)


if __name__ == "__main__":
    main()
