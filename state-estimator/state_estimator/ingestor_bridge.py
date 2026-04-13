from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .features import build_snapshot_from_raw_records, build_zone_state_from_raw_records


def load_sensor_ingestor_mqtt_outbox(path: str | Path) -> list[dict[str, Any]]:
    outbox_path = Path(path)
    rows: list[dict[str, Any]] = []
    if not outbox_path.exists():
        return rows
    with outbox_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def group_ingestor_records_by_zone(records: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        payload = record.get("payload")
        payload_dict = payload if isinstance(payload, dict) else record
        if not isinstance(payload_dict, dict):
            continue
        zone_id = str(payload_dict.get("zone_id") or "")
        if not zone_id:
            continue
        grouped[zone_id].append(record)
    return dict(grouped)


def build_snapshot_from_ingestor_outbox(
    path: str | Path,
    *,
    zone_id: str,
    growth_stage: str = "unknown",
    farm_id: str = "gh-01",
    site_id: str | None = None,
    constraints: dict[str, Any] | None = None,
    weather_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = load_sensor_ingestor_mqtt_outbox(path)
    return build_snapshot_from_raw_records(
        records,
        zone_id=zone_id,
        growth_stage=growth_stage,
        farm_id=farm_id,
        site_id=site_id,
        constraints=constraints,
        weather_context=weather_context,
    )


def build_zone_state_from_ingestor_outbox(
    path: str | Path,
    *,
    zone_id: str,
    growth_stage: str = "unknown",
    farm_id: str = "gh-01",
    site_id: str | None = None,
    constraints: dict[str, Any] | None = None,
    weather_context: dict[str, Any] | None = None,
    calculated_at: str | None = None,
) -> dict[str, Any]:
    records = load_sensor_ingestor_mqtt_outbox(path)
    return build_zone_state_from_raw_records(
        records,
        zone_id=zone_id,
        growth_stage=growth_stage,
        farm_id=farm_id,
        site_id=site_id,
        constraints=constraints,
        weather_context=weather_context,
        calculated_at=calculated_at,
    )
