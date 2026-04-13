from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

from .adapters import AdapterContext, SensorAdapterRegistry
from .backends import PublishRouter
from .config import LoadedConfig
from .quality import SensorHistoryEntry, evaluate_device_quality, evaluate_sensor_quality


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_device_readback(device_type: str) -> dict[str, Any]:
    if device_type in {"circulation_fan", "dry_fan"}:
        return {"run_state": "on", "speed_pct": 55}
    if device_type in {"vent_window", "shade_curtain"}:
        return {"run_state": "moving", "position_pct": 35}
    if device_type in {"irrigation_valve", "source_water_valve"}:
        return {"run_state": "closed"}
    if device_type in {"heater", "dehumidifier"}:
        return {"run_state": "off", "stage": 0}
    if device_type == "co2_doser":
        return {"run_state": "off", "dose_pct": 0}
    if device_type == "nutrient_mixer":
        return {"run_state": "idle", "recipe_stage": "standby"}
    return {"run_state": "unknown"}


def merge_override(record: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    if not override:
        return record
    merged = dict(record)
    for key, value in override.items():
        if key in {"values", "readback"} and isinstance(value, dict):
            current = dict(merged.get(key, {}))
            current.update(value)
            merged[key] = current
            continue
        merged[key] = value
    return merged


@dataclass
class RuntimeMetrics:
    run_count: int = 0
    sensor_groups_processed: int = 0
    device_groups_processed: int = 0
    sensor_records_published: int = 0
    device_records_published: int = 0
    mqtt_messages_published: int = 0
    timeseries_records_written: int = 0
    object_store_records_written: int = 0
    anomaly_alerts_emitted: int = 0
    sensor_retry_attempts: int = 0
    device_retry_attempts: int = 0
    timeout_fallback_records: int = 0
    publish_target_counts: Counter[str] = field(default_factory=Counter)
    last_run_at: str | None = None
    last_error: str | None = None

    def as_prometheus(self) -> str:
        lines = [
            "# HELP sensor_ingestor_run_count Total completed sensor-ingestor runs",
            "# TYPE sensor_ingestor_run_count counter",
            f"sensor_ingestor_run_count {self.run_count}",
            "# HELP sensor_ingestor_sensor_groups_processed Total processed sensor binding groups",
            "# TYPE sensor_ingestor_sensor_groups_processed counter",
            f"sensor_ingestor_sensor_groups_processed {self.sensor_groups_processed}",
            "# HELP sensor_ingestor_device_groups_processed Total processed device binding groups",
            "# TYPE sensor_ingestor_device_groups_processed counter",
            f"sensor_ingestor_device_groups_processed {self.device_groups_processed}",
            "# HELP sensor_ingestor_sensor_records_published Total normalized sensor records",
            "# TYPE sensor_ingestor_sensor_records_published counter",
            f"sensor_ingestor_sensor_records_published {self.sensor_records_published}",
            "# HELP sensor_ingestor_device_records_published Total normalized device records",
            "# TYPE sensor_ingestor_device_records_published counter",
            f"sensor_ingestor_device_records_published {self.device_records_published}",
            "# HELP sensor_ingestor_mqtt_messages_published Total MQTT envelopes written",
            "# TYPE sensor_ingestor_mqtt_messages_published counter",
            f"sensor_ingestor_mqtt_messages_published {self.mqtt_messages_published}",
            "# HELP sensor_ingestor_timeseries_records_written Total timeseries points written",
            "# TYPE sensor_ingestor_timeseries_records_written counter",
            f"sensor_ingestor_timeseries_records_written {self.timeseries_records_written}",
            "# HELP sensor_ingestor_anomaly_alerts_emitted Total anomaly alerts emitted",
            "# TYPE sensor_ingestor_anomaly_alerts_emitted counter",
            f"sensor_ingestor_anomaly_alerts_emitted {self.anomaly_alerts_emitted}",
            "# HELP sensor_ingestor_sensor_retry_attempts Total sensor read retries attempted",
            "# TYPE sensor_ingestor_sensor_retry_attempts counter",
            f"sensor_ingestor_sensor_retry_attempts {self.sensor_retry_attempts}",
            "# HELP sensor_ingestor_device_retry_attempts Total device read retries attempted",
            "# TYPE sensor_ingestor_device_retry_attempts counter",
            f"sensor_ingestor_device_retry_attempts {self.device_retry_attempts}",
            "# HELP sensor_ingestor_timeout_fallback_records Total records emitted after retry exhaustion",
            "# TYPE sensor_ingestor_timeout_fallback_records counter",
            f"sensor_ingestor_timeout_fallback_records {self.timeout_fallback_records}",
        ]
        for target_id, count in sorted(self.publish_target_counts.items()):
            lines.append(f'sensor_ingestor_publish_target_total{{target_id="{target_id}"}} {count}')
        return "\n".join(lines) + "\n"


class SensorIngestorService:
    def __init__(
        self,
        loaded: LoadedConfig,
        *,
        timeseries_writer: Any | None = None,
    ) -> None:
        self.loaded = loaded
        self.metrics = RuntimeMetrics()
        self.publisher = PublishRouter(loaded.publish_targets)
        self.sensor_adapters = SensorAdapterRegistry()
        self.sensor_history: dict[str, SensorHistoryEntry] = {}
        self._http_server: ThreadingHTTPServer | None = None
        self._http_thread: Thread | None = None
        self.timeseries_writer = timeseries_writer

    @classmethod
    def from_files(cls, *, config_path: str, catalog_path: str | None = None) -> "SensorIngestorService":
        return cls(LoadedConfig.from_files(config_path, catalog_path))

    @property
    def site_id(self) -> str:
        return self.loaded.config["site_id"]

    def _sensor_groups(self) -> list[dict[str, Any]]:
        return [group for group in self.loaded.config.get("sensor_binding_groups", []) if group.get("enabled", False)]

    def _device_groups(self) -> list[dict[str, Any]]:
        return [group for group in self.loaded.config.get("device_binding_groups", []) if group.get("enabled", False)]

    def _timeseries_write(self, normalized: list[dict[str, Any]]) -> None:
        if self.timeseries_writer is None or not normalized:
            return
        try:
            self.timeseries_writer.write_records(normalized)
        except Exception as exc:  # pragma: no cover - defensive branch
            self.metrics.last_error = f"timeseries_writer: {exc}"

    @staticmethod
    def _simulate_timeout(override: dict[str, Any] | None, attempt_index: int) -> bool:
        if not override:
            return False
        if override.get("simulate_timeout") is True:
            return True
        timeout_attempts = override.get("simulate_timeout_attempts")
        return isinstance(timeout_attempts, int) and attempt_index < timeout_attempts

    def _read_sensor_with_retry(
        self,
        sensor: dict[str, Any],
        group: dict[str, Any],
        poller_profile: dict[str, Any],
        override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        measured_at = utc_now()
        context = AdapterContext(site_id=self.site_id, measured_at=measured_at, override=override)
        adapter = self.sensor_adapters.for_sensor(sensor)
        max_attempts = poller_profile["retry_count"] + 1

        for attempt_index in range(max_attempts):
            if self._simulate_timeout(override, attempt_index):
                if attempt_index < max_attempts - 1:
                    self.metrics.sensor_retry_attempts += 1
                    continue
                fallback = adapter.timeout_fallback(sensor, context)
                fallback["parser_id"] = group["parser_id"]
                fallback["poll_interval_seconds"] = poller_profile["poll_interval_seconds"]
                fallback["quality_rule_set_id"] = group["quality_rule_set_id"]
                fallback["timeout_retry_exhausted"] = True
                fallback["retry_count"] = poller_profile["retry_count"]
                self.metrics.timeout_fallback_records += 1
                return merge_override(fallback, override)
            record = adapter.read(sensor, context)
            record["parser_id"] = group["parser_id"]
            record["poll_interval_seconds"] = poller_profile["poll_interval_seconds"]
            record["quality_rule_set_id"] = group["quality_rule_set_id"]
            record["retry_count"] = poller_profile["retry_count"]
            return merge_override(record, override)

        fallback = adapter.timeout_fallback(sensor, context)
        fallback["parser_id"] = group["parser_id"]
        fallback["poll_interval_seconds"] = poller_profile["poll_interval_seconds"]
        fallback["quality_rule_set_id"] = group["quality_rule_set_id"]
        fallback["timeout_retry_exhausted"] = True
        fallback["retry_count"] = poller_profile["retry_count"]
        self.metrics.timeout_fallback_records += 1
        return merge_override(fallback, override)

    def _read_sensor_group(self, group: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        poller_profile = self.loaded.poller_profiles[group["poller_profile_id"]]
        for sensor_id in group["sensor_ids"]:
            sensor = self.loaded.sensors[sensor_id]
            records.append(self._read_sensor_with_retry(sensor, group, poller_profile, overrides.get(sensor_id)))
        return records

    def _read_device_with_retry(
        self,
        device: dict[str, Any],
        group: dict[str, Any],
        poller_profile: dict[str, Any],
        override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        measured_at = utc_now()
        max_attempts = poller_profile["retry_count"] + 1
        for attempt_index in range(max_attempts):
            if self._simulate_timeout(override, attempt_index):
                if attempt_index < max_attempts - 1:
                    self.metrics.device_retry_attempts += 1
                    continue
                fallback = {
                    "record_kind": "device",
                    "site_id": self.site_id,
                    "zone_id": device["zone_id"],
                    "device_id": device["device_id"],
                    "device_type": device["device_type"],
                    "measured_at": measured_at,
                    "protocol": device["protocol"],
                    "parser_id": group["parser_id"],
                    "transport_status": "down",
                    "readback": {"fault_state": True, "run_state": "fault"},
                    "timeout_retry_exhausted": True,
                    "retry_count": poller_profile["retry_count"],
                }
                self.metrics.timeout_fallback_records += 1
                return merge_override(fallback, override)
            base_record = {
                "record_kind": "device",
                "site_id": self.site_id,
                "zone_id": device["zone_id"],
                "device_id": device["device_id"],
                "device_type": device["device_type"],
                "measured_at": measured_at,
                "protocol": device["protocol"],
                "parser_id": group["parser_id"],
                "transport_status": "ok",
                "readback": default_device_readback(device["device_type"]),
                "retry_count": poller_profile["retry_count"],
            }
            return merge_override(base_record, override)

        fallback = {
            "record_kind": "device",
            "site_id": self.site_id,
            "zone_id": device["zone_id"],
            "device_id": device["device_id"],
            "device_type": device["device_type"],
            "measured_at": measured_at,
            "protocol": device["protocol"],
            "parser_id": group["parser_id"],
            "transport_status": "down",
            "readback": {"fault_state": True, "run_state": "fault"},
            "timeout_retry_exhausted": True,
            "retry_count": poller_profile["retry_count"],
        }
        self.metrics.timeout_fallback_records += 1
        return merge_override(fallback, override)

    def _read_device_group(self, group: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        poller_profile = self.loaded.poller_profiles[group["poller_profile_id"]]
        for device_id in group["device_ids"]:
            device = self.loaded.devices[device_id]
            records.append(self._read_device_with_retry(device, group, poller_profile, overrides.get(device_id)))
        return records

    def _parse_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        for record in records:
            record_copy = dict(record)
            record_copy["parsed_at"] = utc_now()
            parsed.append(record_copy)
        return parsed

    def _normalize_sensor_record(self, record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        sensor = self.loaded.sensors[record["sensor_id"]]
        rule_set = self.loaded.quality_rule_sets[record["quality_rule_set_id"]]
        assessment, next_history = evaluate_sensor_quality(
            measured_at=record["measured_at"],
            values=record["values"],
            rule_set=rule_set,
            sample_interval_seconds=record["poll_interval_seconds"],
            previous=self.sensor_history.get(record["sensor_id"]),
            transport_status=record.get("transport_status", "ok"),
            calibration_due=bool(record.get("calibration_due", False)),
        )
        self.sensor_history[record["sensor_id"]] = next_history
        normalized = {
            "site_id": record["site_id"],
            "zone_id": record["zone_id"],
            "measured_at": record["measured_at"],
            "ingested_at": utc_now(),
            "source": "sensor-ingestor",
            "sensor_id": record["sensor_id"],
            "sensor_type": record["sensor_type"],
            "values": record["values"],
            "calibration_version": f"{sensor['model_profile']}-baseline",
            "quality_flag": assessment.quality_flag,
            "quality_reason": assessment.quality_reason,
            "automation_gate": assessment.automation_gate,
            "quality_details": assessment.details,
        }
        alert = None
        if assessment.quality_flag != "good":
            alert = {
                "alert_type": "sensor_anomaly",
                "site_id": record["site_id"],
                "zone_id": record["zone_id"],
                "sensor_id": record["sensor_id"],
                "sensor_type": record["sensor_type"],
                "measured_at": record["measured_at"],
                "quality_flag": assessment.quality_flag,
                "quality_reason": assessment.quality_reason,
                "details": assessment.details,
            }
        return normalized, alert

    def _normalize_device_record(self, record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        assessment = evaluate_device_quality(
            readback=record["readback"],
            transport_status=record.get("transport_status", "ok"),
        )
        normalized = {
            "site_id": record["site_id"],
            "zone_id": record["zone_id"],
            "measured_at": record["measured_at"],
            "ingested_at": utc_now(),
            "source": "sensor-ingestor",
            "device_id": record["device_id"],
            "device_type": record["device_type"],
            "readback": record["readback"],
            "quality_flag": assessment.quality_flag,
            "quality_reason": assessment.quality_reason,
            "automation_gate": assessment.automation_gate,
            "quality_details": assessment.details,
        }
        alert = None
        if assessment.quality_flag != "good":
            alert = {
                "alert_type": "device_readback_anomaly",
                "site_id": record["site_id"],
                "zone_id": record["zone_id"],
                "device_id": record["device_id"],
                "device_type": record["device_type"],
                "measured_at": record["measured_at"],
                "quality_flag": assessment.quality_flag,
                "quality_reason": assessment.quality_reason,
                "details": assessment.details,
            }
        return normalized, alert

    def _normalize_records(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        normalized: list[dict[str, Any]] = []
        alerts: list[dict[str, Any]] = []
        for record in records:
            if record["record_kind"] == "sensor":
                normalized_record, alert = self._normalize_sensor_record(record)
            else:
                normalized_record, alert = self._normalize_device_record(record)
            normalized.append(normalized_record)
            if alert is not None:
                alerts.append(alert)
        return normalized, alerts

    def run_once(
        self,
        *,
        limit_sensor_groups: int | None = None,
        limit_device_groups: int | None = None,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        processed_sensor_groups: list[str] = []
        processed_device_groups: list[str] = []
        alerts_emitted: list[dict[str, Any]] = []
        record_overrides = overrides or {}

        try:
            for group in self._sensor_groups()[:limit_sensor_groups]:
                normalized, alerts = self._normalize_records(
                    self._parse_records(self._read_sensor_group(group, record_overrides))
                )
                self.publisher.publish(group["publish_targets"], normalized, self.metrics)
                self.publisher.publish_alerts(alerts, self.metrics)
                self._timeseries_write(normalized)
                processed_sensor_groups.append(group["binding_group_id"])
                alerts_emitted.extend(alerts)
                self.metrics.sensor_groups_processed += 1
                self.metrics.sensor_records_published += len(normalized)

            for group in self._device_groups()[:limit_device_groups]:
                normalized, alerts = self._normalize_records(
                    self._parse_records(self._read_device_group(group, record_overrides))
                )
                self.publisher.publish(group["publish_targets"], normalized, self.metrics)
                self.publisher.publish_alerts(alerts, self.metrics)
                self._timeseries_write(normalized)
                processed_device_groups.append(group["binding_group_id"])
                alerts_emitted.extend(alerts)
                self.metrics.device_groups_processed += 1
                self.metrics.device_records_published += len(normalized)

            self.metrics.run_count += 1
            self.metrics.last_run_at = utc_now()
            self.metrics.last_error = None
        except Exception as exc:  # pragma: no cover - defensive branch
            self.metrics.last_error = str(exc)
            raise

        return {
            "site_id": self.site_id,
            "config_path": str(self.loaded.config_path),
            "catalog_path": str(self.loaded.catalog_path),
            "processed_sensor_groups": processed_sensor_groups,
            "processed_device_groups": processed_device_groups,
            "sensor_records_published": self.metrics.sensor_records_published,
            "device_records_published": self.metrics.device_records_published,
            "anomaly_alerts_emitted": self.metrics.anomaly_alerts_emitted,
            "sensor_retry_attempts": self.metrics.sensor_retry_attempts,
            "device_retry_attempts": self.metrics.device_retry_attempts,
            "timeout_fallback_records": self.metrics.timeout_fallback_records,
            "backend_status": self.publisher.status_payload(),
            "alert_preview": alerts_emitted[:3],
            "health": self.health_payload(),
            "metrics_preview": self.metrics.as_prometheus().splitlines()[:14],
        }

    def health_payload(self) -> dict[str, Any]:
        status = "ok" if self.metrics.last_error is None else "error"
        return {
            "status": status,
            "site_id": self.site_id,
            "last_run_at": self.metrics.last_run_at,
            "last_error": self.metrics.last_error,
            "sensor_groups_processed": self.metrics.sensor_groups_processed,
            "device_groups_processed": self.metrics.device_groups_processed,
            "mqtt_messages_published": self.metrics.mqtt_messages_published,
            "timeseries_records_written": self.metrics.timeseries_records_written,
            "anomaly_alerts_emitted": self.metrics.anomaly_alerts_emitted,
            "sensor_retry_attempts": self.metrics.sensor_retry_attempts,
            "device_retry_attempts": self.metrics.device_retry_attempts,
            "timeout_fallback_records": self.metrics.timeout_fallback_records,
        }

    def start_http_server(self, port: int) -> None:
        service = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/healthz":
                    payload = json.dumps(service.health_payload()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                if self.path == "/metrics":
                    payload = service.metrics.as_prometheus().encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

        self._http_server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self._http_thread = Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()

    def stop_http_server(self) -> None:
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None
        if self._http_thread is not None:
            self._http_thread.join(timeout=1)
            self._http_thread = None
