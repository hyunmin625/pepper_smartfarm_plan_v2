#!/usr/bin/env python3
"""Validate /zones/{zone_id}/stream Server-Sent Events endpoint.

Phase 3 of the native realtime stack regression suite. Drives the SSE
endpoint by calling the FastAPI route handler directly and consuming
the StreamingResponse body iterator. This bypasses HTTP buffering so
the test can pull SSE events deterministically inside a single asyncio
loop.

Invariants:

1. The handler returns a StreamingResponse with ``Content-Type:
   text/event-stream``.
2. The body iterator emits ``event: ready`` first with zone_id +
   actor info.
3. ``event: bootstrap`` rows mirror sensor rows from the last N
   seconds.
4. ``event: bootstrap_complete`` event closes the bootstrap phase
   with a count.
5. Records published through ``RealtimeBroker.publish`` after the
   bootstrap appear as ``event: reading`` payloads in zone order.
6. Records published with a different zone_id are filtered out.
7. ``read_runtime`` permission gate fires on the HTTP layer (no key
   under header_token mode -> 401 via httpx ASGITransport).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "sensor-ingestor"))

import httpx  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.auth import ActorIdentity  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from sensor_ingestor.timeseries_writer import TimeseriesWriter  # noqa: E402


def _make_settings(tmp: Path, *, auth_mode: str = "disabled") -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp}/ops_api.db",
        runtime_mode_path=tmp / "runtime_mode.json",
        auth_mode=auth_mode,
        auth_tokens_json="",
        shadow_audit_log_path=tmp / "shadow.jsonl",
        validator_audit_log_path=tmp / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        chat_provider="stub",
        chat_model_id="pepper-ops-local-stub-chat",
    )


def _seed_bootstrap_rows(writer: TimeseriesWriter, zone: str, *, count: int) -> None:
    base = datetime.utcnow() - timedelta(seconds=120)
    records = []
    for offset in range(count):
        records.append(
            {
                "site_id": "gh-01",
                "zone_id": zone,
                "measured_at": (base + timedelta(seconds=offset * 5)).isoformat(),
                "ingested_at": (base + timedelta(seconds=offset * 5, milliseconds=200)).isoformat(),
                "source": "sensor-ingestor",
                "sensor_id": f"{zone}--climate-vaisala-01",
                "sensor_type": "climate_combo",
                "values": {"air_temp_c": 26.0 + offset * 0.1},
                "calibration_version": "vaisala-baseline",
                "quality_flag": "good",
                "quality_reason": "all clear",
                "automation_gate": "ok",
                "quality_details": {},
            }
        )
    writer.write_records(records)


def _parse_sse_buffer(buffer: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for chunk in buffer.split("\n\n"):
        chunk = chunk.strip()
        if not chunk or chunk.startswith(":"):
            continue
        event_name = "message"
        data_lines: list[str] = []
        for line in chunk.split("\n"):
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        if not data_lines:
            continue
        try:
            payload = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            payload = {"raw": "\n".join(data_lines)}
        events.append((event_name, payload))
    return events


def _resolve_stream_handler(app):
    """Locate the get_zone_stream route handler closure on the app."""
    for route in app.routes:
        if getattr(route, "path", None) == "/zones/{zone_id}/stream":
            return route.endpoint
    raise RuntimeError("/zones/{zone_id}/stream route not found")


async def _drive_stream(app, services) -> tuple[list[tuple[str, dict]], str]:
    handler = _resolve_stream_handler(app)
    actor = ActorIdentity(actor_id="smoke-actor", role="viewer", auth_mode="disabled")
    response = await handler(
        zone_id="gh-01-zone-a",
        bootstrap_seconds=300,
        services=services,
        actor=actor,
    )
    media_type = response.media_type
    body_iterator = response.body_iterator
    buffer = b""
    publisher_task: asyncio.Task | None = None
    saw_complete = False
    async for chunk in body_iterator:
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        buffer += chunk
        text = buffer.decode("utf-8", errors="ignore")
        if not saw_complete and "bootstrap_complete" in text:
            saw_complete = True
            publisher_task = asyncio.create_task(_publish_records(services.realtime_broker))
        if text.count("event: reading") >= 3:
            break
        if len(buffer) > 200000:
            break
    if publisher_task is not None and not publisher_task.done():
        with __import__("contextlib").suppress(Exception):
            await asyncio.wait_for(publisher_task, timeout=1.0)
    events = _parse_sse_buffer(buffer.decode("utf-8", errors="ignore"))
    return events, media_type


async def _publish_records(broker) -> None:
    await asyncio.sleep(0.05)
    for offset in range(3):
        await broker.publish(
            {
                "measured_at": datetime.utcnow().isoformat(),
                "site_id": "gh-01",
                "zone_id": "gh-01-zone-a",
                "record_kind": "sensor",
                "source_id": "gh-01-zone-a--climate-vaisala-01",
                "source_type": "climate_combo",
                "metric_name": "air_temp_c",
                "value_double": 27.5 + offset * 0.2,
                "value_text": None,
                "quality_flag": "good",
            }
        )
    await broker.publish(
        {
            "measured_at": datetime.utcnow().isoformat(),
            "site_id": "gh-01",
            "zone_id": "gh-01-zone-b",
            "record_kind": "sensor",
            "source_id": "gh-01-zone-b--climate-vaisala-01",
            "source_type": "climate_combo",
            "metric_name": "air_temp_c",
            "value_double": 30.0,
            "value_text": None,
            "quality_flag": "good",
        }
    )


async def _verify_auth_gate(tmp_path: Path) -> int:
    app = create_app(settings=_make_settings(tmp_path, auth_mode="header_token"))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=3.0) as client:
        no_key = await client.get("/zones/gh-01-zone-a/stream", params={"bootstrap_seconds": 0})
    return no_key.status_code


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    events: list[tuple[str, dict]] = []
    media_type = ""
    auth_status = 0

    with tempfile.TemporaryDirectory(prefix="ops-api-sse-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        services = app.state.services
        writer = TimeseriesWriter(session_factory=services.session_factory)
        _seed_bootstrap_rows(writer, "gh-01-zone-a", count=4)

        events, media_type = asyncio.run(_drive_stream(app, services))

        if media_type != "text/event-stream":
            errors.append(f"media_type should be text/event-stream, got {media_type!r}")

        first_event = events[0] if events else (None, {})
        if first_event[0] != "ready":
            errors.append(f"first event should be 'ready', got {first_event[0]!r}")
        if first_event[1].get("zone_id") != "gh-01-zone-a":
            errors.append("ready payload should expose zone_id")

        bootstrap_events = [e for e in events if e[0] == "bootstrap"]
        if len(bootstrap_events) != 4:
            errors.append(
                f"expected 4 bootstrap events from seeded rows, got {len(bootstrap_events)}"
            )

        bootstrap_complete = next((e for e in events if e[0] == "bootstrap_complete"), None)
        if bootstrap_complete is None:
            errors.append("missing bootstrap_complete event")
        elif bootstrap_complete[1].get("count") != 4:
            errors.append(
                f"bootstrap_complete count mismatch, got {bootstrap_complete[1]}"
            )

        reading_events = [e for e in events if e[0] == "reading"]
        if len(reading_events) < 3:
            errors.append(
                f"expected >=3 reading events from broker.publish, got {len(reading_events)}"
            )
        for _, payload in reading_events[:3]:
            if payload.get("zone_id") != "gh-01-zone-a":
                errors.append("reading event leaked from other zone")
                break

        zone_b_leaked = any(
            e[0] == "reading" and e[1].get("zone_id") == "gh-01-zone-b" for e in events
        )
        if zone_b_leaked:
            errors.append("zone-b broadcast must not appear on zone-a stream")

    with tempfile.TemporaryDirectory(prefix="ops-api-sse-auth-") as tmp_dir:
        auth_status = asyncio.run(_verify_auth_gate(Path(tmp_dir)))
    if auth_status != 401:
        errors.append(f"header_token without key should 401, got {auth_status}")

    report = {
        "errors": errors,
        "status": "ok" if not errors else "failed",
        "event_summary": {
            "ready_count": sum(1 for e in events if e[0] == "ready"),
            "bootstrap_count": sum(1 for e in events if e[0] == "bootstrap"),
            "bootstrap_complete_count": sum(1 for e in events if e[0] == "bootstrap_complete"),
            "reading_count": sum(1 for e in events if e[0] == "reading"),
        },
        "media_type": media_type,
        "auth_no_key_status": auth_status,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
