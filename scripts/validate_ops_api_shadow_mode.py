#!/usr/bin/env python3
"""Validate ops-api shadow capture and window summary helpers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from ops_api.shadow_mode import build_window_summary_from_paths, capture_shadow_cases  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ops-api-shadow-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        shadow_path = tmp_path / "shadow.jsonl"
        validator_path = tmp_path / "validator.jsonl"
        cases = load_jsonl(REPO_ROOT / "data/examples/shadow_mode_runtime_day0_seed_cases.jsonl")[:4]
        summary = capture_shadow_cases(
            cases,
            shadow_audit_log_path=shadow_path,
            validator_audit_log_path=validator_path,
            append=False,
        )
        if summary["decision_count"] != len(cases):
            errors.append("decision_count should match captured case count")
        if not shadow_path.exists():
            errors.append("shadow audit log should be written")
        if not validator_path.exists():
            errors.append("validator audit log should be written")
        rebuilt = build_window_summary_from_paths([shadow_path])
        if rebuilt["decision_count"] != len(cases):
            errors.append("rebuilt summary should match captured case count")
        if rebuilt["operator_agreement_rate"] != summary["operator_agreement_rate"]:
            errors.append("rebuilt summary should preserve operator_agreement_rate")

        print(
            json.dumps(
                {
                    "errors": errors,
                    "decision_count": summary["decision_count"],
                    "operator_agreement_rate": summary["operator_agreement_rate"],
                    "critical_disagreement_count": summary["critical_disagreement_count"],
                    "promotion_decision": summary["promotion_decision"],
                    "shadow_audit_log": str(shadow_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
