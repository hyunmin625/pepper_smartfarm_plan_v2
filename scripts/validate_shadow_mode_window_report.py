#!/usr/bin/env python3
"""Validate append-style shadow capture and rolling window summary generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="shadow-mode-window-") as tmp_dir:
        shadow_audit = Path(tmp_dir) / "shadow_mode_window_audit.jsonl"
        validator_audit = Path(tmp_dir) / "output_validator_window_audit.jsonl"
        day0_prefix = Path(tmp_dir) / "shadow_day0"
        window_prefix = Path(tmp_dir) / "shadow_window"

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/run_shadow_mode_capture_cases.py"),
                "--cases-file",
                str(REPO_ROOT / "data/examples/shadow_mode_runtime_cases.jsonl"),
                "--cases-file",
                str(REPO_ROOT / "data/examples/shadow_mode_runtime_day0_seed_cases.jsonl"),
                "--audit-log",
                str(shadow_audit),
                "--validator-audit-log",
                str(validator_audit),
                "--output-prefix",
                str(day0_prefix),
            ],
            check=True,
            cwd=REPO_ROOT,
        )

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/build_shadow_mode_window_report.py"),
                "--audit-log",
                str(shadow_audit),
                "--output-prefix",
                str(window_prefix),
            ],
            check=True,
            cwd=REPO_ROOT,
        )

        summary = json.loads(window_prefix.with_suffix(".json").read_text(encoding="utf-8"))
        if summary.get("decision_count") != 15:
            errors.append(f"expected 15 decision rows, found {summary.get('decision_count')}")
        if summary.get("critical_disagreement_count") != 1:
            errors.append("expected one critical disagreement in merged shadow window")
        if summary.get("promotion_decision") != "rollback":
            errors.append("merged shadow window should rollback when a critical disagreement exists")
        if len(summary.get("audit_logs", [])) != 1:
            errors.append("window summary should record one audit log path")
        if "shadow_seed_day0" not in summary.get("eval_set_ids", []) or "shadow-day-20260412" not in summary.get(
            "eval_set_ids", []
        ):
            errors.append("window summary should contain both eval_set_ids")

        print(
            json.dumps(
                {
                    "decision_count": summary.get("decision_count"),
                    "operator_agreement_rate": summary.get("operator_agreement_rate"),
                    "critical_disagreement_count": summary.get("critical_disagreement_count"),
                    "promotion_decision": summary.get("promotion_decision"),
                    "eval_set_ids": summary.get("eval_set_ids"),
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
