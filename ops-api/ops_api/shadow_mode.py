from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from llm_orchestrator.runtime import (
    LLMDecisionEnvelope,
    ShadowModeMetadata,
    ShadowModeObservedOutcome,
    run_shadow_mode_capture,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
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


def build_window_summary(rows: list[dict[str, Any]], audit_logs: list[str]) -> dict[str, Any]:
    if not rows:
        raise ValueError("shadow audit rows are empty")

    first = rows[0]
    operator_mismatch_rows = [row for row in rows if row.get("operator_agreement") is False]
    critical_disagreement_rows = [row for row in rows if row.get("critical_disagreement") is True]
    citation_required_rows = [row for row in rows if row.get("citation_required") is True]
    citation_present_rows = [row for row in citation_required_rows if row.get("citation_present") is True]
    schema_pass_rows = [row for row in rows if row.get("schema_pass") is True]
    retrieval_hit_rows = [row for row in rows if row.get("retrieval_hit") is True]

    created_at_values = [str(row.get("created_at") or "") for row in rows if row.get("created_at")]
    eval_set_ids = sorted({str(row.get("eval_set_id") or "unknown") for row in rows})
    zone_ids = sorted({str(row.get("zone_id") or "unknown") for row in rows})
    growth_stage_distribution: dict[str, int] = {}
    for row in rows:
        growth_stage = str(row.get("growth_stage") or "unknown")
        growth_stage_distribution[growth_stage] = growth_stage_distribution.get(growth_stage, 0) + 1

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

    top_disagreements = operator_mismatch_rows[:10]

    return {
        "report_id": f"shadow-window-{first.get('model_id', 'unknown-model')}",
        "model_id": first.get("model_id"),
        "prompt_id": first.get("prompt_id"),
        "dataset_id": first.get("dataset_id"),
        "retrieval_profile_id": first.get("retrieval_profile_id"),
        "audit_logs": audit_logs,
        "eval_set_ids": eval_set_ids,
        "decision_count": len(rows),
        "zone_count": len(zone_ids),
        "zones": zone_ids,
        "window_start": min(created_at_values) if created_at_values else None,
        "window_end": max(created_at_values) if created_at_values else None,
        "schema_pass_rate": schema_pass_rate,
        "citation_coverage": citation_coverage,
        "retrieval_hit_rate": retrieval_hit_rate,
        "operator_agreement_rate": operator_agreement_rate,
        "critical_disagreement_count": len(critical_disagreement_rows),
        "manual_override_rate": manual_override_rate,
        "blocked_action_recommendation_count": blocked_action_recommendation_count,
        "approval_missing_count": approval_missing_count,
        "policy_mismatch_count": policy_mismatch_count,
        "growth_stage_distribution": sorted(growth_stage_distribution.items()),
        "promotion_decision": promotion_decision,
        "top_disagreements": [
            {
                "request_id": row.get("request_id"),
                "task_type": row.get("task_type"),
                "eval_set_id": row.get("eval_set_id"),
                "critical_disagreement": bool(row.get("critical_disagreement")),
                "ai_action_types_after": row.get("ai_action_types_after", []),
                "ai_robot_task_types_after": row.get("ai_robot_task_types_after", []),
                "operator_action_types": row.get("operator_action_types", []),
                "operator_robot_task_types": row.get("operator_robot_task_types", []),
                "validator_reason_codes": row.get("validator_reason_codes", []),
            }
            for row in top_disagreements
        ],
    }


def build_window_summary_from_paths(audit_logs: list[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for audit_log in audit_logs:
        rows.extend(load_jsonl(audit_log))
    return build_window_summary(rows, [path.as_posix() for path in audit_logs])


def capture_shadow_cases(
    cases: list[dict[str, Any]],
    *,
    shadow_audit_log_path: Path,
    validator_audit_log_path: Path,
    append: bool = True,
) -> dict[str, Any]:
    shadow_audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    validator_audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    if not append:
        if shadow_audit_log_path.exists():
            shadow_audit_log_path.unlink()
        if validator_audit_log_path.exists():
            validator_audit_log_path.unlink()

    os.environ["LLM_OUTPUT_VALIDATOR_SHADOW_LOG_PATH"] = str(shadow_audit_log_path)
    os.environ["LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH"] = str(validator_audit_log_path)

    for case in cases:
        run_shadow_mode_capture(
            LLMDecisionEnvelope.from_dict(case),
            ShadowModeMetadata.from_dict(case["metadata"]),
            ShadowModeObservedOutcome.from_dict(case["observed"]),
        )

    return build_window_summary_from_paths([shadow_audit_log_path])
