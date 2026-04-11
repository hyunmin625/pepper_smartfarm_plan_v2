from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def append_lines(path: Path, lines: list[str]) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def parse_iso_timestamp(value: str) -> int:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return int(timestamp.timestamp() * 1_000_000_000)


def escape_tag(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")


def encode_field_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"{value}i"
    if isinstance(value, float):
        return f"{value}"
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def to_line_protocol(measurement: str, record: dict[str, Any]) -> str:
    tags: dict[str, str] = {
        "site_id": str(record["site_id"]),
        "zone_id": str(record["zone_id"]),
        "quality_flag": str(record.get("quality_flag", "good")),
    }
    if "sensor_id" in record:
        tags["sensor_id"] = str(record["sensor_id"])
        tags["sensor_type"] = str(record["sensor_type"])
        fields_source = record["values"]
    else:
        tags["device_id"] = str(record["device_id"])
        tags["device_type"] = str(record["device_type"])
        fields_source = record["readback"]

    if record.get("quality_reason"):
        tags["quality_reason"] = str(record["quality_reason"])

    tag_text = ",".join(f"{escape_tag(key)}={escape_tag(value)}" for key, value in sorted(tags.items()))
    fields: dict[str, Any] = {"source": record.get("source", "sensor-ingestor")}
    for key, value in fields_source.items():
        if value is None:
            continue
        fields[key] = value
    field_text = ",".join(f"{escape_tag(key)}={encode_field_value(value)}" for key, value in sorted(fields.items()))
    timestamp_ns = parse_iso_timestamp(record["measured_at"])
    return f"{escape_tag(measurement)},{tag_text} {field_text} {timestamp_ns}"


@dataclass
class BackendStatus:
    mqtt_outbox_path: str
    timeseries_outbox_path: str
    object_store_outbox_path: str
    alert_outbox_path: str


class PublishRouter:
    def __init__(self, publish_targets: dict[str, dict[str, Any]]) -> None:
        base_dir = Path(os.getenv("SENSOR_INGESTOR_RUNTIME_DIR", "artifacts/runtime/sensor_ingestor"))
        self.publish_targets = publish_targets
        self.mqtt_outbox_path = Path(
            os.getenv("SENSOR_INGESTOR_MQTT_OUTBOX_PATH", str(base_dir / "mqtt_outbox.jsonl"))
        )
        self.timeseries_outbox_path = Path(
            os.getenv("SENSOR_INGESTOR_TIMESERIES_OUTBOX_PATH", str(base_dir / "timeseries_outbox.lp"))
        )
        self.object_store_outbox_path = Path(
            os.getenv("SENSOR_INGESTOR_OBJECT_STORE_OUTBOX_PATH", str(base_dir / "object_store_outbox.jsonl"))
        )
        self.alert_outbox_path = Path(
            os.getenv("SENSOR_INGESTOR_ALERT_OUTBOX_PATH", str(base_dir / "anomaly_alerts.jsonl"))
        )
        self.last_payloads: dict[str, list[dict[str, Any]]] = {}

    def status_payload(self) -> dict[str, str]:
        return {
            "mqtt_outbox_path": str(self.mqtt_outbox_path),
            "timeseries_outbox_path": str(self.timeseries_outbox_path),
            "object_store_outbox_path": str(self.object_store_outbox_path),
            "alert_outbox_path": str(self.alert_outbox_path),
        }

    def _publish_mqtt(self, target: dict[str, Any], records: list[dict[str, Any]], metrics: Any) -> None:
        envelopes = [
            {
                "target_id": target["target_id"],
                "target_type": target["target_type"],
                "route": target["route"],
                "payload_format": target["payload_format"],
                "published_at": datetime.utcnow().isoformat() + "Z",
                "payload": record,
            }
            for record in records
        ]
        append_jsonl(self.mqtt_outbox_path, envelopes)
        self.last_payloads[target["target_id"]] = envelopes[:2]
        metrics.mqtt_messages_published += len(envelopes)

    def _publish_timeseries(self, target: dict[str, Any], records: list[dict[str, Any]], metrics: Any) -> None:
        lines = [to_line_protocol(target["route"], record) for record in records]
        append_lines(self.timeseries_outbox_path, lines)
        self.last_payloads[target["target_id"]] = [{"line_protocol": line} for line in lines[:2]]
        metrics.timeseries_records_written += len(lines)

    def _publish_object_store(self, target: dict[str, Any], records: list[dict[str, Any]], metrics: Any) -> None:
        rows: list[dict[str, Any]] = []
        for record in records:
            values = record.get("values", {})
            frame_ref = next((value for value in values.values() if isinstance(value, str) and value.startswith("mock://")), None)
            if frame_ref is None:
                continue
            rows.append(
                {
                    "target_id": target["target_id"],
                    "route": target["route"],
                    "stored_at": datetime.utcnow().isoformat() + "Z",
                    "record_ref": {
                        "site_id": record["site_id"],
                        "zone_id": record["zone_id"],
                        "sensor_id": record.get("sensor_id"),
                        "measured_at": record["measured_at"],
                    },
                    "frame_ref": frame_ref,
                }
            )
        if rows:
            append_jsonl(self.object_store_outbox_path, rows)
            self.last_payloads[target["target_id"]] = rows[:2]
            metrics.object_store_records_written += len(rows)

    def publish(self, target_ids: list[str], records: list[dict[str, Any]], metrics: Any) -> None:
        for target_id in target_ids:
            target = self.publish_targets[target_id]
            target_type = target["target_type"]
            if target_type == "mqtt":
                self._publish_mqtt(target, records, metrics)
            elif target_type == "timeseries":
                self._publish_timeseries(target, records, metrics)
            elif target_type == "object_store":
                self._publish_object_store(target, records, metrics)
            metrics.publish_target_counts[target_id] += len(records)

    def publish_alerts(self, alerts: list[dict[str, Any]], metrics: Any) -> None:
        if not alerts:
            return
        append_jsonl(self.alert_outbox_path, alerts)
        metrics.anomaly_alerts_emitted += len(alerts)
