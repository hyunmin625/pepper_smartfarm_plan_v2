#!/usr/bin/env python3
"""Validate runtime policy output validator behavior with sample cases."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from policy_engine.output_validator import ValidatorContext, apply_output_validator, load_rule_catalog  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    rule_catalog = load_rule_catalog()
    rows = load_jsonl(REPO_ROOT / "data/examples/policy_output_validator_cases.jsonl")
    errors: list[str] = []
    summary_rows: list[dict[str, object]] = []

    for row in rows:
        case_id = row["case_id"]
        context = ValidatorContext.from_dict(row["context"])
        result = apply_output_validator(row["output"], context, rule_catalog=rule_catalog)
        expected = row["expected"]
        action_types = [
            action.get("action_type")
            for action in result.output.get("recommended_actions", [])
            if isinstance(action, dict)
        ]
        robot_task_types = [
            task.get("task_type")
            for task in result.output.get("robot_tasks", [])
            if isinstance(task, dict)
        ]

        if "risk_level" in expected and result.output.get("risk_level") != expected["risk_level"]:
            errors.append(f"{case_id}: expected risk_level={expected['risk_level']} got {result.output.get('risk_level')}")
        if "decision" in expected and result.output.get("decision") != expected["decision"]:
            errors.append(f"{case_id}: expected decision={expected['decision']} got {result.output.get('decision')}")
        if "blocked_action_type" in expected and result.output.get("blocked_action_type") != expected["blocked_action_type"]:
            errors.append(
                f"{case_id}: expected blocked_action_type={expected['blocked_action_type']} got {result.output.get('blocked_action_type')}"
            )
        for action_type in expected.get("required_action_types", []):
            if action_type not in action_types:
                errors.append(f"{case_id}: missing required action_type={action_type}")
        for action_type in expected.get("forbidden_action_types", []):
            if action_type in action_types:
                errors.append(f"{case_id}: forbidden action_type still present={action_type}")
        if "robot_task_count" in expected and len(robot_task_types) != expected["robot_task_count"]:
            errors.append(f"{case_id}: expected robot_task_count={expected['robot_task_count']} got {len(robot_task_types)}")
        for task_type in expected.get("robot_task_types", []):
            if task_type not in robot_task_types:
                errors.append(f"{case_id}: missing robot_task_type={task_type}")
        if expected.get("requires_citations") and not result.output.get("citations"):
            errors.append(f"{case_id}: citations were not added")
        required_citation_chunk_ids = expected.get("required_citation_chunk_ids", [])
        if isinstance(required_citation_chunk_ids, list) and required_citation_chunk_ids:
            output_citation_ids = {
                str(citation.get("chunk_id"))
                for citation in result.output.get("citations", [])
                if isinstance(citation, dict) and citation.get("chunk_id")
            }
            for chunk_id in required_citation_chunk_ids:
                if chunk_id not in output_citation_ids:
                    errors.append(f"{case_id}: missing required citation chunk_id={chunk_id}")
        if expected.get("follow_up_count_min", 0) > len(result.output.get("follow_up", [])):
            errors.append(f"{case_id}: expected follow_up_count_min={expected['follow_up_count_min']}")
        if expected.get("required_follow_up_count_min", 0) > len(result.output.get("required_follow_up", [])):
            errors.append(
                f"{case_id}: expected required_follow_up_count_min={expected['required_follow_up_count_min']}"
            )
        for action in result.output.get("recommended_actions", []):
            if not isinstance(action, dict):
                continue
            if action.get("action_type") in expected.get("approval_required_action_types", []) and action.get("approval_required") is not True:
                errors.append(f"{case_id}: {action.get('action_type')} was not escalated to approval_required")
        for rule_id in expected.get("required_rule_ids", []):
            if rule_id not in result.applied_rules:
                errors.append(f"{case_id}: missing rule_id={rule_id}")

        summary_rows.append(
            {
                "case_id": case_id,
                "decision": result.decision,
                "output_decision": result.output.get("decision"),
                "blocked_action_type": result.output.get("blocked_action_type"),
                "risk_level": result.output.get("risk_level"),
                "action_types": action_types,
                "robot_task_types": robot_task_types,
                "applied_rules": result.applied_rules,
            }
        )

    print(json.dumps({"checked_cases": len(rows), "errors": errors, "cases": summary_rows}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
