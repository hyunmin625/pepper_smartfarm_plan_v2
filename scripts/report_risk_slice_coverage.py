#!/usr/bin/env python3
"""Report risk-label and product-blocking slice coverage across training and eval sets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from evaluate_fine_tuned_model import ALLOWED_ROBOT_TASK_TYPES
from training_data_config import training_sample_files


DEFAULT_DATASETS = {
    "training": Path("artifacts/training/combined_training_samples.jsonl"),
    "extended_eval": Path("artifacts/training/combined_eval_cases.jsonl"),
    "blind_holdout": Path("evals/blind_holdout_eval_set.jsonl"),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def load_default_training_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in training_sample_files():
        rows.extend(load_jsonl(path))
    rows.sort(key=lambda item: str(item.get("sample_id") or ""))
    return rows


def task_type_for_row(row: dict[str, Any]) -> str:
    return str(row.get("task_type") or row.get("category") or "unknown")


def row_identifier(row: dict[str, Any]) -> str:
    return str(row.get("sample_id") or row.get("eval_id") or "unknown")


def row_input(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("input")
    if isinstance(value, dict):
        return value
    value = row.get("input_state")
    if isinstance(value, dict):
        return value
    return {}


def row_output(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("preferred_output")
    if isinstance(value, dict):
        return value
    value = row.get("expected")
    if isinstance(value, dict):
        return value
    return {}


def risk_level_for_row(row: dict[str, Any]) -> str | None:
    value = row_output(row).get("risk_level")
    return str(value) if isinstance(value, str) else None


def recommended_action_types(row: dict[str, Any]) -> set[str]:
    output = row_output(row)
    if "required_action_types" in output and isinstance(output["required_action_types"], list):
        return {str(item) for item in output["required_action_types"] if isinstance(item, str)}
    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        return set()
    types = set()
    for item in actions:
        if isinstance(item, dict) and isinstance(item.get("action_type"), str):
            types.add(str(item["action_type"]))
    return types


def robot_task_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = row_output(row).get("robot_tasks")
    if not isinstance(tasks, list):
        return []
    return [item for item in tasks if isinstance(item, dict)]


def active_constraints(row: dict[str, Any]) -> set[str]:
    payload = row_input(row)
    values = payload.get("active_constraints")
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values if isinstance(item, str)}


def active_faults(row: dict[str, Any]) -> set[str]:
    payload = row_input(row)
    values = payload.get("active_faults")
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values if isinstance(item, str)}


def failure_type(row: dict[str, Any]) -> str:
    return str(row_input(row).get("failure_type") or "")


def text_blob(row: dict[str, Any]) -> str:
    payload = row_input(row)
    parts = [
        str(payload.get("state_summary") or ""),
        str(payload.get("summary") or ""),
        failure_type(row),
        " ".join(sorted(active_faults(row))),
        " ".join(sorted(active_constraints(row))),
        " ".join(str(item) for item in row.get("product_dimensions", []) if isinstance(item, str)),
        " ".join(str(item) for item in row.get("gate_tags", []) if isinstance(item, str)),
    ]
    return " ".join(parts).lower()


def is_safety_hard_block_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) != "safety_policy":
        return False
    risk = risk_level_for_row(row)
    actions = recommended_action_types(row)
    if risk == "critical" and {"block_action", "create_alert"}.issubset(actions):
        return True
    constraints = active_constraints(row)
    faults = active_faults(row)
    return bool(
        {"manual_override_active", "worker_present", "safe_mode_active"} & constraints
        or {"manual_override_active", "worker_present"} & faults
        or {"manual_scouting_active", "reentry_pending", "dry_room_manual_inspection"} & constraints
    )


def is_sensor_unknown_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) != "sensor_fault":
        return False
    if risk_level_for_row(row) == "unknown":
        return True
    constraints = active_constraints(row)
    faults = active_faults(row)
    text = text_blob(row)
    markers = {
        "core_sensor_fault",
        "slab_wc_missing",
        "drain_sensor_stale",
        "drain_sensor_flatline",
    }
    return bool(markers & constraints) or any(
        token in text
        for token in ("sensor stale", "sensor_stale", "missing", "flatline", "calibration", "inconsistent")
    ) or bool({"air_temp_sensor_stale", "co2_sensor_stale"} & faults)


def is_evidence_incomplete_unknown_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) not in {"rootzone_diagnosis", "nutrient_risk"}:
        return False
    if risk_level_for_row(row) == "unknown":
        return True
    constraints = active_constraints(row)
    return bool(
        constraints
        & {
            "rootzone_evidence_incomplete",
            "fertigation_evidence_incomplete",
            "drain_sensor_flatline",
            "drain_sensor_stale",
            "slab_wc_missing",
            "core_sensor_fault",
        }
    )


def is_failure_safe_mode_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) != "failure_response":
        return False
    actions = recommended_action_types(row)
    if {"enter_safe_mode", "request_human_check"}.issubset(actions):
        return True
    text = text_blob(row)
    water_path_tokens = (
        "dry-room-comm-loss",
        "irrigation_pump_comm_loss",
        "irrigation_valve_readback_mismatch",
        "source_water",
        "source-water",
        "source water",
        "water-room",
    )
    if any(token in text for token in water_path_tokens):
        return True
    failure = failure_type(row).lower()
    if failure in {"irrigation_readback_mismatch", "readback_mismatch"} and any(
        token in text for token in water_path_tokens if token != "dry-room-comm-loss"
    ):
        return True
    if failure == "communication_loss" and any(
        token in text for token in ("dry-room-comm-loss", "irrigation_pump_comm_loss", "source_water", "source-water", "source water")
    ):
        return True
    return False


def is_robot_contract_slice(row: dict[str, Any]) -> bool:
    return task_type_for_row(row) == "robot_task_prioritization"


def is_gt_master_dryback_high_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) not in {"action_recommendation", "rootzone_diagnosis"}:
        return False
    text = text_blob(row)
    return (
        ("gt master" in text or "gt_master" in text)
        and any(token in text for token in ("dry-back", "dryback"))
        and any(token in text for token in ("wc", "함수율"))
        and any(token in text for token in ("잎 처짐", "wilt"))
    )


def is_nursery_cold_humid_high_slice(row: dict[str, Any]) -> bool:
    if task_type_for_row(row) != "climate_risk":
        return False
    text = text_blob(row)
    return (
        ("delta 6.5" in text or "delta65" in text or "육묘" in text or "nursery" in text)
        and any(token in text for token in ("해진", "post_sunset", "post-sunset", "야간"))
        and any(token in text for token in ("습도", "humidity"))
        and any(token in text for token in ("잎 젖음", "leaf wet", "결로"))
    )


def rule_checks(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    risk = risk_level_for_row(row)
    actions = recommended_action_types(row)
    robot_tasks = robot_task_rows(row)

    if is_safety_hard_block_slice(row):
        if risk != "critical":
            failures.append("safety_hard_block_risk_not_critical")
        if not {"block_action", "create_alert"}.issubset(actions):
            failures.append("safety_hard_block_actions_missing")

    if is_sensor_unknown_slice(row) and risk != "unknown":
        failures.append("sensor_fault_should_be_unknown")

    if is_evidence_incomplete_unknown_slice(row):
        if risk != "unknown":
            failures.append("evidence_incomplete_should_be_unknown")
        if "request_human_check" not in actions:
            failures.append("evidence_incomplete_missing_request_human_check")

    if is_failure_safe_mode_slice(row):
        if risk != "critical":
            failures.append("failure_safe_mode_risk_not_critical")
        if not {"enter_safe_mode", "request_human_check"}.issubset(actions):
            failures.append("failure_safe_mode_actions_missing")

    if is_robot_contract_slice(row):
        for item in robot_tasks:
            task_type = item.get("task_type")
            if isinstance(task_type, str) and task_type not in ALLOWED_ROBOT_TASK_TYPES:
                failures.append("robot_task_enum_invalid")
            if not item.get("candidate_id") and not item.get("target"):
                failures.append("robot_task_target_missing")
                break

    if is_gt_master_dryback_high_slice(row):
        if risk != "high":
            failures.append("gt_master_dryback_should_be_high")
        if not {"create_alert", "request_human_check"}.issubset(actions):
            failures.append("gt_master_dryback_actions_missing")

    if is_nursery_cold_humid_high_slice(row):
        if risk != "high":
            failures.append("nursery_cold_humid_should_be_high")
        if not {"create_alert", "request_human_check"}.issubset(actions):
            failures.append("nursery_cold_humid_actions_missing")

    return failures


def slice_hits(row: dict[str, Any]) -> list[str]:
    names: list[str] = []
    if is_safety_hard_block_slice(row):
        names.append("safety_hard_block")
    if is_sensor_unknown_slice(row):
        names.append("sensor_unknown")
    if is_evidence_incomplete_unknown_slice(row):
        names.append("evidence_incomplete_unknown")
    if is_failure_safe_mode_slice(row):
        names.append("failure_safe_mode")
    if is_robot_contract_slice(row):
        names.append("robot_contract")
    if is_gt_master_dryback_high_slice(row):
        names.append("gt_master_dryback_high")
    if is_nursery_cold_humid_high_slice(row):
        names.append("nursery_cold_humid_high")
    return names


def summarize_dataset(name: str, rows: list[dict[str, Any]]) -> int:
    task_risk: dict[str, Counter[str]] = {}
    slice_counter: Counter[str] = Counter()
    rule_failures: Counter[str] = Counter()
    failure_examples: dict[str, list[str]] = {}

    for row in rows:
        task = task_type_for_row(row)
        risk = risk_level_for_row(row)
        if risk:
            task_risk.setdefault(task, Counter())[risk] += 1

        for slice_name in slice_hits(row):
            slice_counter[slice_name] += 1

        failures = rule_checks(row)
        for failure in failures:
            rule_failures[failure] += 1
            failure_examples.setdefault(failure, []).append(row_identifier(row))

    print(f"[{name}]")
    print(f"rows={len(rows)}")
    print("risk_by_task")
    for task in sorted(task_risk):
        print(f"  {task}: {dict(task_risk[task])}")
    print("slice_coverage")
    for slice_name in (
        "safety_hard_block",
        "sensor_unknown",
        "evidence_incomplete_unknown",
        "failure_safe_mode",
        "robot_contract",
        "gt_master_dryback_high",
        "nursery_cold_humid_high",
    ):
        print(f"  {slice_name}: {slice_counter[slice_name]}")
    print("rule_failures")
    if not rule_failures:
        print("  none")
    else:
        for failure, count in rule_failures.most_common():
            examples = ", ".join(failure_examples[failure][:5])
            print(f"  {failure}: {count} [{examples}]")
    print()
    return sum(rule_failures.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training", default=DEFAULT_DATASETS["training"].as_posix())
    parser.add_argument("--extended-eval", default=DEFAULT_DATASETS["extended_eval"].as_posix())
    parser.add_argument("--blind-holdout", default=DEFAULT_DATASETS["blind_holdout"].as_posix())
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any rubric mismatch is found.",
    )
    args = parser.parse_args()

    total_failures = 0
    training_path = Path(args.training)
    training_rows = (
        load_default_training_rows()
        if training_path.as_posix() == DEFAULT_DATASETS["training"].as_posix()
        else load_jsonl(training_path)
    )
    total_failures += summarize_dataset("training", training_rows)
    total_failures += summarize_dataset("extended_eval", load_jsonl(Path(args.extended_eval)))
    total_failures += summarize_dataset("blind_holdout", load_jsonl(Path(args.blind_holdout)))

    if args.strict and total_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
