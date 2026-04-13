#!/usr/bin/env python3
"""Validate sensor-specific adapters plus timeout/retry handling."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "sensor-ingestor"))

from sensor_ingestor.runtime import SensorIngestorService  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sensor-ingestor-adapters-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        os.environ["SENSOR_INGESTOR_RUNTIME_DIR"] = str(tmp_path)
        os.environ["SENSOR_INGESTOR_MQTT_OUTBOX_PATH"] = str(tmp_path / "mqtt.jsonl")
        os.environ["SENSOR_INGESTOR_TIMESERIES_OUTBOX_PATH"] = str(tmp_path / "timeseries.lp")
        os.environ["SENSOR_INGESTOR_OBJECT_STORE_OUTBOX_PATH"] = str(tmp_path / "object_store.jsonl")
        os.environ["SENSOR_INGESTOR_ALERT_OUTBOX_PATH"] = str(tmp_path / "alerts.jsonl")

        service = SensorIngestorService.from_files(
            config_path="data/examples/sensor_ingestor_config_seed.json",
            catalog_path="data/examples/sensor_catalog_seed.json",
        )
        summary = service.run_once(
            limit_sensor_groups=None,
            limit_device_groups=2,
            overrides={
                "gh-01-zone-a--co2--01": {"simulate_timeout_attempts": 1},
                "gh-01-outside--outside-weather--01": {"simulate_timeout": True},
                "gh-01-zone-a--circulation-fan--01": {"simulate_timeout_attempts": 1},
            },
        )

        mqtt_rows = read_jsonl(tmp_path / "mqtt.jsonl")
        payloads = [row["payload"] for row in mqtt_rows if isinstance(row, dict) and isinstance(row.get("payload"), dict)]
        sensor_payloads = {payload.get("sensor_type"): payload for payload in payloads if "sensor_type" in payload}

        errors: list[str] = []
        expected_sensor_fields = {
            "air_temp_rh": {"air_temp_c", "relative_humidity_pct"},
            "co2": {"co2_ppm"},
            "par": {"par_umol_m2_s"},
            "substrate_moisture": {"substrate_moisture_pct"},
            "drain_ec_ph": {"drain_ec_ds_m", "drain_ph"},
            "outside_weather": {"outside_temp_c", "outside_rh_pct", "wind_speed_m_s", "rain_mm_h", "solar_radiation_w_m2"},
            "feed_ec_ph": {"feed_ec_ds_m", "feed_ph"},
            "product_moisture": {"product_moisture_pct"},
        }
        for sensor_type, required_fields in expected_sensor_fields.items():
            payload = sensor_payloads.get(sensor_type)
            if payload is None:
                errors.append(f"missing payload for sensor_type={sensor_type}")
                continue
            values = payload.get("values", {})
            if not isinstance(values, dict):
                errors.append(f"sensor_type={sensor_type} values missing")
                continue
            missing_fields = sorted(required_fields - set(values.keys()))
            if missing_fields:
                errors.append(f"sensor_type={sensor_type} missing fields {missing_fields}")
            if "ingested_at" not in payload:
                errors.append(f"sensor_type={sensor_type} missing ingested_at")

        outside_payload = sensor_payloads.get("outside_weather")
        if outside_payload is None or outside_payload.get("quality_reason") not in {"missing", "communication_loss"}:
            errors.append("outside_weather timeout fallback did not degrade to missing/communication-loss path")

        if summary["sensor_retry_attempts"] < 1:
            errors.append("sensor retry attempts did not increment")
        if summary["device_retry_attempts"] < 1:
            errors.append("device retry attempts did not increment")
        if summary["timeout_fallback_records"] < 1:
            errors.append("timeout fallback records did not increment")

        print(
            json.dumps(
                {
                    "sensor_retry_attempts": summary["sensor_retry_attempts"],
                    "device_retry_attempts": summary["device_retry_attempts"],
                    "timeout_fallback_records": summary["timeout_fallback_records"],
                    "mqtt_rows": len(mqtt_rows),
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
