#!/usr/bin/env python3
"""Summarize residual failures that remain after validator simulation."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OWNER_BY_CHECK = {
    "risk_level_match": "risk_rubric_and_data",
    "required_action_types_present": "data_and_model",
    "required_task_types_present": "robot_contract_and_model",
    "citations_present": "output_contract_and_retrieval",
    "forbidden_action_types_absent": "data_and_model",
    "decision_match": "risk_rubric_and_data",
    "allowed_robot_task_enum_only": "robot_contract_and_model",
}

NEXT_ACTION_BY_OWNER = {
    "risk_rubric_and_data": "risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다.",
    "data_and_model": "required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다.",
    "robot_contract_and_model": "robot task target/enum/selection slice를 별도 계약형 batch로 보강한다.",
    "output_contract_and_retrieval": "citation/follow_up/retrieval coverage contract를 runtime/output 계층에서 더 강하게 검사한다.",
    "runtime_validator_gap": "현재 validator rule catalog에 없는 invariant를 runtime rule로 추가한다.",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object")
    return payload


def case_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = report.get("cases", [])
    if not isinstance(rows, list):
        raise ValueError("report.cases must be a list")
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            eval_id = str(row.get("eval_id") or "")
            if eval_id:
                index[eval_id] = row
    return index


def check_names(case: dict[str, Any]) -> list[str]:
    failed = []
    for item in case.get("failed_checks", []):
        if isinstance(item, str):
            failed.append(item)
    for item in case.get("optional_failures", []):
        if isinstance(item, str):
            failed.append(item)
    return failed


def build_summary(
    raw_report: dict[str, Any],
    validator_report: dict[str, Any],
    gate_report: dict[str, Any] | None,
) -> dict[str, Any]:
    raw_cases = case_index(raw_report)
    validator_cases = case_index(validator_report)

    runtime_gap_ids = {
        str(item.get("eval_id"))
        for item in gate_report.get("gate_summary", {}).get("failed_invariants", [])
    } if gate_report else set()

    owner_counter: Counter[str] = Counter()
    check_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    cases_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    recovered_cases = 0

    remaining_cases: list[dict[str, Any]] = []
    for eval_id, validator_case in validator_cases.items():
        if validator_case.get("passed") is True:
            if raw_cases.get(eval_id, {}).get("passed") is False:
                recovered_cases += 1
            continue

        failed_checks = check_names(validator_case)
        owners: set[str] = set()
        if eval_id in runtime_gap_ids:
            owners.add("runtime_validator_gap")
        for check in failed_checks:
            owners.add(OWNER_BY_CHECK.get(check, "data_and_model"))
            check_counter[check] += 1
        category = str(validator_case.get("category") or validator_case.get("task_type") or "unknown")
        category_counter[category] += 1

        case_payload = {
            "eval_id": eval_id,
            "category": category,
            "failed_checks": sorted(set(failed_checks)),
            "owners": sorted(owners),
        }
        remaining_cases.append(case_payload)
        for owner in owners:
            owner_counter[owner] += 1
            cases_by_owner[owner].append(case_payload)

    return {
        "schema_version": "validator_residual_report.v1",
        "model": validator_report.get("model"),
        "source_raw_report": raw_report.get("source_report", ""),
        "source_validator_report": validator_report.get("source_report", validator_report.get("evaluated_at")),
        "total_cases": validator_report.get("summary", {}).get("total_cases"),
        "raw_pass_rate": raw_report.get("summary", {}).get("pass_rate"),
        "validator_pass_rate": validator_report.get("summary", {}).get("pass_rate"),
        "recovered_cases": recovered_cases,
        "remaining_failed_cases": len(remaining_cases),
        "runtime_validator_gap_cases": len(runtime_gap_ids),
        "top_remaining_checks": check_counter.most_common(),
        "remaining_by_category": category_counter.most_common(),
        "remaining_by_owner": [
            {
                "owner": owner,
                "cases": count,
                "next_action": NEXT_ACTION_BY_OWNER.get(owner, "manual review"),
            }
            for owner, count in owner_counter.most_common()
        ],
        "remaining_cases": sorted(remaining_cases, key=lambda item: (item["category"], item["eval_id"])),
        "owner_case_map": {
            owner: cases_by_owner[owner]
            for owner in sorted(cases_by_owner)
        },
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Validator Residual Failures",
        "",
        f"- model: `{summary['model']}`",
        f"- raw_pass_rate: `{summary['raw_pass_rate']}`",
        f"- validator_pass_rate: `{summary['validator_pass_rate']}`",
        f"- recovered_cases: `{summary['recovered_cases']}`",
        f"- remaining_failed_cases: `{summary['remaining_failed_cases']}`",
        f"- runtime_validator_gap_cases: `{summary['runtime_validator_gap_cases']}`",
        "",
        "## Remaining By Owner",
        "",
        "| owner | cases | next_action |",
        "|---|---:|---|",
    ]
    for item in summary["remaining_by_owner"]:
        lines.append(f"| `{item['owner']}` | {item['cases']} | {item['next_action']} |")

    lines.extend(["", "## Top Remaining Checks", ""])
    for name, count in summary["top_remaining_checks"]:
        lines.append(f"- `{name}`: `{count}`")

    lines.extend(["", "## Remaining By Category", ""])
    for name, count in summary["remaining_by_category"]:
        lines.append(f"- `{name}`: `{count}`")

    lines.extend(["", "## Remaining Cases", ""])
    for item in summary["remaining_cases"]:
        lines.append(
            f"- `{item['eval_id']}` `{item['category']}` owners={item['owners']} failed={item['failed_checks']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-report", required=True)
    parser.add_argument("--validator-report", required=True)
    parser.add_argument("--gate-report")
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()

    raw_report = load_json(Path(args.raw_report))
    validator_report = load_json(Path(args.validator_report))
    gate_report = load_json(Path(args.gate_report)) if args.gate_report else None
    summary = build_summary(raw_report, validator_report, gate_report)

    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_prefix.with_suffix(".md").write_text(render_markdown(summary), encoding="utf-8")

    print(f"summary_json: {output_prefix.with_suffix('.json')}")
    print(f"summary_md: {output_prefix.with_suffix('.md')}")
    print(f"remaining_failed_cases: {summary['remaining_failed_cases']}")
    print(f"remaining_by_owner: {summary['remaining_by_owner']}")


if __name__ == "__main__":
    main()
