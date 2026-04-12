#!/usr/bin/env python3
"""Validate shadow-mode capture and report generation from llm-orchestrator runtime."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator.runtime import (  # noqa: E402
    LLMDecisionEnvelope,
    ShadowModeMetadata,
    ShadowModeObservedOutcome,
    run_shadow_mode_capture,
)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    rows = load_jsonl(REPO_ROOT / "data/examples/shadow_mode_runtime_cases.jsonl")
    errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="shadow-mode-runtime-") as tmp_dir:
        output_validator_path = Path(tmp_dir) / "output_validator_audit.jsonl"
        shadow_audit_path = Path(tmp_dir) / "shadow_mode_audit.jsonl"
        report_prefix = Path(tmp_dir) / "shadow_mode_summary"
        os.environ["LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH"] = str(output_validator_path)
        os.environ["LLM_OUTPUT_VALIDATOR_SHADOW_LOG_PATH"] = str(shadow_audit_path)

        for row in rows:
            run_shadow_mode_capture(
                LLMDecisionEnvelope.from_dict(row),
                ShadowModeMetadata.from_dict(row["metadata"]),
                ShadowModeObservedOutcome.from_dict(row["observed"]),
            )

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/build_shadow_mode_report.py"),
                "--audit-log",
                str(shadow_audit_path),
                "--output-prefix",
                str(report_prefix),
            ],
            check=True,
            cwd=REPO_ROOT,
        )

        shadow_rows = load_jsonl(shadow_audit_path)
        summary = json.loads(report_prefix.with_suffix(".json").read_text(encoding="utf-8"))

        if len(shadow_rows) != 3:
            errors.append(f"expected 3 shadow audit rows, found {len(shadow_rows)}")
        if summary.get("critical_disagreement_count") != 1:
            errors.append("shadow summary should count one critical disagreement")
        if summary.get("promotion_decision") != "rollback":
            errors.append("shadow summary should rollback when a critical disagreement exists")
        if summary.get("citation_coverage") != 1.0:
            errors.append("shadow summary should keep citation coverage at 1.0")
        if summary.get("operator_agreement_rate") != 0.6667:
            errors.append("shadow summary should compute operator_agreement_rate 0.6667")
        if summary.get("blocked_action_recommendation_count") != 1:
            errors.append("shadow summary should count one block_action recommendation")

        print(
            json.dumps(
                {
                    "checked_cases": len(rows),
                    "shadow_audit_rows": len(shadow_rows),
                    "operator_agreement_rate": summary.get("operator_agreement_rate"),
                    "critical_disagreement_count": summary.get("critical_disagreement_count"),
                    "promotion_decision": summary.get("promotion_decision"),
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
