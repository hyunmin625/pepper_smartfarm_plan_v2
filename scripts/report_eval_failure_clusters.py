#!/usr/bin/env python3
"""Cluster evaluation failures into reusable root-cause buckets."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT_CAUSE_META: dict[str, dict[str, str]] = {
    "sensor_or_evidence_gap_not_marked_unknown": {
        "priority": "high",
        "owner": "risk_rubric_and_data",
        "summary": "근거 결손/센서 충돌을 unknown으로 내리지 못한다.",
        "action": "risk rubric과 targeted sample을 먼저 맞추고 prompt rule은 축소한다.",
    },
    "critical_hazard_undercalled": {
        "priority": "high",
        "owner": "risk_rubric_and_data",
        "summary": "critical hazard를 high/medium/unknown으로 낮게 부른다.",
        "action": "critical 조건을 rubric과 eval notes에 다시 고정한다.",
    },
    "high_risk_case_undercalled": {
        "priority": "medium",
        "owner": "risk_rubric_and_data",
        "summary": "high 케이스를 medium/low로 낮게 부른다.",
        "action": "high vs medium 경계 사례를 추가하고 existing labels를 재점검한다.",
    },
    "watch_case_overescalated": {
        "priority": "medium",
        "owner": "risk_rubric_and_data",
        "summary": "watch/review 케이스를 high/critical로 과상향한다.",
        "action": "damage confirmed 이전 watch 단계 예시를 보강한다.",
    },
    "safe_mode_pair_missing_on_path_or_comms_loss": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "통신·readback loss에서 enter_safe_mode 쌍이 빠진다.",
        "action": "관수/원수/건조실 path loss는 validator가 safe_mode pair를 강제한다.",
    },
    "pause_automation_missing_on_degraded_control_signal": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "degraded control signal에서 pause_automation이 빠진다.",
        "action": "핵심 센서 stale/missing/inconsistent면 자동화 축소를 validator가 강제한다.",
    },
    "block_action_missing_on_safety_lock": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "worker_present/manual_override/safe_mode에서 block_action이 빠진다.",
        "action": "safety lock active면 제어 제안 대신 block_action + create_alert를 강제한다.",
    },
    "alert_missing_on_operator_visible_risk": {
        "priority": "medium",
        "owner": "data_and_model",
        "summary": "현장 가시화가 필요한 리스크인데 create_alert가 빠진다.",
        "action": "operator-visible failure 예시를 추가하고 alert 의무 케이스를 명확히 한다.",
    },
    "human_review_missing_on_uncertain_or_manual_case": {
        "priority": "medium",
        "owner": "data_and_model",
        "summary": "uncertain/manual case인데 request_human_check가 빠진다.",
        "action": "manual review 의무 케이스를 eval과 training에 더 분명히 넣는다.",
    },
    "low_friction_action_bias_over_interlock": {
        "priority": "high",
        "owner": "data_and_model",
        "summary": "create_alert/request_human_check/observe_only에 과도하게 치우친다.",
        "action": "interlock action pair가 필요한 failure/safety slice를 별도 family처럼 보강한다.",
    },
    "unsafe_control_emitted_under_evidence_gap": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "근거 결손 상태인데 short_irrigation/adjust_fertigation 등 unsafe control이 나온다.",
        "action": "evidence gap에서는 unsafe control action을 validator가 차단한다.",
    },
    "robot_task_selection_mismatch": {
        "priority": "medium",
        "owner": "data_and_model",
        "summary": "inspect_crop/skip_area/manual_review 등 올바른 robot task를 고르지 못한다.",
        "action": "robot task type별 contrastive sample을 추가하고 generic task를 금지한다.",
    },
    "robot_task_emitted_under_safety_lock": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "worker/safe-mode/clearance uncertain 상태인데 robot task를 생성한다.",
        "action": "safety lock active면 robot task 생성을 validator가 거부한다.",
    },
    "robot_task_enum_drift": {
        "priority": "medium",
        "owner": "policy_output_validator",
        "summary": "허용되지 않은 generic robot task enum으로 drift한다.",
        "action": "허용 enum 외 task_type은 validator에서 reject한다.",
    },
    "citations_missing_in_actionable_output": {
        "priority": "medium",
        "owner": "output_contract",
        "summary": "actionable output인데 citations가 빠진다.",
        "action": "retrieved_context가 있을 때 citation 미포함 출력을 reject 또는 manual review로 보낸다.",
    },
    "forbidden_robot_task_emitted_under_safety_constraint": {
        "priority": "high",
        "owner": "policy_output_validator",
        "summary": "금지된 robot task가 safety constraint 아래서 그대로 나온다.",
        "action": "forbidden task_type과 safety flag 조합을 validator에서 차단한다.",
    },
    "unclassified_failure": {
        "priority": "medium",
        "owner": "manual_review",
        "summary": "현재 규칙으로 묶이지 않는 실패다.",
        "action": "case-level review 후 root cause taxonomy를 확장한다.",
    },
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


def canonical_risk(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "missing"


def build_eval_index(paths: list[Path]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in load_jsonl(path):
            eval_id = str(row.get("eval_id") or "")
            if eval_id:
                index[eval_id] = row
    return index


def expected_actions(case: dict[str, Any]) -> set[str]:
    expected = case.get("expected", {})
    values = expected.get("required_action_types", [])
    return {str(value) for value in values if isinstance(value, str)}


def forbidden_actions(case: dict[str, Any]) -> set[str]:
    expected = case.get("expected", {})
    values = expected.get("forbidden_action_types", [])
    return {str(value) for value in values if isinstance(value, str)}


def expected_tasks(case: dict[str, Any]) -> set[str]:
    expected = case.get("expected", {})
    values = expected.get("required_task_types", [])
    return {str(value) for value in values if isinstance(value, str)}


def forbidden_tasks(case: dict[str, Any]) -> set[str]:
    expected = case.get("expected", {})
    values = expected.get("forbidden_task_types", [])
    return {str(value) for value in values if isinstance(value, str)}


def actual_output(record: dict[str, Any]) -> dict[str, Any]:
    output = record.get("response", {}).get("parsed_output")
    return output if isinstance(output, dict) else {}


def classify_failure(
    record: dict[str, Any],
    case: dict[str, Any],
) -> tuple[list[str], list[str]]:
    failed_checks = set(str(item) for item in record.get("failed_checks", []))
    optional_failures = set(str(item) for item in record.get("optional_failures", []))
    expected = case.get("expected", {})
    output = actual_output(record)
    action_types = {str(item) for item in record.get("action_types", []) if isinstance(item, str)}
    robot_task_types = {str(item) for item in record.get("robot_task_types", []) if isinstance(item, str)}
    root_causes: list[str] = []
    signatures: list[str] = []

    if "risk_level_match" in failed_checks:
        expected_risk = canonical_risk(expected.get("risk_level"))
        actual_risk = canonical_risk(output.get("risk_level"))
        signatures.append(f"risk_transition:{expected_risk}->{actual_risk}")
        if expected_risk == "unknown" and actual_risk != "unknown":
            root_causes.append("sensor_or_evidence_gap_not_marked_unknown")
        elif expected_risk == "critical" and actual_risk != "critical":
            root_causes.append("critical_hazard_undercalled")
        elif expected_risk == "high" and actual_risk in {"medium", "low", "unknown"}:
            root_causes.append("high_risk_case_undercalled")
        elif expected_risk in {"medium", "unknown"} and actual_risk in {"high", "critical"}:
            root_causes.append("watch_case_overescalated")
        else:
            root_causes.append("unclassified_failure")

    if "required_action_types_present" in failed_checks:
        missing_actions = sorted(expected_actions(case) - action_types)
        for action in missing_actions:
            signatures.append(f"missing_action:{action}")
            if action == "enter_safe_mode":
                root_causes.append("safe_mode_pair_missing_on_path_or_comms_loss")
            elif action == "pause_automation":
                root_causes.append("pause_automation_missing_on_degraded_control_signal")
            elif action == "block_action":
                root_causes.append("block_action_missing_on_safety_lock")
            elif action == "create_alert":
                root_causes.append("alert_missing_on_operator_visible_risk")
            elif action == "request_human_check":
                root_causes.append("human_review_missing_on_uncertain_or_manual_case")
            else:
                root_causes.append("unclassified_failure")
        if missing_actions and action_types.issubset({"create_alert", "request_human_check", "observe_only"}):
            root_causes.append("low_friction_action_bias_over_interlock")

    if "forbidden_action_types_absent" in failed_checks:
        emitted_forbidden = sorted(forbidden_actions(case) & action_types)
        for action in emitted_forbidden:
            signatures.append(f"forbidden_action_emitted:{action}")
            if action in {"short_irrigation", "adjust_fertigation", "adjust_heating", "adjust_co2"}:
                root_causes.append("unsafe_control_emitted_under_evidence_gap")
            elif action == "create_robot_task":
                root_causes.append("robot_task_emitted_under_safety_lock")
            else:
                root_causes.append("unclassified_failure")

    if "required_task_types_present" in failed_checks:
        missing_tasks = sorted(expected_tasks(case) - robot_task_types)
        for task in missing_tasks:
            signatures.append(f"missing_task:{task}")
        root_causes.append("robot_task_selection_mismatch")

    if "forbidden_task_types_absent" in failed_checks:
        emitted_forbidden_tasks = sorted(forbidden_tasks(case) & robot_task_types)
        for task in emitted_forbidden_tasks:
            signatures.append(f"forbidden_task_emitted:{task}")
        root_causes.append("forbidden_robot_task_emitted_under_safety_constraint")

    if "allowed_robot_task_enum_only" in optional_failures:
        root_causes.append("robot_task_enum_drift")

    if "citations_present" in failed_checks:
        signatures.append("citations_missing")
        root_causes.append("citations_missing_in_actionable_output")

    if not root_causes:
        root_causes.append("unclassified_failure")

    return sorted(set(root_causes)), sorted(set(signatures))


def format_case_refs(case_ids: list[str], *, limit: int = 8) -> str:
    if len(case_ids) <= limit:
        return ", ".join(f"`{case_id}`" for case_id in case_ids)
    head = ", ".join(f"`{case_id}`" for case_id in case_ids[:limit])
    return f"{head}, ... (+{len(case_ids) - limit})"


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Eval Failure Clusters",
        "",
        f"- source_report: `{report['source_report']}`",
        f"- total_failed_cases: `{summary['total_failed_cases']}`",
        f"- base_case_count: `{summary['base_case_count']}`",
        f"- new_tranche_failed_cases: `{summary['new_tranche_failed_cases']}`",
        f"- validator_priority_failed_cases: `{summary['validator_priority_failed_cases']}`",
        "",
        "## Root Cause Summary",
        "",
        "| root_cause | cases | priority | owner | summary |",
        "|---|---:|---|---|---|",
    ]

    for item in report["root_causes"]:
        lines.append(
            f"| {item['name']} | {item['count']} | {item['priority']} | {item['owner']} | {item['summary']} |"
        )

    lines.extend(["", "## New Tranche Root Causes", ""])
    if report["new_tranche_root_causes"]:
        for item in report["new_tranche_root_causes"]:
            lines.append(
                f"- `{item['name']}` `{item['count']}`: {format_case_refs(item['case_ids'])}"
            )
    else:
        lines.append("- 없음")

    lines.extend(["", "## Atomic Failure Signatures", ""])
    if report["top_signatures"]:
        for item in report["top_signatures"]:
            lines.append(f"- `{item['name']}`: `{item['count']}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Externalize Now", ""])
    if report["validator_priority_root_causes"]:
        for item in report["validator_priority_root_causes"]:
            lines.append(
                f"- `{item['name']}` `{item['count']}`: {item['action']} "
                f"cases={format_case_refs(item['case_ids'])}"
            )
    else:
        lines.append("- 없음")

    lines.extend(["", "## Root Cause Case Map", ""])
    for item in report["root_causes"]:
        lines.append(
            f"- `{item['name']}`: {format_case_refs(item['case_ids'])}"
        )

    return "\n".join(lines) + "\n"


def build_output(
    *,
    report_path: Path,
    eval_index: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    base_case_count: int,
) -> dict[str, Any]:
    failed_records = [record for record in records if not record.get("passed")]
    root_to_cases: dict[str, list[str]] = defaultdict(list)
    root_to_new_cases: dict[str, list[str]] = defaultdict(list)
    signature_counter: Counter[str] = Counter()
    validator_priority_cases: set[str] = set()

    details: list[dict[str, Any]] = []

    for record in failed_records:
        eval_id = str(record.get("eval_id") or "")
        case = eval_index.get(eval_id, {})
        root_causes, signatures = classify_failure(record, case)
        prompt_index = int(record.get("prompt_index") or 0)
        is_new_tranche = base_case_count > 0 and prompt_index > base_case_count

        for root_cause in root_causes:
            root_to_cases[root_cause].append(eval_id)
            if is_new_tranche:
                root_to_new_cases[root_cause].append(eval_id)
            if ROOT_CAUSE_META.get(root_cause, {}).get("owner") == "policy_output_validator":
                validator_priority_cases.add(eval_id)
        signature_counter.update(signatures)

        details.append(
            {
                "eval_id": eval_id,
                "category": record.get("category"),
                "task_type": record.get("task_type"),
                "prompt_index": prompt_index,
                "failed_checks": record.get("failed_checks", []),
                "root_causes": root_causes,
                "signatures": signatures,
                "expected": case.get("expected", {}),
                "grading_notes": case.get("grading_notes"),
            }
        )

    def build_root_rows(source: dict[str, list[str]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for name, case_ids in source.items():
            meta = ROOT_CAUSE_META.get(name, ROOT_CAUSE_META["unclassified_failure"])
            rows.append(
                {
                    "name": name,
                    "count": len(case_ids),
                    "case_ids": sorted(case_ids),
                    "priority": meta["priority"],
                    "owner": meta["owner"],
                    "summary": meta["summary"],
                    "action": meta["action"],
                }
            )
        rows.sort(key=lambda row: (-row["count"], row["name"]))
        return rows

    root_rows = build_root_rows(root_to_cases)
    new_tranche_rows = build_root_rows(root_to_new_cases)
    validator_priority_rows = [
        row for row in root_rows if row["owner"] == "policy_output_validator"
    ]
    top_signatures = [
        {"name": name, "count": count}
        for name, count in signature_counter.most_common(20)
    ]

    return {
        "schema_version": "eval_failure_clusters.v1",
        "source_report": report_path.as_posix(),
        "summary": {
            "total_failed_cases": len(failed_records),
            "base_case_count": base_case_count,
            "new_tranche_failed_cases": sum(
                1 for record in failed_records if base_case_count > 0 and int(record.get("prompt_index") or 0) > base_case_count
            ),
            "validator_priority_failed_cases": len(validator_priority_cases),
        },
        "root_causes": root_rows,
        "new_tranche_root_causes": new_tranche_rows,
        "validator_priority_root_causes": validator_priority_rows,
        "top_signatures": top_signatures,
        "failed_case_details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="Evaluation summary JSON report path.")
    parser.add_argument(
        "--eval-files",
        nargs="*",
        help="Eval JSONL files used to build the report. Defaults to eval_files embedded in the report.",
    )
    parser.add_argument(
        "--output-prefix",
        default="artifacts/reports/eval_failure_clusters_latest",
        help="Output prefix for JSON and Markdown cluster reports.",
    )
    parser.add_argument(
        "--base-case-count",
        type=int,
        default=0,
        help="Number of base benchmark cases before the newest tranche starts.",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    report = load_json(report_path)

    eval_files = args.eval_files
    if not eval_files:
        raw_paths = report.get("eval_files", [])
        if not isinstance(raw_paths, list) or not raw_paths:
            raise SystemExit("No eval files provided and report does not embed eval_files.")
        eval_files = [str(item) for item in raw_paths]

    eval_index = build_eval_index([Path(path) for path in eval_files])
    records = report.get("cases", [])
    if not isinstance(records, list):
        raise SystemExit("Report does not contain a valid cases list.")

    output = build_output(
        report_path=report_path,
        eval_index=eval_index,
        records=records,
        base_case_count=args.base_case_count,
    )

    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(output), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
