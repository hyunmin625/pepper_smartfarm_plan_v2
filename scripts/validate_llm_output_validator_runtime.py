#!/usr/bin/env python3
"""Validate llm-orchestrator runtime wiring for output validator audit logging."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator.runtime import LLMDecisionEnvelope, run_output_validator  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    rows = load_jsonl(REPO_ROOT / "data/examples/llm_output_validator_runtime_cases.jsonl")
    errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="llm-output-validator-") as tmp_dir:
        audit_path = Path(tmp_dir) / "output_validator_audit.jsonl"
        os.environ["LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH"] = str(audit_path)

        first_output, first_audit, _ = run_output_validator(LLMDecisionEnvelope.from_dict(rows[0]))
        second_output, second_audit, _ = run_output_validator(LLMDecisionEnvelope.from_dict(rows[1]))
        audit_rows = load_jsonl(audit_path)

        first_actions = [action.get("action_type") for action in first_output.get("recommended_actions", []) if isinstance(action, dict)]
        second_actions = [action.get("action_type") for action in second_output.get("recommended_actions", []) if isinstance(action, dict)]

        if first_output.get("risk_level") != "high":
            errors.append("runtime-001 should keep risk_level high for climate degraded case")
        if "pause_automation" not in first_actions or "request_human_check" not in first_actions:
            errors.append("runtime-001 should force pause_automation + request_human_check")
        if second_output.get("risk_level") != "unknown":
            errors.append("runtime-002 should downgrade to unknown for rootzone evidence collapse")
        if "short_irrigation" in second_actions:
            errors.append("runtime-002 should strip short_irrigation")
        if "pause_automation" not in second_actions or "request_human_check" not in second_actions:
            errors.append("runtime-002 should force pause_automation + request_human_check")
        if len(audit_rows) != 2:
            errors.append(f"expected 2 audit rows, found {len(audit_rows)}")
        if first_audit.validator_decision != "rewritten":
            errors.append("runtime-001 audit should record rewritten decision")
        if second_audit.validator_decision != "rewritten":
            errors.append("runtime-002 audit should record rewritten decision")

        print(
            json.dumps(
                {
                    "checked_cases": len(rows),
                    "audit_rows": len(audit_rows),
                    "errors": errors,
                    "cases": [
                        {
                            "request_id": first_audit.request_id,
                            "validator_reason_codes": first_audit.validator_reason_codes,
                            "action_types_after": first_audit.action_types_after,
                        },
                        {
                            "request_id": second_audit.request_id,
                            "validator_reason_codes": second_audit.validator_reason_codes,
                            "action_types_after": second_audit.action_types_after,
                        },
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
