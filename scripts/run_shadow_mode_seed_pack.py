#!/usr/bin/env python3
"""Run a synthetic shadow-mode seed pack through runtime capture and summary."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator.runtime import (  # noqa: E402
    LLMDecisionEnvelope,
    ShadowModeMetadata,
    ShadowModeObservedOutcome,
    run_shadow_mode_capture,
)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases-file",
        default="data/examples/shadow_mode_runtime_day0_seed_cases.jsonl",
        help="Synthetic shadow-mode runtime cases JSONL.",
    )
    parser.add_argument(
        "--audit-log",
        default="artifacts/runtime/llm_orchestrator/shadow_mode_ds_v11_day0_seed.jsonl",
        help="Output shadow audit JSONL path.",
    )
    parser.add_argument(
        "--validator-audit-log",
        default="artifacts/runtime/llm_orchestrator/output_validator_ds_v11_day0_seed.jsonl",
        help="Output validator audit JSONL path.",
    )
    parser.add_argument(
        "--output-prefix",
        default="artifacts/reports/shadow_mode_ds_v11_day0_seed",
        help="Output prefix for summary JSON/MD.",
    )
    args = parser.parse_args()

    cases_path = Path(args.cases_file)
    rows = load_jsonl(cases_path)
    shadow_audit_path = Path(args.audit_log)
    validator_audit_path = Path(args.validator_audit_log)
    output_prefix = Path(args.output_prefix)

    for path in (shadow_audit_path, validator_audit_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()

    os.environ["LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH"] = str(validator_audit_path)
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
            str(output_prefix),
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    summary_path = output_prefix.with_suffix(".json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    print(f"cases_file: {cases_path}")
    print(f"audit_log: {shadow_audit_path}")
    print(f"summary_json: {summary_path}")
    print(f"decision_count: {summary['decision_count']}")
    print(f"operator_agreement_rate: {summary['operator_agreement_rate']}")
    print(f"critical_disagreement_count: {summary['critical_disagreement_count']}")
    print(f"promotion_decision: {summary['promotion_decision']}")


if __name__ == "__main__":
    main()
