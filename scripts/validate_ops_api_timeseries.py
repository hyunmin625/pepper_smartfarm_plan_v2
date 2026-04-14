#!/usr/bin/env python3
"""Validate /zones/{zone_id}/timeseries endpoint.

Phase 3 of the native realtime stack regression suite. Seeds
sensor_readings via the TimeseriesWriter, then queries the new
endpoint with raw / 1m / 5m / 30m intervals and asserts the routing,
metric filter, time bounds, and permission gates behave as documented
in docs/native_realtime_dashboard_plan.md.

Invariants:

1. interval=raw returns one point per sensor_reading row.
2. interval=1m / 5m / 30m groups rows into time buckets and exposes
   avg / min / max / sample_count fields per bucket.
3. metric=air_temp_c filters the response to that metric only.
4. from / to bounds clamp the result set.
5. Invalid interval returns 400.
6. from >= to returns 400.
7. read_runtime permission gate fires (no x-api-key under
   header_token mode -> 401, viewer token -> 200).
"""

from __future__ import annotations

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

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
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
    )


def _seed_records(writer: TimeseriesWriter, *, base: datetime) -> int:
    records = []
    for offset in range(0, 600, 30):  # 600 seconds, 1 sample per 30s = 20 samples
        records.append(
            {
                "site_id": "gh-01",
                "zone_id": "gh-01-zone-a",
                "measured_at": (base + timedelta(seconds=offset)).isoformat(),
                "ingested_at": (base + timedelta(seconds=offset, milliseconds=200)).isoformat(),
                "source": "sensor-ingestor",
                "sensor_id": "gh-01-zone-a--climate-vaisala-01",
                "sensor_type": "climate_combo",
                "values": {
                    "air_temp_c": 25.0 + (offset / 30.0) * 0.5,
                    "rh_pct": 70.0 + (offset / 30.0) * 0.2,
                },
                "calibration_version": "vaisala-baseline",
                "quality_flag": "good",
                "quality_reason": "all clear",
                "automation_gate": "ok",
                "quality_details": {},
            }
        )
    summary = writer.write_records(records)
    return summary.metric_row_count


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    with tempfile.TemporaryDirectory(prefix="ops-api-timeseries-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        client = TestClient(app)

        services = app.state.services
        writer = TimeseriesWriter(session_factory=services.session_factory)
        base = datetime.utcnow() - timedelta(minutes=15)
        seeded = _seed_records(writer, base=base)
        if seeded != 40:  # 20 samples * 2 metrics
            errors.append(f"writer should insert 40 metric rows, got {seeded}")

        # 1. interval=raw
        raw = client.get(f"/zones/gh-01-zone-a/timeseries?interval=raw&from={(base - timedelta(seconds=5)).isoformat()}&to={(base + timedelta(seconds=605)).isoformat()}")
        if raw.status_code != 200:
            errors.append(f"raw timeseries should 200, got {raw.status_code}")
        raw_body = (raw.json().get("data") or {})
        raw_series = raw_body.get("series") or {}
        if "air_temp_c" not in raw_series or "rh_pct" not in raw_series:
            errors.append(f"raw series should include both metrics, got {sorted(raw_series.keys())}")
        if len(raw_series.get("air_temp_c", [])) != 20:
            errors.append(
                f"raw air_temp_c should keep all 20 samples, got {len(raw_series.get('air_temp_c', []))}"
            )

        # 2. interval=1m bucketing
        one_m = client.get(f"/zones/gh-01-zone-a/timeseries?interval=1m&from={(base - timedelta(seconds=5)).isoformat()}&to={(base + timedelta(seconds=605)).isoformat()}")
        if one_m.status_code != 200:
            errors.append(f"1m timeseries should 200, got {one_m.status_code}")
        one_m_series = ((one_m.json().get("data") or {}).get("series") or {})
        air_buckets = one_m_series.get("air_temp_c", [])
        if not (8 <= len(air_buckets) <= 12):
            errors.append(
                f"1m bucketing should fold 20 samples into ~10 buckets, got {len(air_buckets)}"
            )
        if air_buckets and not {"avg", "value", "min", "max", "sample_count"}.issubset(air_buckets[0].keys() | {"value"}):
            sample_keys = set(air_buckets[0].keys())
            if not {"value", "min", "max", "sample_count"}.issubset(sample_keys):
                errors.append(
                    f"1m bucket missing aggregate keys, got {sorted(sample_keys)}"
                )

        # 3. metric filter
        filtered = client.get(
            f"/zones/gh-01-zone-a/timeseries?interval=raw&metric=air_temp_c"
            f"&from={(base - timedelta(seconds=5)).isoformat()}&to={(base + timedelta(seconds=605)).isoformat()}"
        )
        if filtered.status_code != 200:
            errors.append(f"metric filter should 200, got {filtered.status_code}")
        filtered_series = ((filtered.json().get("data") or {}).get("series") or {})
        if set(filtered_series.keys()) != {"air_temp_c"}:
            errors.append(
                f"metric filter should narrow to air_temp_c only, got {sorted(filtered_series.keys())}"
            )

        # 4. from clamp - request only the second half of the window
        clamped = client.get(
            f"/zones/gh-01-zone-a/timeseries?interval=raw"
            f"&from={(base + timedelta(seconds=300)).isoformat()}&to={(base + timedelta(seconds=605)).isoformat()}"
        )
        clamped_series = ((clamped.json().get("data") or {}).get("series") or {})
        clamped_air = clamped_series.get("air_temp_c", [])
        if not (8 <= len(clamped_air) <= 12):
            errors.append(
                f"from clamp should keep ~10 samples, got {len(clamped_air)}"
            )

        # 5. invalid interval
        bad_interval = client.get("/zones/gh-01-zone-a/timeseries?interval=2m")
        if bad_interval.status_code != 400:
            errors.append(f"invalid interval should 400, got {bad_interval.status_code}")

        # 6. from >= to
        flipped = client.get(
            f"/zones/gh-01-zone-a/timeseries?interval=raw"
            f"&from={(base + timedelta(seconds=600)).isoformat()}&to={(base).isoformat()}"
        )
        if flipped.status_code != 400:
            errors.append(f"from>=to should 400, got {flipped.status_code}")

    # 7. permission gate under header_token
    with tempfile.TemporaryDirectory(prefix="ops-api-timeseries-auth-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path, auth_mode="header_token"))
        client = TestClient(app)
        no_key = client.get("/zones/gh-01-zone-a/timeseries?interval=raw")
        if no_key.status_code != 401:
            errors.append(f"header_token without key should 401, got {no_key.status_code}")
        viewer = client.get(
            "/zones/gh-01-zone-a/timeseries?interval=raw",
            headers={"x-api-key": "viewer-demo-token"},
        )
        if viewer.status_code != 200:
            errors.append(f"viewer token should 200, got {viewer.status_code}")

    report = {
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
