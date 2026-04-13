#!/usr/bin/env python3
"""Validate policy-engine loader and execution precheck decisions."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from policy_engine import evaluate_device_policy_precheck, evaluate_override_policy_precheck, load_enabled_policy_rules  # noqa: E402


def main() -> int:
    errors: list[str] = []

    rules = load_enabled_policy_rules()
    if len(rules) < 20:
        errors.append("expected at least 20 enabled policy rules")

    irrigation_path_result = evaluate_device_policy_precheck(
        {
            "request_id": "policy-precheck-001",
            "action_type": "short_irrigation",
            "irrigation_path_degraded": True,
            "policy_snapshot": {"policy_result": "pass", "policy_ids": []},
        }
    )
    if irrigation_path_result.policy_result != "blocked" or "HSV-04" not in irrigation_path_result.policy_ids:
        errors.append("irrigation path degraded should block short_irrigation via HSV-04")

    fertigation_conflict_result = evaluate_device_policy_precheck(
        {
            "request_id": "policy-precheck-002",
            "action_type": "adjust_fertigation",
            "rootzone_sensor_conflict": True,
            "rootzone_control_interpretable": False,
            "policy_snapshot": {"policy_result": "pass", "policy_ids": []},
        }
    )
    if fertigation_conflict_result.policy_result != "approval_required" or "HSV-09" not in fertigation_conflict_result.policy_ids:
        errors.append("rootzone conflict should escalate fertigation to approval_required via HSV-09")

    pass_result = evaluate_device_policy_precheck(
        {
            "request_id": "policy-precheck-003",
            "action_type": "adjust_fan",
            "policy_snapshot": {"policy_result": "pass", "policy_ids": ["seed-pass"]},
        }
    )
    if pass_result.policy_result != "pass" or pass_result.policy_ids != ["seed-pass"]:
        errors.append("clean action should preserve pass snapshot")

    override_result = evaluate_override_policy_precheck(
        {
            "request_id": "policy-precheck-004",
            "override_type": "auto_mode_reentry_request",
            "policy_snapshot": {"policy_result": "approval_required", "policy_ids": ["policy-auto-mode-reentry"]},
        }
    )
    if override_result.policy_result != "approval_required" or "policy-auto-mode-reentry" not in override_result.policy_ids:
        errors.append("override precheck should preserve snapshot policy state")

    print(
        json.dumps(
            {
                "enabled_rule_count": len(rules),
                "irrigation_path_result": irrigation_path_result.__dict__,
                "fertigation_conflict_result": fertigation_conflict_result.__dict__,
                "pass_result": pass_result.__dict__,
                "override_result": override_result.__dict__,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
