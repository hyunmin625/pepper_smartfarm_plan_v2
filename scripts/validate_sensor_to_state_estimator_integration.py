#!/usr/bin/env python3
"""Validate sensor-ingestor MQTT outbox -> state-estimator integration."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "sensor-ingestor"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from sensor_ingestor.runtime import SensorIngestorService  # noqa: E402
from state_estimator import (  # noqa: E402
    build_snapshot_from_ingestor_outbox,
    build_zone_state_from_ingestor_outbox,
    group_ingestor_records_by_zone,
    load_sensor_ingestor_mqtt_outbox,
    validate_feature_snapshot,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sensor-state-bridge-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        mqtt_outbox = tmp_path / "mqtt.jsonl"
        os.environ["SENSOR_INGESTOR_RUNTIME_DIR"] = str(tmp_path)
        os.environ["SENSOR_INGESTOR_MQTT_OUTBOX_PATH"] = str(mqtt_outbox)
        os.environ["SENSOR_INGESTOR_TIMESERIES_OUTBOX_PATH"] = str(tmp_path / "timeseries.lp")
        os.environ["SENSOR_INGESTOR_OBJECT_STORE_OUTBOX_PATH"] = str(tmp_path / "object_store.jsonl")
        os.environ["SENSOR_INGESTOR_ALERT_OUTBOX_PATH"] = str(tmp_path / "alerts.jsonl")

        service = SensorIngestorService.from_files(
            config_path="data/examples/sensor_ingestor_config_seed.json",
            catalog_path="data/examples/sensor_catalog_seed.json",
        )
        run_summary = service.run_once()

        rows = load_sensor_ingestor_mqtt_outbox(mqtt_outbox)
        grouped = group_ingestor_records_by_zone(rows)
        snapshot = build_snapshot_from_ingestor_outbox(
            mqtt_outbox,
            zone_id="gh-01-zone-a",
            growth_stage="flowering",
            farm_id="gh-01",
        )
        zone_state = build_zone_state_from_ingestor_outbox(
            mqtt_outbox,
            zone_id="gh-01-zone-a",
            growth_stage="flowering",
            farm_id="gh-01",
        )

        errors: list[str] = []
        if run_summary["sensor_records_published"] < 1:
            errors.append("sensor-ingestor should publish sensor records")
        if not rows:
            errors.append("mqtt outbox should contain published envelopes")
        if "gh-01-zone-a" not in grouped:
            errors.append("zone-a should be present in grouped outbox records")
        if not snapshot.get("current_state"):
            errors.append("snapshot current_state should be populated from outbox")
        if not snapshot.get("device_status"):
            errors.append("snapshot device_status should be populated from outbox")
        if not snapshot.get("sensor_quality"):
            errors.append("snapshot sensor_quality should be populated from outbox")
        if not zone_state.get("derived_features"):
            errors.append("zone_state should include derived_features")
        else:
            feature_errors = validate_feature_snapshot(zone_state["derived_features"])
            if feature_errors:
                errors.extend(f"feature_validation:{item}" for item in feature_errors)
        climate = zone_state.get("derived_features", {}).get("climate", {})
        if climate.get("air_temperature_1m_avg_c", {}).get("value") is None:
            errors.append("air_temperature_1m_avg_c should be derived from mqtt outbox")
        if climate.get("vpd_kpa", {}).get("value") is None:
            errors.append("vpd_kpa should be derived from mqtt outbox")
        rootzone = zone_state.get("derived_features", {}).get("rootzone", {})
        if rootzone.get("substrate_moisture_1m_avg_pct", {}).get("value") is None:
            errors.append("substrate_moisture_1m_avg_pct should be derived from mqtt outbox")
        if len(grouped) < 2:
            errors.append("expected at least two zones in mqtt outbox grouping")

        print(
            json.dumps(
                {
                    "errors": errors,
                    "mqtt_rows": len(rows),
                    "zones_seen": sorted(grouped.keys()),
                    "zone_a_current_state_keys": sorted(snapshot.get("current_state", {}).keys()),
                    "zone_a_device_count": len(snapshot.get("device_status", [])),
                    "sample_metrics": {
                        "air_temperature_1m_avg_c": climate.get("air_temperature_1m_avg_c", {}).get("value"),
                        "vpd_kpa": climate.get("vpd_kpa", {}).get("value"),
                        "substrate_moisture_1m_avg_pct": rootzone.get("substrate_moisture_1m_avg_pct", {}).get("value"),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
