#!/usr/bin/env python3
"""Validate the synthetic shadow-mode day0 seed pack baseline."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="shadow-seed-pack-") as tmp_dir:
        tmp = Path(tmp_dir)
        audit_log = tmp / "shadow_mode_seed.jsonl"
        validator_audit_log = tmp / "output_validator_seed.jsonl"
        output_prefix = tmp / "shadow_mode_seed_report"

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/run_shadow_mode_seed_pack.py"),
                "--cases-file",
                str(REPO_ROOT / "data/examples/shadow_mode_runtime_day0_seed_cases.jsonl"),
                "--audit-log",
                str(audit_log),
                "--validator-audit-log",
                str(validator_audit_log),
                "--output-prefix",
                str(output_prefix),
            ],
            check=True,
            cwd=REPO_ROOT,
        )

        summary = load_json(output_prefix.with_suffix(".json"))

        if summary.get("decision_count") != 12:
            errors.append("seed pack should contain 12 decisions")
        if summary.get("operator_agreement_rate") != 0.6667:
            errors.append("seed pack operator_agreement_rate should be 0.6667")
        if summary.get("critical_disagreement_count") != 0:
            errors.append("seed pack should have zero critical disagreements")
        if summary.get("promotion_decision") != "hold":
            errors.append("seed pack should stay hold before real shadow mode")
        disagreement_ids = {item.get("request_id") for item in summary.get("top_disagreements", [])}
        expected_ids = {"blind-action-004", "blind-expert-003", "blind-expert-010", "blind-robot-005"}
        if expected_ids - disagreement_ids:
            errors.append("seed pack top disagreements should include all four offline residual ids")

        print(
            json.dumps(
                {
                    "checked_cases": summary.get("decision_count"),
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
