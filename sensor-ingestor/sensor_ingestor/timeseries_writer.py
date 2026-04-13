"""TimescaleDB sensor writer.

Bridges sensor-ingestor normalized records into the ``sensor_readings``
hypertable (or its sqlite equivalent for tests). Optionally publishes
each row to a process-local RealtimeBroker so the ops-api SSE endpoint
can stream live readings to operator browsers.

Design notes:

- The writer is **decoupled from the runtime**: SensorIngestorService
  only calls ``writer.write_records(normalized)`` if a writer was
  injected at construction time. Standalone runs without a writer keep
  publishing through the existing PublishRouter outbox.
- One sensor-ingestor record can carry multiple metric values
  (e.g. a single climate sensor emits ``air_temp_c``, ``rh_pct``,
  ``vpd_kpa`` in one tick). We fan it out into one
  ``SensorReadingRecord`` per metric so the hypertable stays
  long-format.
- Numeric values land in ``metric_value_double``, string/enum
  readbacks land in ``metric_value_text``. Mixed dicts are stored as
  the JSON ``metadata_json`` payload.
- The writer is intentionally synchronous: sensor-ingestor itself runs
  in a sync runtime today. The realtime broker has a
  ``publish_nowait`` shim so we can call it from this sync context.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "ops-api") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from ops_api.models import SensorReadingRecord  # noqa: E402


class _BrokerLike(Protocol):
    def publish_nowait(self, record: dict[str, Any]) -> int: ...


@dataclass
class WriteSummary:
    sensor_record_count: int = 0
    device_record_count: int = 0
    metric_row_count: int = 0
    broker_publish_count: int = 0


class TimeseriesWriter:
    """Insert normalized sensor-ingestor records into ``sensor_readings``.

    Construction:

    >>> from ops_api.database import build_session_factory
    >>> session_factory = build_session_factory("sqlite:////tmp/ops_api.db")
    >>> writer = TimeseriesWriter(session_factory=session_factory, broker=None)

    Usage:

    >>> writer.write_records(normalized_sensor_records)
    >>> writer.write_records(normalized_device_records)
    """

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        broker: _BrokerLike | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.broker = broker

    def write_records(self, records: Iterable[dict[str, Any]]) -> WriteSummary:
        summary = WriteSummary()
        rows: list[SensorReadingRecord] = []
        broadcast_payloads: list[dict[str, Any]] = []
        for record in records:
            kind = "device" if "device_id" in record else "sensor"
            for row, broadcast in self._explode_record(record, kind):
                rows.append(row)
                broadcast_payloads.append(broadcast)
            if kind == "sensor":
                summary.sensor_record_count += 1
            else:
                summary.device_record_count += 1
        if not rows:
            return summary
        session = self.session_factory()
        try:
            session.add_all(rows)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        summary.metric_row_count = len(rows)
        if self.broker is not None:
            for payload in broadcast_payloads:
                summary.broker_publish_count += self.broker.publish_nowait(payload)
        return summary

    def _explode_record(
        self,
        record: dict[str, Any],
        kind: str,
    ) -> Iterable[tuple[SensorReadingRecord, dict[str, Any]]]:
        measured_at = _parse_timestamp(record.get("measured_at"))
        ingested_at = _parse_timestamp(record.get("ingested_at")) or measured_at
        site_id = str(record.get("site_id") or "unknown-site")
        zone_id = str(record.get("zone_id") or "unknown-zone")
        quality_flag = str(record.get("quality_flag") or "unknown")
        transport_status = str(record.get("transport_status") or "ok")
        binding_group_id = record.get("binding_group_id")
        parser_id = record.get("parser_id")
        calibration_version = record.get("calibration_version")
        source = str(record.get("source") or "sensor-ingestor")
        details = record.get("quality_details") or {}
        if kind == "sensor":
            source_id = str(record.get("sensor_id") or "unknown-sensor")
            source_type = str(record.get("sensor_type") or "unknown")
            metric_pairs = (record.get("values") or {}).items()
        else:
            source_id = str(record.get("device_id") or "unknown-device")
            source_type = str(record.get("device_type") or "unknown")
            metric_pairs = (record.get("readback") or {}).items()
        for metric_name, value in metric_pairs:
            metric_value_double, metric_value_text, value_metadata = _coerce_value(value)
            metadata = {
                "quality_reason": record.get("quality_reason"),
                "automation_gate": record.get("automation_gate"),
                "quality_details": details,
                "raw_value": value if value_metadata else None,
            }
            metadata = {k: v for k, v in metadata.items() if v not in (None, {}, [])}
            row = SensorReadingRecord(
                measured_at=measured_at,
                ingested_at=ingested_at,
                site_id=site_id,
                zone_id=zone_id,
                record_kind=kind,
                source_id=source_id,
                source_type=source_type,
                metric_name=str(metric_name),
                metric_value_double=metric_value_double,
                metric_value_text=metric_value_text,
                unit=None,
                quality_flag=quality_flag,
                transport_status=transport_status,
                binding_group_id=binding_group_id,
                parser_id=parser_id,
                calibration_version=calibration_version,
                source=source,
                metadata_json=json.dumps(metadata, ensure_ascii=False, default=str),
            )
            broadcast = {
                "measured_at": measured_at.isoformat() if measured_at else None,
                "site_id": site_id,
                "zone_id": zone_id,
                "record_kind": kind,
                "source_id": source_id,
                "source_type": source_type,
                "metric_name": str(metric_name),
                "value_double": metric_value_double,
                "value_text": metric_value_text,
                "quality_flag": quality_flag,
            }
            yield row, broadcast


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(tz=None).replace(tzinfo=None)
        return value
    if isinstance(value, str) and value:
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            return parsed.astimezone(tz=None).replace(tzinfo=None)
        return parsed
    return None


def _coerce_value(value: Any) -> tuple[float | None, str | None, bool]:
    """Return (numeric, text, has_metadata) tuple for a raw metric value."""
    if isinstance(value, bool):
        return (1.0 if value else 0.0, None, False)
    if isinstance(value, (int, float)):
        return (float(value), None, False)
    if isinstance(value, str):
        try:
            return (float(value), None, False)
        except ValueError:
            return (None, value, False)
    if value is None:
        return (None, None, False)
    return (None, None, True)
