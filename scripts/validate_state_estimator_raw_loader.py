#!/usr/bin/env python3
"""Validate raw sensor loader -> feature snapshot path."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from state_estimator import (  # noqa: E402
    build_feature_snapshot,
    build_snapshot_from_raw_records,
    build_zone_state_from_raw_records,
    validate_feature_snapshot,
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
    records = load_jsonl(REPO_ROOT / "data/examples/raw_sensor_window_seed.jsonl")
    snapshot = build_snapshot_from_raw_records(
        records,
        zone_id="gh-01-zone-a",
        growth_stage="flowering",
        farm_id="gh-01",
    )
    features = build_feature_snapshot(snapshot)
    zone_state = build_zone_state_from_raw_records(
        records,
        zone_id="gh-01-zone-a",
        growth_stage="flowering",
        farm_id="gh-01",
    )

    errors: list[str] = []
    climate = features["climate"]
    rootzone = features["rootzone"]
    risk_scores = features["risk_scores"]

    if climate["air_temperature_1m_avg_c"]["value"] is None:
        errors.append("air_temperature_1m_avg_c should be populated from raw records")
    if climate["air_temperature_10m_delta_c"]["value"] is None:
        errors.append("air_temperature_10m_delta_c should be populated from raw records")
    if climate["par_10m_delta_umol_m2_s"]["value"] is None:
        errors.append("par_10m_delta_umol_m2_s should be populated from raw records")
    if rootzone["substrate_moisture_10m_delta_pct"]["value"] is None:
        errors.append("substrate_moisture_10m_delta_pct should be populated from raw records")
    if risk_scores["rootzone_stress_score"]["score"] is None:
        errors.append("rootzone_stress_score should be calculated")
    if not snapshot.get("device_status"):
        errors.append("device_status should be collected from raw device records")
    if validate_feature_snapshot(features):
        errors.append("validate_feature_snapshot should pass for raw seed window")
    if zone_state["derived_features"]["climate"]["co2_1m_avg_ppm"]["value"] is None:
        errors.append("zone_state derived features should include co2_1m_avg_ppm")

    print(
        json.dumps(
            {
                "errors": errors,
                "current_state_keys": sorted(snapshot["current_state"].keys()),
                "history_windows": sorted(snapshot["history"]["air_temp_c"].keys()),
                "sample_metrics": {
                    "air_temperature_1m_avg_c": climate["air_temperature_1m_avg_c"]["value"],
                    "air_temperature_10m_delta_c": climate["air_temperature_10m_delta_c"]["value"],
                    "substrate_moisture_10m_delta_pct": rootzone["substrate_moisture_10m_delta_pct"]["value"],
                    "rootzone_stress_score": risk_scores["rootzone_stress_score"]["score"],
                    "automation_safety_score": risk_scores["automation_safety_score"]["score"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
