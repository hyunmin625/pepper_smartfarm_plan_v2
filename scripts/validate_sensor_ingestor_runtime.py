#!/usr/bin/env python3
"""Validate sensor-ingestor publish backends and quality alerts."""

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
    with tempfile.TemporaryDirectory(prefix="sensor-ingestor-runtime-") as tmp_dir:
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

        first_summary = service.run_once(limit_sensor_groups=2, limit_device_groups=1)
        second_summary = service.run_once(
            limit_sensor_groups=2,
            limit_device_groups=1,
            overrides={
                "gh-01-zone-a--substrate-moisture--01": {
                    "values": {"substrate_moisture_pct": 150.0},
                },
                "gh-01-zone-a--circulation-fan--01": {
                    "readback": {"fault_state": True, "run_state": "fault"},
                },
            },
        )

        mqtt_rows = read_jsonl(tmp_path / "mqtt.jsonl")
        alert_rows = read_jsonl(tmp_path / "alerts.jsonl")
        timeseries_lines = (tmp_path / "timeseries.lp").read_text(encoding="utf-8").splitlines()

        errors: list[str] = []
        if not mqtt_rows:
            errors.append("mqtt outbox is empty")
        if not timeseries_lines:
            errors.append("timeseries outbox is empty")
        if not alert_rows:
            errors.append("alert outbox is empty")
        elif not any(row.get("quality_reason") in {"outlier", "device_fault"} for row in alert_rows):
            errors.append("expected outlier/device_fault alert not found")
        if first_summary["backend_status"]["mqtt_outbox_path"] != str(tmp_path / "mqtt.jsonl"):
            errors.append("backend status did not expose mqtt path")
        if second_summary["anomaly_alerts_emitted"] < 1:
            errors.append("anomaly_alerts_emitted did not increment")

        summary = {
            "mqtt_rows": len(mqtt_rows),
            "timeseries_lines": len(timeseries_lines),
            "alert_rows": len(alert_rows),
            "anomaly_alerts_emitted": second_summary["anomaly_alerts_emitted"],
            "errors": errors,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
