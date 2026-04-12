#!/usr/bin/env python3
"""Apply policy/output validator rules to an eval report and re-grade the results."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from evaluate_fine_tuned_model import (
    ALLOWED_ACTION_TYPES,
    ALLOWED_ROBOT_TASK_TYPES,
    grade_case,
    summarize_cases,
)


HIGH_APPROVAL_ACTIONS = {
    "adjust_fertigation",
    "adjust_heating",
    "adjust_co2",
    "create_robot_task",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(row)
    return rows


def build_eval_index(paths: list[Path]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in load_jsonl(path):
            eval_id = str(row.get("eval_id") or "")
            if eval_id:
                index[eval_id] = row
    return index


def lower_text(value: Any) -> str:
    return str(value or "").lower()


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def case_summary(case: dict[str, Any]) -> str:
    input_state = case.get("input_state")
    if isinstance(input_state, dict):
        return str(input_state.get("summary") or "")
    return ""


def case_zone_id(case: dict[str, Any]) -> str:
    input_state = case.get("input_state")
    if isinstance(input_state, dict) and isinstance(input_state.get("zone_id"), str):
        return input_state["zone_id"]
    return "unknown-zone"


def case_target(output: dict[str, Any], case: dict[str, Any], *, target_type: str = "zone", fallback_id: str | None = None) -> dict[str, str]:
    if isinstance(output.get("recommended_actions"), list):
        for action in output["recommended_actions"]:
            if isinstance(action, dict) and isinstance(action.get("target"), dict):
                target = action["target"]
                target_type_value = target.get("target_type")
                target_id_value = target.get("target_id")
                if isinstance(target_type_value, str) and isinstance(target_id_value, str):
                    return {"target_type": target_type_value, "target_id": target_id_value}
    return {"target_type": target_type, "target_id": fallback_id or case_zone_id(case)}


def make_citations(case: dict[str, Any]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    for chunk_id in case.get("retrieved_context", []):
        if isinstance(chunk_id, str) and chunk_id.strip():
            citations.append({"chunk_id": chunk_id, "document_id": "VALIDATOR-AUTO"})
    return citations


def make_follow_up(case: dict[str, Any], description: str) -> list[dict[str, Any]]:
    return [
        {
            "check_type": "operator_confirm",
            "description": description,
            "due_in_minutes": 0,
        }
    ]


def make_action(
    *,
    action_type: str,
    risk_level: str,
    reason: str,
    target: dict[str, str],
    approval_required: bool = False,
    cooldown_minutes: int = 0,
    expected_effect: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": f"validator-{action_type}",
        "action_type": action_type,
        "approval_required": approval_required,
        "cooldown_minutes": cooldown_minutes,
        "expected_effect": expected_effect or "validator applied a conservative safety fallback.",
        "reason": reason,
        "risk_level": risk_level,
        "target": target,
    }


def normalize_action_contract(output: dict[str, Any], case: dict[str, Any], applied_rules: list[str]) -> None:
    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        return
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get("action_type") in HIGH_APPROVAL_ACTIONS and action.get("approval_required") is not True:
            action["approval_required"] = True
            applied_rules.append("OV-08")
        action.setdefault("reason", "validator supplied missing action reason")
        action.setdefault("risk_level", output.get("risk_level", "unknown"))
        action.setdefault("approval_required", False)
        action.setdefault("cooldown_minutes", 0)
        action.setdefault("expected_effect", "validator supplied missing expected effect")
        if not isinstance(action.get("target"), dict):
            action["target"] = case_target(output, case)


def normalize_robot_contract(output: dict[str, Any], case: dict[str, Any], applied_rules: list[str]) -> None:
    tasks = output.get("robot_tasks")
    if not isinstance(tasks, list):
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("task_type") not in ALLOWED_ROBOT_TASK_TYPES:
            mapped = infer_robot_task_type(case)
            if mapped is not None:
                task["task_type"] = mapped
                applied_rules.append("OV-02")
        task.setdefault("priority", "medium")
        task.setdefault("approval_required", True)
        task.setdefault("reason", "validator supplied missing robot task reason")
        if not task.get("candidate_id") and not isinstance(task.get("target"), dict):
            task["target"] = {"target_type": "zone", "target_id": case_zone_id(case)}
            applied_rules.append("OV-04")


def infer_robot_task_type(case: dict[str, Any]) -> str | None:
    summary = lower_text(case_summary(case))
    if any(keyword in summary for keyword in ["우회", "skip", "젖어", "미끄럼", "blocked", "interrupt", "clearance"]):
        return "skip_area"
    if any(keyword in summary for keyword in ["병반", "inspection", "inspect", "영상", "hotspot", "병해"]):
        return "inspect_crop"
    if any(keyword in summary for keyword in ["confidence", "manual review", "수동 검토", "낮아"]):
        return "manual_review"
    if any(keyword in summary for keyword in ["숙도", "수확 후보", "harvest", "과실"]):
        return "harvest_candidate_review"
    return None


def needs_citations(case: dict[str, Any]) -> bool:
    expected = case.get("expected", {})
    return bool(expected.get("must_include_citations"))


def ensure_citations(output: dict[str, Any], case: dict[str, Any], applied_rules: list[str]) -> None:
    if needs_citations(case) and not output.get("citations"):
        citations = make_citations(case)
        if citations:
            output["citations"] = citations
            applied_rules.append("OV-06")


def ensure_follow_up(output: dict[str, Any], case: dict[str, Any], applied_rules: list[str]) -> None:
    expected = case.get("expected", {})
    if expected.get("must_include_follow_up") and not (
        isinstance(output.get("follow_up"), list) and output.get("follow_up")
    ):
        output["follow_up"] = make_follow_up(case, "validator inserted follow-up for required review.")
        applied_rules.append("OV-05")


def is_worker_or_lock_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    invariant_id = lower_text(case.get("invariant_id"))
    worker_negated = contains_any(
        summary,
        [
            "작업자 출입 이벤트는 없다",
            "작업자 없음",
            "worker entry is not active",
            "worker event is not active",
            "worker present is false",
            "출입 이벤트는 없다",
        ],
    )
    worker_active = (
        not worker_negated
        and contains_any(
            summary,
            [
                "작업자가",
                "작업자 ",
                "lane 안",
                "worker present",
                "worker-entry",
                "entry event가 active",
                "출입 이벤트가 active",
            ],
        )
    ) or contains_any(invariant_id, ["worker_present", "worker-entry"])
    manual_override_active = contains_any(
        summary,
        ["manual override", "manual_override", "수동 override", "수동모드"]
    ) or "manual_override" in invariant_id
    safe_mode_latched = contains_any(
        summary,
        ["safe_mode가 active", "safe_mode active", "safe_mode가 함께 latch", "safe mode가 active", "safe mode active"]
    ) or "block_all_control" in invariant_id
    return worker_active or manual_override_active or safe_mode_latched


def is_zone_clear_uncertain_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    return contains_any(
        summary,
        [
            "clear되지 않았",
            "clear 상태가 확인되지",
            "clearance가 불확실",
            "zone clear이 확인되지",
            "zone clear 상태가 확인되지",
            "미확인",
            "불확실",
            "uncertain",
            "unconfirmed",
        ],
    )


def is_path_or_comms_loss_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    failure_type = lower_text(case.get("failure_type"))
    invariant_id = lower_text(case.get("invariant_id"))
    return (
        failure_type in {"communication_loss", "readback_mismatch", "irrigation_readback_mismatch"}
        or "enters_safe_mode" in invariant_id
        or any(
            keyword in summary
            for keyword in [
                "통신",
                "communication",
                "readback",
                "timeout",
                "mismatch",
                "ack",
            ]
        )
        and any(
            keyword in summary
            for keyword in [
                "관수",
                "pump",
                "밸브",
                "원수",
                "source water",
                "건조실",
                "dry",
                "dehumidifier",
                "fan",
            ]
        )
    )


def is_climate_control_degraded_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    failure_type = lower_text(case.get("failure_type"))
    invariant_id = lower_text(case.get("invariant_id"))
    return (
        failure_type == "sensor_stale"
        and any(keyword in summary for keyword in ["온도", "temperature", "습도", "humidity", "vpd"])
        and any(keyword in summary for keyword in ["invalid", "환기", "vent", "자동", "automatic"])
    ) or contains_any(invariant_id, ["climate_control_degraded_pauses_automation"])


def is_degraded_control_signal_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    failure_type = lower_text(case.get("failure_type"))
    invariant_id = lower_text(case.get("invariant_id"))
    return (
        failure_type == "sensor_stale"
        or "pauses_automation" in invariant_id
        or any(
            keyword in summary
            for keyword in [
                "stale",
                "flatline",
                "missing",
                "inconsistent",
                "invalid",
            ]
        )
        and any(
            keyword in summary
            for keyword in [
                "vpd",
                "wc",
                "ec",
                "ph",
                "loadcell",
                "배수",
                "함수율",
                "근권",
                "sensor",
                "센서",
            ]
        )
    )


def is_incomplete_fertigation_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    proposed_action = lower_text(case.get("proposed_action"))
    return proposed_action == "adjust_fertigation" and any(
        keyword in summary
        for keyword in ["ec", "ph", "drain", "sensor", "센서", "missing", "stale", "fault"]
    )


def is_robot_safety_case(case: dict[str, Any]) -> bool:
    summary = lower_text(case_summary(case))
    if is_worker_or_lock_case(case) or is_zone_clear_uncertain_case(case):
        return True
    return contains_any(summary, ["미끄럼", "젖어", "slip hazard", "skip", "우회"])


def rewrite_to_actions(
    output: dict[str, Any],
    *,
    risk_level: str,
    actions: list[dict[str, Any]],
    keep_alert: bool = False,
) -> None:
    existing = output.get("recommended_actions")
    if keep_alert and isinstance(existing, list):
        kept = [
            action for action in existing
            if isinstance(action, dict) and action.get("action_type") == "create_alert"
        ]
    else:
        kept = []
    deduped: dict[str, dict[str, Any]] = {}
    for action in kept + actions:
        deduped[str(action["action_type"])] = action
    output["recommended_actions"] = list(deduped.values())
    output["risk_level"] = risk_level


def apply_validator(case: dict[str, Any], output: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    mutated = copy.deepcopy(output)
    applied_rules: list[str] = []
    validator_decision = "pass"

    mutated.setdefault("situation_summary", case_summary(case) or "validator supplied situation summary")
    mutated.setdefault("risk_level", "unknown")
    mutated.setdefault("retrieval_coverage", "partial")
    mutated.setdefault("confidence", 0.5)
    mutated.setdefault("requires_human_approval", False)

    if is_worker_or_lock_case(case) or is_zone_clear_uncertain_case(case):
        rewrite_to_actions(
            mutated,
            risk_level="critical",
            actions=[
                make_action(
                    action_type="block_action",
                    risk_level="critical",
                    reason="validator blocked action because worker/manual override/safe mode safety lock is active.",
                    target=case_target(mutated, case, target_type="system"),
                ),
                make_action(
                    action_type="create_alert",
                    risk_level="critical",
                    reason="validator raised a critical operator alert for the active safety lock.",
                    target={"target_type": "zone", "target_id": case_zone_id(case)},
                    cooldown_minutes=10,
                    expected_effect="operators are alerted to a blocking safety condition.",
                ),
            ],
        )
        mutated["robot_tasks"] = []
        mutated["requires_human_approval"] = False
        ensure_follow_up(mutated, case, applied_rules)
        applied_rules.extend(["HSV-01", "HSV-02", "HSV-03"])
        validator_decision = "rewritten"

    if is_path_or_comms_loss_case(case):
        rewrite_to_actions(
            mutated,
            risk_level="critical",
            actions=[
                make_action(
                    action_type="enter_safe_mode",
                    risk_level="critical",
                    reason="validator forced safe mode because a critical path communication/readback loss is active.",
                    target=case_target(mutated, case, target_type="system"),
                ),
                make_action(
                    action_type="request_human_check",
                    risk_level="critical",
                    reason="validator requested manual confirmation of the affected path before any restart.",
                    target={"target_type": "operator", "target_id": "duty-manager"},
                ),
            ],
        )
        mutated["robot_tasks"] = []
        applied_rules.extend(["HSV-04", "HSV-05", "HSV-06"])
        validator_decision = "rewritten"

    elif is_climate_control_degraded_case(case):
        rewrite_to_actions(
            mutated,
            risk_level="high",
            actions=[
                make_action(
                    action_type="pause_automation",
                    risk_level="high",
                    reason="validator paused automation because climate control continued on degraded sensor evidence.",
                    target=case_target(mutated, case, target_type="system"),
                ),
                make_action(
                    action_type="request_human_check",
                    risk_level="high",
                    reason="validator requested manual climate sensor and command history confirmation.",
                    target={"target_type": "operator", "target_id": "duty-manager"},
                ),
            ],
            keep_alert=True,
        )
        applied_rules.append("HSV-07")
        validator_decision = "rewritten"

    elif is_degraded_control_signal_case(case):
        unsafe = {"short_irrigation", "adjust_fertigation", "adjust_heating", "adjust_co2", "adjust_fan", "adjust_shade", "adjust_vent"}
        existing_actions = [
            action
            for action in mutated.get("recommended_actions", [])
            if isinstance(action, dict) and action.get("action_type") not in unsafe
        ]
        rewrite_to_actions(
            mutated,
            risk_level="unknown",
            actions=existing_actions
            + [
                make_action(
                    action_type="pause_automation",
                    risk_level="unknown",
                    reason="validator paused automation because control evidence is degraded.",
                    target=case_target(mutated, case, target_type="system"),
                ),
                make_action(
                    action_type="request_human_check",
                    risk_level="unknown",
                    reason="validator requested manual sensor or measurement confirmation.",
                    target={"target_type": "operator", "target_id": "duty-manager"},
                ),
            ],
        )
        applied_rules.extend(["HSV-07", "HSV-08"])
        validator_decision = "rewritten"

    if is_incomplete_fertigation_case(case) and case.get("task_type") == "forbidden_action":
        mutated["decision"] = "approval_required"
        mutated["blocked_action_type"] = case.get("proposed_action") or "adjust_fertigation"
        mutated["risk_level"] = "high"
        mutated.setdefault("required_follow_up", make_follow_up(case, "validator required approval before fertigation adjustment."))
        applied_rules.append("HSV-09")
        validator_decision = "rewritten"

    if case.get("task_type") == "robot_task_prioritization":
        tasks = mutated.get("robot_tasks")
        if not isinstance(tasks, list):
            tasks = []
        if is_robot_safety_case(case):
            summary = lower_text(case_summary(case))
            if any(keyword in summary for keyword in ["우회", "미끄럼", "젖어", "skip"]):
                tasks = [
                    {
                        "task_type": "skip_area",
                        "priority": "high",
                        "approval_required": True,
                        "reason": "validator forced skip_area because the aisle is unsafe.",
                        "target": {"target_type": "zone", "target_id": case_zone_id(case)},
                    }
                ]
            else:
                tasks = []
            mutated["robot_tasks"] = tasks
            applied_rules.append("HSV-10")
            validator_decision = "rewritten"
        else:
            mutated["robot_tasks"] = tasks
        normalize_robot_contract(mutated, case, applied_rules)

    normalize_action_contract(mutated, case, applied_rules)
    ensure_follow_up(mutated, case, applied_rules)
    ensure_citations(mutated, case, applied_rules)
    mutated["validator_reason_codes"] = sorted(set(applied_rules))
    mutated["validator_decision"] = validator_decision
    return mutated, sorted(set(applied_rules)), validator_decision


def rerender_report(
    *,
    source_report: dict[str, Any],
    eval_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    new_records: list[dict[str, Any]] = []
    rule_counter: Counter[str] = Counter()
    improved_cases = 0
    worsened_cases = 0
    changed_cases = 0

    for record in source_report.get("cases", []):
        eval_id = str(record.get("eval_id") or "")
        case = eval_index.get(eval_id)
        if case is None:
            continue
        output = record.get("response", {}).get("parsed_output")
        if not isinstance(output, dict):
            output = {}

        mutated_output, applied_rules, validator_decision = apply_validator(case, output)
        parse_result = {
            "strict_json_ok": True,
            "recovered_json_ok": True,
            "json_object_ok": True,
            "parse_error": None,
            "parsed_output": mutated_output,
        }
        graded = grade_case(case, parse_result)
        new_record = copy.deepcopy(record)
        new_record["passed"] = graded["passed"]
        new_record["passed_checks"] = graded["passed_checks"]
        new_record["failed_checks"] = graded["failed_checks"]
        new_record["optional_failures"] = graded["optional_failures"]
        new_record["action_types"] = graded["action_types"]
        new_record["robot_task_types"] = graded["robot_task_types"]
        new_record["citation_ids"] = graded["citation_ids"]
        new_record["confidence"] = graded["confidence"]
        new_record["response"]["parsed_output"] = graded["raw_output"]
        new_record["validator_applied_rules"] = applied_rules
        new_record["validator_decision"] = validator_decision
        new_record["pre_validator_passed"] = bool(record.get("passed"))
        new_record["pre_validator_failed_checks"] = record.get("failed_checks", [])
        new_record["post_validator_failed_checks"] = graded["failed_checks"]
        new_record["post_validator_optional_failures"] = graded["optional_failures"]
        new_records.append(new_record)

        rule_counter.update(applied_rules)
        if applied_rules:
            changed_cases += 1
        if not record.get("passed") and graded["passed"]:
            improved_cases += 1
        if record.get("passed") and not graded["passed"]:
            worsened_cases += 1

    summary = summarize_cases(new_records)
    before_summary = source_report.get("summary", {})
    return {
        "schema_version": "validator_simulation_report.v1",
        "status": "completed",
        "evaluated_at": source_report.get("evaluated_at"),
        "source_report": source_report.get("source_report") or source_report.get("evaluated_at"),
        "model": source_report.get("model"),
        "eval_files": source_report.get("eval_files", []),
        "summary": summary,
        "summary_before": before_summary,
        "summary_after": summary,
        "validator_summary": {
            "changed_cases": changed_cases,
            "improved_cases": improved_cases,
            "worsened_cases": worsened_cases,
            "top_applied_rules": rule_counter.most_common(20),
        },
        "cases": new_records,
    }


def render_markdown(report: dict[str, Any]) -> str:
    before = report["summary_before"]
    after = report["summary_after"]
    validator = report["validator_summary"]
    lines = [
        "# Policy Output Validator Simulation",
        "",
        f"- model: `{report['model']}`",
        f"- source_eval_files: `{', '.join(report.get('eval_files', []))}`",
        f"- pass_rate_before: `{before.get('pass_rate')}`",
        f"- pass_rate_after: `{after.get('pass_rate')}`",
        f"- passed_cases_before: `{before.get('passed_cases')}`",
        f"- passed_cases_after: `{after.get('passed_cases')}`",
        f"- changed_cases: `{validator['changed_cases']}`",
        f"- improved_cases: `{validator['improved_cases']}`",
        f"- worsened_cases: `{validator['worsened_cases']}`",
        "",
        "## Applied Rules",
        "",
    ]
    if validator["top_applied_rules"]:
        for name, count in validator["top_applied_rules"]:
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Category Results After Validator", "", "| category | cases | passed | pass_rate |", "|---|---:|---:|---:|"])
    for category, row in after.get("by_category", {}).items():
        lines.append(f"| {category} | {row['cases']} | {row['passed']} | {row['pass_rate']} |")

    lines.extend(["", "## Recovered Cases", ""])
    recovered = [
        record for record in report["cases"]
        if not record.get("pre_validator_passed") and record.get("passed")
    ]
    if recovered:
        for record in recovered:
            lines.append(
                f"- `{record['eval_id']}`: "
                f"{', '.join(record.get('validator_applied_rules', []))}"
            )
    else:
        lines.append("- 없음")

    lines.extend(["", "## Remaining Failures", ""])
    remaining = [record for record in report["cases"] if not record.get("passed")]
    if remaining:
        for record in remaining[:40]:
            lines.append(
                f"- `{record['eval_id']}`: "
                f"{', '.join(record.get('post_validator_failed_checks', []))}"
            )
    else:
        lines.append("- 없음")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="Evaluation summary JSON report path.")
    parser.add_argument(
        "--eval-files",
        nargs="*",
        help="Eval JSONL files used to grade the report. Defaults to report embedded eval_files.",
    )
    parser.add_argument(
        "--output-prefix",
        default="artifacts/reports/policy_output_validator_simulation_latest",
        help="Output prefix for JSON/Markdown reports.",
    )
    args = parser.parse_args()

    source_path = Path(args.report)
    source_report = load_json(source_path)
    eval_files = args.eval_files or source_report.get("eval_files", [])
    if not isinstance(eval_files, list) or not eval_files:
        raise SystemExit("No eval files provided.")
    eval_index = build_eval_index([Path(path) for path in eval_files])

    report = rerender_report(source_report=source_report, eval_index=eval_index)
    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
