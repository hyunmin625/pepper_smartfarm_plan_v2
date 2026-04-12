#!/usr/bin/env python3
"""Summarize residual disagreements from a shadow-mode seed audit log."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CAUSE_TO_OWNER = {
    "alert_missing_before_fertigation_review": "data_and_model",
    "inspect_crop_enum_drift": "robot_contract_and_model",
    "other_shadow_disagreement": "manual_review",
}

NEXT_ACTION_BY_OWNER = {
    "data_and_model": "create_alert + request_human_check 우선 패턴과 adjust_fertigation reflex 차단 slice를 training batch로 다시 넣는다.",
    "robot_contract_and_model": "low-confidence hotspot에서 inspect_crop exact enum과 candidate_id/target 계약을 더 강하게 고정한다.",
    "manual_review": "runtime shadow raw row를 사람이 다시 읽고 rubric/data/validator ownership을 수동 분류한다.",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(item)
    return rows


def infer_cause(row: dict[str, Any]) -> str:
    task_type = str(row.get("task_type") or "")
    ai_actions = set(str(item) for item in row.get("ai_action_types_after", []) if isinstance(item, str))
    operator_actions = set(str(item) for item in row.get("operator_action_types", []) if isinstance(item, str))
    ai_robot = set(str(item) for item in row.get("ai_robot_task_types_after", []) if isinstance(item, str))
    operator_robot = set(str(item) for item in row.get("operator_robot_task_types", []) if isinstance(item, str))

    if task_type in {"action_recommendation", "nutrient_risk", "rootzone_diagnosis"}:
        if "adjust_fertigation" in ai_actions and "create_alert" in operator_actions and "create_alert" not in ai_actions:
            return "alert_missing_before_fertigation_review"

    if task_type == "robot_task_prioritization":
        if "inspect_crop" in operator_robot and "inspect_crop" not in ai_robot:
            return "inspect_crop_enum_drift"

    return "other_shadow_disagreement"


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    disagreements = [row for row in rows if row.get("operator_agreement") is False]
    cause_counter: Counter[str] = Counter()
    owner_counter: Counter[str] = Counter()
    task_counter: Counter[str] = Counter()
    cases_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    case_rows: list[dict[str, Any]] = []

    for row in disagreements:
        request_id = str(row.get("request_id") or "unknown")
        task_type = str(row.get("task_type") or "unknown")
        cause = infer_cause(row)
        owner = CAUSE_TO_OWNER.get(cause, "manual_review")
        cause_counter[cause] += 1
        owner_counter[owner] += 1
        task_counter[task_type] += 1

        case_payload = {
            "request_id": request_id,
            "task_type": task_type,
            "cause": cause,
            "owner": owner,
            "ai_action_types_after": row.get("ai_action_types_after", []),
            "operator_action_types": row.get("operator_action_types", []),
            "ai_robot_task_types_after": row.get("ai_robot_task_types_after", []),
            "operator_robot_task_types": row.get("operator_robot_task_types", []),
            "validator_reason_codes": row.get("validator_reason_codes", []),
        }
        case_rows.append(case_payload)
        cases_by_owner[owner].append(case_payload)

    return {
        "schema_version": "shadow_seed_residual_report.v1",
        "decision_count": len(rows),
        "residual_case_count": len(disagreements),
        "remaining_by_owner": [
            {
                "owner": owner,
                "cases": count,
                "next_action": NEXT_ACTION_BY_OWNER.get(owner, "manual review"),
            }
            for owner, count in owner_counter.most_common()
        ],
        "remaining_by_cause": cause_counter.most_common(),
        "remaining_by_task_type": task_counter.most_common(),
        "remaining_cases": sorted(case_rows, key=lambda item: (item["task_type"], item["request_id"])),
        "owner_case_map": {owner: cases_by_owner[owner] for owner in sorted(cases_by_owner)},
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Shadow Seed Residuals",
        "",
        f"- decision_count: `{summary['decision_count']}`",
        f"- residual_case_count: `{summary['residual_case_count']}`",
        "",
        "## Remaining By Owner",
        "",
        "| owner | cases | next_action |",
        "|---|---:|---|",
    ]
    for item in summary["remaining_by_owner"]:
        lines.append(f"| `{item['owner']}` | {item['cases']} | {item['next_action']} |")

    lines.extend(["", "## Remaining By Cause", ""])
    for name, count in summary["remaining_by_cause"]:
        lines.append(f"- `{name}`: `{count}`")

    lines.extend(["", "## Remaining Cases", ""])
    for item in summary["remaining_cases"]:
        lines.append(
            f"- `{item['request_id']}` `{item['task_type']}` cause=`{item['cause']}` owner=`{item['owner']}` "
            f"ai={item['ai_action_types_after'] or item['ai_robot_task_types_after']} "
            f"operator={item['operator_action_types'] or item['operator_robot_task_types']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-log", required=True)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()

    rows = load_jsonl(Path(args.audit_log))
    summary = build_summary(rows)
    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_prefix.with_suffix(".md").write_text(render_markdown(summary), encoding="utf-8")

    print(f"summary_json: {output_prefix.with_suffix('.json')}")
    print(f"summary_md: {output_prefix.with_suffix('.md')}")
    print(f"residual_case_count: {summary['residual_case_count']}")
    print(f"remaining_by_owner: {summary['remaining_by_owner']}")


if __name__ == "__main__":
    main()
