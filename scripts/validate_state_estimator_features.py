#!/usr/bin/env python3
"""Validate derived feature builder with synthetic sensor scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from state_estimator import build_feature_snapshot  # noqa: E402


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

    stable = build_feature_snapshot(scenarios["synthetic-001"])
    if stable["climate"]["vpd_kpa"]["value"] is None:
        errors.append("synthetic-001 should calculate VPD")
    if stable["risk_scores"]["sensor_reliability_score"]["score"] <= 0.5:
        errors.append("synthetic-001 should keep sensor reliability high")

    rootzone = build_feature_snapshot(scenarios["synthetic-003"])
    if rootzone["rootzone"]["rootzone_stress_risk"]["level"] not in {"medium", "high"}:
        errors.append("synthetic-003 should elevate rootzone stress risk")

    stale = build_feature_snapshot(scenarios["synthetic-004"])
    if stale["risk_scores"]["sensor_reliability_score"]["score"] >= 0.6:
        errors.append("synthetic-004 should lower sensor reliability score")

    heat = build_feature_snapshot(scenarios["synthetic-008"])
    if heat["climate"]["heat_stress_risk"]["level"] not in {"high", "critical"}:
        errors.append("synthetic-008 should detect heat stress")

    print(
        json.dumps(
            {
                "checked_cases": 4,
                "errors": errors,
                "sample_scores": {
                    "synthetic-001_vpd": stable["climate"]["vpd_kpa"]["value"],
                    "synthetic-003_rootzone_risk": rootzone["rootzone"]["rootzone_stress_risk"]["level"],
                    "synthetic-004_reliability": stale["risk_scores"]["sensor_reliability_score"]["score"],
                    "synthetic-008_heat": heat["climate"]["heat_stress_risk"]["level"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
