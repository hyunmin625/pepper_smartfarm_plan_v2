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

from ops_api.shadow_mode import (  # noqa: E402
    SHADOW_AUDIT_ENV,
    VALIDATOR_AUDIT_ENV,
    build_window_summary_from_paths,
    capture_shadow_cases,
    safe_ratio,
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
    errors: list[str] = []
    if safe_ratio(0, 0) is not None:
        errors.append("safe_ratio should return None for zero denominator")
    if safe_ratio(1, 2) != 0.5:
        errors.append("safe_ratio(1,2) should equal 0.5")

    previous_shadow_env = os.environ.get(SHADOW_AUDIT_ENV)
    previous_validator_env = os.environ.get(VALIDATOR_AUDIT_ENV)
    sentinel = "/tmp/ops-api-shadow-env-sentinel.jsonl"
    os.environ[SHADOW_AUDIT_ENV] = sentinel
    os.environ[VALIDATOR_AUDIT_ENV] = sentinel
    try:
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
            if os.environ.get(SHADOW_AUDIT_ENV) != sentinel:
                errors.append("capture_shadow_cases must restore SHADOW_AUDIT_ENV after call")
            if os.environ.get(VALIDATOR_AUDIT_ENV) != sentinel:
                errors.append("capture_shadow_cases must restore VALIDATOR_AUDIT_ENV after call")
            rebuilt = build_window_summary_from_paths([shadow_path])
            if rebuilt["decision_count"] != len(cases):
                errors.append("rebuilt summary should match captured case count")
            if rebuilt["operator_agreement_rate"] != summary["operator_agreement_rate"]:
                errors.append("rebuilt summary should preserve operator_agreement_rate")

            second = capture_shadow_cases(
                cases,
                shadow_audit_log_path=shadow_path,
                validator_audit_log_path=validator_path,
                append=False,
            )
            rotated = second.get("rotated_audit_logs") or {}
            if not rotated.get("shadow") or not rotated.get("validator"):
                errors.append("second append=False call should rotate previous audit logs")
            elif not Path(rotated["shadow"]).exists():
                errors.append("rotated shadow audit log should exist on disk")

            print(
                json.dumps(
                    {
                        "errors": errors,
                        "decision_count": summary["decision_count"],
                        "operator_agreement_rate": summary["operator_agreement_rate"],
                        "critical_disagreement_count": summary["critical_disagreement_count"],
                        "promotion_decision": summary["promotion_decision"],
                        "rotated_audit_logs": rotated,
                        "shadow_audit_log": str(shadow_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1 if errors else 0
    finally:
        for key, value in (
            (SHADOW_AUDIT_ENV, previous_shadow_env),
            (VALIDATOR_AUDIT_ENV, previous_validator_env),
        ):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
