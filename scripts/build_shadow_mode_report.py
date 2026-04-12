#!/usr/bin/env python3
"""Build a shadow-mode summary report from validator shadow audit rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


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


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("shadow audit rows are empty")

    first = rows[0]
    growth_stage_counter = Counter(str(row.get("growth_stage") or "unknown") for row in rows)
    operator_mismatch_rows = [row for row in rows if row.get("operator_agreement") is False]
    critical_disagreement_rows = [row for row in rows if row.get("critical_disagreement") is True]
    citation_required_rows = [row for row in rows if row.get("citation_required") is True]
    citation_present_rows = [row for row in citation_required_rows if row.get("citation_present") is True]
    schema_pass_rows = [row for row in rows if row.get("schema_pass") is True]
    retrieval_hit_rows = [row for row in rows if row.get("retrieval_hit") is True]

    blocked_action_recommendation_count = sum(
        int(row.get("blocked_action_recommendation_count") or 0) for row in rows
    )
    approval_missing_count = sum(int(row.get("approval_missing_count") or 0) for row in rows)
    manual_override_count = sum(1 for row in rows if row.get("manual_override_used") is True)
    policy_mismatch_count = sum(1 for row in rows if row.get("validator_decision") != "pass")

    operator_agreement_rate = safe_ratio(
        sum(1 for row in rows if row.get("operator_agreement") is True),
        len(rows),
    )
    citation_coverage = safe_ratio(len(citation_present_rows), len(citation_required_rows))
    schema_pass_rate = safe_ratio(len(schema_pass_rows), len(rows))
    retrieval_hit_rate = safe_ratio(len(retrieval_hit_rows), len(rows))
    manual_override_rate = safe_ratio(manual_override_count, len(rows))

    if critical_disagreement_rows:
        promotion_decision = "rollback"
    elif operator_agreement_rate < 0.9 or citation_coverage < 0.95:
        promotion_decision = "hold"
    else:
        promotion_decision = "promote"

    top_disagreements = sorted(
        operator_mismatch_rows,
        key=lambda row: (
            row.get("critical_disagreement") is not True,
            row.get("task_type") or "",
            row.get("request_id") or "",
        ),
    )[:10]

    return {
        "report_id": f"shadow-{first.get('model_id', 'unknown-model')}",
        "model_id": first.get("model_id"),
        "prompt_id": first.get("prompt_id"),
        "dataset_id": first.get("dataset_id"),
        "eval_set_id": first.get("eval_set_id"),
        "retrieval_profile_id": first.get("retrieval_profile_id"),
        "decision_count": len(rows),
        "zone_count": len({str(row.get('zone_id') or 'unknown-zone') for row in rows}),
        "growth_stage_distribution": sorted(growth_stage_counter.items()),
        "schema_pass_rate": schema_pass_rate,
        "citation_coverage": citation_coverage,
        "retrieval_hit_rate": retrieval_hit_rate,
        "operator_agreement_rate": operator_agreement_rate,
        "critical_disagreement_count": len(critical_disagreement_rows),
        "manual_override_rate": manual_override_rate,
        "blocked_action_recommendation_count": blocked_action_recommendation_count,
        "approval_missing_count": approval_missing_count,
        "policy_mismatch_count": policy_mismatch_count,
        "promotion_decision": promotion_decision,
        "top_disagreements": [
            {
                "request_id": row.get("request_id"),
                "task_type": row.get("task_type"),
                "zone_id": row.get("zone_id"),
                "critical_disagreement": bool(row.get("critical_disagreement")),
                "ai_action_types_after": row.get("ai_action_types_after", []),
                "ai_decision_after": row.get("ai_decision_after"),
                "ai_blocked_action_type_after": row.get("ai_blocked_action_type_after"),
                "operator_action_types": row.get("operator_action_types", []),
                "operator_decision": row.get("operator_decision"),
                "operator_blocked_action_type": row.get("operator_blocked_action_type"),
                "validator_reason_codes": row.get("validator_reason_codes", []),
            }
            for row in top_disagreements
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Shadow Mode Summary",
        "",
        "## 실행 메타데이터",
        "",
        f"- model_id: `{summary['model_id']}`",
        f"- prompt_id: `{summary['prompt_id']}`",
        f"- dataset_id: `{summary['dataset_id']}`",
        f"- eval_set_id: `{summary['eval_set_id']}`",
        f"- retrieval_profile_id: `{summary['retrieval_profile_id']}`",
        "",
        "## 커버리지",
        "",
        f"- decision_count: `{summary['decision_count']}`",
        f"- zone_count: `{summary['zone_count']}`",
        f"- growth_stage_distribution: `{summary['growth_stage_distribution']}`",
        "",
        "## 안전성",
        "",
        f"- blocked_action_recommendation_count: `{summary['blocked_action_recommendation_count']}`",
        f"- approval_missing_count: `{summary['approval_missing_count']}`",
        f"- policy_mismatch_count: `{summary['policy_mismatch_count']}`",
        f"- critical_disagreement_count: `{summary['critical_disagreement_count']}`",
        f"- manual_override_rate: `{summary['manual_override_rate']}`",
        "",
        "## 검색 품질",
        "",
        f"- schema_pass_rate: `{summary['schema_pass_rate']}`",
        f"- citation_coverage: `{summary['citation_coverage']}`",
        f"- retrieval_hit_rate: `{summary['retrieval_hit_rate']}`",
        "",
        "## 운영자 불일치",
        "",
        f"- operator_agreement_rate: `{summary['operator_agreement_rate']}`",
    ]

    if summary["top_disagreements"]:
        for item in summary["top_disagreements"]:
            decision_suffix = ""
            if item.get("ai_decision_after") or item.get("operator_decision"):
                decision_suffix = (
                    f" ai_decision={item.get('ai_decision_after')}"
                    f" operator_decision={item.get('operator_decision')}"
                )
            blocked_suffix = ""
            if item.get("ai_blocked_action_type_after") or item.get("operator_blocked_action_type"):
                blocked_suffix = (
                    f" ai_blocked={item.get('ai_blocked_action_type_after')}"
                    f" operator_blocked={item.get('operator_blocked_action_type')}"
                )
            lines.append(
                f"- `{item['request_id']}` `{item['task_type']}` critical={item['critical_disagreement']}"
                f" ai={item['ai_action_types_after']} operator={item['operator_action_types']}"
                f"{decision_suffix}{blocked_suffix} validator={item['validator_reason_codes']}"
            )
    else:
        lines.append("- 없음")

    lines.extend(
        [
            "",
            "## 승격 판단",
            "",
            f"- promotion_decision: `{summary['promotion_decision']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audit-log",
        default="artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl",
        help="Shadow-mode audit JSONL from llm_orchestrator.runtime",
    )
    parser.add_argument(
        "--output-prefix",
        default="artifacts/reports/shadow_mode_latest",
        help="Output prefix for shadow-mode summary JSON/MD",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.audit_log))
    summary = build_summary(rows)

    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path = output_prefix.with_suffix(".json")
    summary_md_path = output_prefix.with_suffix(".md")
    summary_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_md_path.write_text(render_markdown(summary), encoding="utf-8")

    print(f"audit_log: {args.audit_log}")
    print(f"summary_json: {summary_json_path}")
    print(f"summary_md: {summary_md_path}")
    print(f"decision_count: {summary['decision_count']}")
    print(f"operator_agreement_rate: {summary['operator_agreement_rate']}")
    print(f"critical_disagreement_count: {summary['critical_disagreement_count']}")
    print(f"promotion_decision: {summary['promotion_decision']}")


if __name__ == "__main__":
    main()
