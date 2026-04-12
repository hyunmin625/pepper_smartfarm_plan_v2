#!/usr/bin/env python3
"""Validate state-estimator MVP with synthetic sensor scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from state_estimator import estimate_zone_state  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    scenarios = {
        row["scenario_id"]: row
        for row in load_jsonl(REPO_ROOT / "data/examples/synthetic_sensor_scenarios.jsonl")
    }
    errors: list[str] = []

    normal = estimate_zone_state(scenarios["synthetic-001"])
    if normal.risk_level != "low":
        errors.append("synthetic-001 should stay low risk")

    stale_temp = estimate_zone_state(scenarios["synthetic-004"])
    if stale_temp.risk_level != "unknown" or "pause_automation" not in stale_temp.recommended_action_types:
        errors.append("synthetic-004 should promote to unknown with pause_automation")

    rootzone_bus_loss = estimate_zone_state(scenarios["synthetic-011"])
    if rootzone_bus_loss.risk_level != "unknown" or "request_human_check" not in rootzone_bus_loss.recommended_action_types:
        errors.append("synthetic-011 should promote to unknown with request_human_check")

    reboot_recovery = estimate_zone_state(scenarios["synthetic-012"])
    if reboot_recovery.risk_level != "critical" or "enter_safe_mode" not in reboot_recovery.recommended_action_types:
        errors.append("synthetic-012 should stay critical with enter_safe_mode")

    robot_breach = estimate_zone_state(scenarios["synthetic-014"])
    if robot_breach.risk_level != "critical" or "enter_safe_mode" not in robot_breach.recommended_action_types:
        errors.append("synthetic-014 should stay critical with enter_safe_mode")

    print(
        json.dumps(
            {
                "checked_cases": 5,
                "errors": errors,
                "unknown_cases": [stale_temp.scenario_id, rootzone_bus_loss.scenario_id],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
