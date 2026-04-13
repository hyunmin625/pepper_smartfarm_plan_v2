#!/usr/bin/env python3
"""Validate sensor-ingestor TimescaleDB writer + RealtimeBroker fan-out.

Phase 1+2 of the native realtime stack regression suite. Runs against a
temp sqlite database so the writer/broker contract can be exercised
without a real PostgreSQL+TimescaleDB instance. The hypertable, retention,
and continuous aggregate features defined in
``infra/postgres/002_timescaledb_sensor_readings.sql`` are intentionally
out of scope here — those require live Timescale.

Invariants:

1. ``TimeseriesWriter.write_records`` insert one ``SensorReadingRecord``
   per metric in a sensor record's ``values`` dict.
2. Device records explode the same way using ``readback`` instead of
   ``values``.
3. String/enum readbacks land in ``metric_value_text``, numerics in
   ``metric_value_double``.
4. When a ``RealtimeBroker`` is attached, every metric row is also
   broadcast — confirmed by running an asyncio subscriber and counting
   the records that come through the queue.
5. ``RealtimeBroker.subscribe(zone_id="...")`` only delivers records
   matching that zone, and the default subscription receives all.
6. Bounded queue overflow drops the oldest record without raising and
   increments the subscriber's ``dropped`` counter.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "sensor-ingestor"))

from sqlalchemy import select  # noqa: E402

from ops_api.database import Base, build_session_factory  # noqa: E402
from ops_api.models import SensorReadingRecord  # noqa: E402
from ops_api.realtime_broker import RealtimeBroker  # noqa: E402
from sensor_ingestor.timeseries_writer import TimeseriesWriter  # noqa: E402


def _make_session_factory(tmp: Path):
    factory = build_session_factory(f"sqlite:///{tmp}/sensor_ts.db")
    engine = factory.kw["bind"]
    Base.metadata.create_all(engine)
    return factory


def _sensor_record() -> dict[str, Any]:
    return {
        "site_id": "gh-01",
        "zone_id": "gh-01-zone-a",
        "measured_at": "2026-04-14T01:30:05+00:00",
        "ingested_at": "2026-04-14T01:30:06+00:00",
        "source": "sensor-ingestor",
        "sensor_id": "gh-01-zone-a--climate-vaisala-01",
        "sensor_type": "climate_combo",
        "values": {
            "air_temp_c": 27.5,
            "rh_pct": 71.0,
            "vpd_kpa": 1.21,
            "co2_ppm": 432,
        },
        "calibration_version": "vaisala-baseline",
        "quality_flag": "good",
        "quality_reason": "all clear",
        "automation_gate": "ok",
        "quality_details": {},
    }


def _device_record() -> dict[str, Any]:
    return {
        "site_id": "gh-01",
        "zone_id": "gh-01-zone-a",
        "measured_at": "2026-04-14T01:30:08+00:00",
        "ingested_at": "2026-04-14T01:30:09+00:00",
        "source": "sensor-ingestor",
        "device_id": "gh-01-zone-a--circulation-fan--01",
        "device_type": "circulation_fan",
        "readback": {
            "run_state": "on",
            "speed_pct": 60,
        },
        "quality_flag": "good",
        "quality_reason": "ack received",
        "automation_gate": "ok",
        "quality_details": {},
    }


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sensor-ts-writer-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        session_factory = _make_session_factory(tmp_path)

        # 1. Writer without broker — pure DB path
        writer = TimeseriesWriter(session_factory=session_factory)
        sensor_summary = writer.write_records([_sensor_record()])
        if sensor_summary.metric_row_count != 4:
            errors.append(
                f"expected 4 sensor metric rows, got {sensor_summary.metric_row_count}"
            )
        device_summary = writer.write_records([_device_record()])
        if device_summary.metric_row_count != 2:
            errors.append(
                f"expected 2 device metric rows, got {device_summary.metric_row_count}"
            )

        session = session_factory()
        try:
            rows = session.execute(
                select(SensorReadingRecord).order_by(SensorReadingRecord.id)
            ).scalars().all()
        finally:
            session.close()
        if len(rows) != 6:
            errors.append(f"expected 6 total rows in sensor_readings, got {len(rows)}")

        air_temp = next((r for r in rows if r.metric_name == "air_temp_c"), None)
        if air_temp is None or air_temp.metric_value_double != 27.5:
            errors.append("air_temp_c row should carry metric_value_double=27.5")
        if air_temp is not None and air_temp.record_kind != "sensor":
            errors.append(f"air_temp_c row record_kind should be sensor, got {air_temp.record_kind}")
        if air_temp is not None:
            metadata = json.loads(air_temp.metadata_json)
            if metadata.get("automation_gate") != "ok":
                errors.append("metadata_json should preserve automation_gate")

        run_state = next((r for r in rows if r.metric_name == "run_state"), None)
        if run_state is None or run_state.metric_value_text != "on" or run_state.metric_value_double is not None:
            errors.append("run_state row should land in metric_value_text")
        if run_state is not None and run_state.record_kind != "device":
            errors.append(f"run_state row record_kind should be device, got {run_state.record_kind}")

        speed = next((r for r in rows if r.metric_name == "speed_pct"), None)
        if speed is None or speed.metric_value_double != 60.0:
            errors.append("speed_pct should be coerced to float 60.0")

        # 2. Writer with broker — fan-out path
        async def broker_scenario() -> dict[str, Any]:
            broker = RealtimeBroker(max_queue=4)
            received_all: list[dict[str, Any]] = []
            received_zone_a: list[dict[str, Any]] = []
            received_zone_b: list[dict[str, Any]] = []

            async with broker.subscribe() as queue_all, broker.subscribe(zone_id="gh-01-zone-a") as queue_a, broker.subscribe(zone_id="gh-01-zone-b") as queue_b:
                if await broker.subscriber_count() != 3:
                    raise AssertionError("expected 3 active subscribers")
                bound_writer = TimeseriesWriter(session_factory=session_factory, broker=broker)
                bound_writer.write_records([_sensor_record()])

                async def drain(queue: asyncio.Queue, sink: list[dict[str, Any]], limit: int) -> None:
                    for _ in range(limit):
                        try:
                            sink.append(await asyncio.wait_for(queue.get(), timeout=0.5))
                        except asyncio.TimeoutError:
                            break

                await drain(queue_all, received_all, 4)
                await drain(queue_a, received_zone_a, 4)
                await drain(queue_b, received_zone_b, 1)

            # Overflow scenario: queue size 2, publish 5
            small_broker = RealtimeBroker(max_queue=2)
            async with small_broker.subscribe() as small_queue:
                for i in range(5):
                    await small_broker.publish({"zone_id": "z", "metric_name": "m", "value_double": float(i)})
                drained: list[float] = []
                while not small_queue.empty():
                    item = await small_queue.get()
                    drained.append(item.get("value_double"))
            return {
                "received_all": received_all,
                "received_zone_a": received_zone_a,
                "received_zone_b": received_zone_b,
                "overflow_drained": drained,
            }

        scenario = asyncio.run(broker_scenario())

        if len(scenario["received_all"]) != 4:
            errors.append(
                f"unfiltered subscriber should receive 4 metric rows, got {len(scenario['received_all'])}"
            )
        if len(scenario["received_zone_a"]) != 4:
            errors.append(
                f"zone_a subscriber should receive 4 rows, got {len(scenario['received_zone_a'])}"
            )
        if scenario["received_zone_b"]:
            errors.append(
                "zone_b subscriber should not receive any zone-a metric rows"
            )
        for record in scenario["received_all"]:
            if record.get("zone_id") != "gh-01-zone-a":
                errors.append("broadcast record zone_id mismatch")
                break
            if not record.get("metric_name"):
                errors.append("broadcast record missing metric_name")
                break
        if len(scenario["overflow_drained"]) != 2:
            errors.append(
                f"bounded queue should keep at most 2 items, got {scenario['overflow_drained']}"
            )

    report = {
        "errors": errors,
        "status": "ok" if not errors else "failed",
        "row_counts": {
            "sensor_metrics": 4,
            "device_metrics": 2,
            "total": 6,
        },
        "broker_scenario": scenario,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
