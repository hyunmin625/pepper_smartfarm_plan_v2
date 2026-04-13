#!/usr/bin/env python3
"""Validate /zones/{zone_id}/history sensor_series + dashboard sparkline hook.

Three invariants are covered:

1. An empty database returns ``sensor_series: {}`` and ``decisions: []``
   so the dashboard renders a "데이터 없음" placeholder instead of
   crashing the sparkline renderer.
2. After two ``POST /decisions/evaluate-zone`` calls with distinct
   current_state values, the response exposes a time-ordered
   ``sensor_series`` dict containing at least ``air_temp_c`` and
   ``rh_pct`` entries, each with ``t``, ``value``, ``decision_id`` keys.
3. ``GET /dashboard`` serves HTML that wires ``renderZoneHistory``
   against ``sensor_series``, so a regression that removes the chart
   card fails the smoke instead of silently breaking the UI.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path}/ops_api.db",
        runtime_mode_path=tmp_path / "runtime_mode.json",
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_path / "shadow.jsonl",
        validator_audit_log_path=tmp_path / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
    )


def _evaluate_zone(client: TestClient, request_id: str, current_state: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "request_id": request_id,
        "zone_id": "gh-01-zone-a",
        "task_type": "action_recommendation",
        "growth_stage": "fruiting",
        "current_state": current_state,
        "sensor_quality": {"overall": "good"},
    }
    # auth_mode=disabled trusts x-actor-role headers; the evaluate_zone
    # permission only lives on the ``service`` role today.
    response = client.post(
        "/decisions/evaluate-zone",
        json=payload,
        headers={"x-actor-id": "zone-history-smoke", "x-actor-role": "service"},
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    with tempfile.TemporaryDirectory(prefix="ops-api-zone-history-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        client = TestClient(app)

        empty_history = client.get("/zones/gh-01-zone-a/history")
        empty_history.raise_for_status()
        empty_body = empty_history.json()
        empty_data = empty_body.get("data") or {}
        if empty_data.get("sensor_series") != {}:
            errors.append(
                f"empty history should expose sensor_series={{}}, got {empty_data.get('sensor_series')!r}"
            )
        if empty_data.get("decisions") != []:
            errors.append("empty history should expose decisions=[] before any decisions are recorded")

        first_state = {
            "air_temp_c": 26.0,
            "rh_pct": 70.0,
            "vpd_kpa": 1.1,
            "substrate_moisture_pct": 55.0,
            "co2_ppm": 420,
        }
        second_state = {
            "air_temp_c": 28.5,
            "rh_pct": 75.0,
            "vpd_kpa": 1.0,
            "substrate_moisture_pct": 52.0,
            "co2_ppm": 440,
        }
        _evaluate_zone(client, "history-smoke-001", first_state)
        _evaluate_zone(client, "history-smoke-002", second_state)

        history = client.get("/zones/gh-01-zone-a/history?limit=30")
        history.raise_for_status()
        history_body = history.json()
        data = history_body.get("data") or {}
        sensor_series = data.get("sensor_series") or {}
        required_metrics = ("air_temp_c", "rh_pct", "vpd_kpa", "substrate_moisture_pct", "co2_ppm")
        for metric in required_metrics:
            if metric not in sensor_series:
                errors.append(f"sensor_series missing {metric}")
                continue
            points = sensor_series[metric]
            if len(points) < 2:
                errors.append(f"{metric} should accumulate >=2 points, got {len(points)}")
                continue
            for point in points:
                if not {"t", "value", "decision_id"}.issubset(point.keys()):
                    errors.append(f"{metric} point missing required keys: {point}")
                    break
            timestamps = [p["t"] for p in points]
            if timestamps != sorted(timestamps):
                errors.append(f"{metric} points should be time-ordered, got {timestamps}")

        air_temp_values = [p["value"] for p in sensor_series.get("air_temp_c", [])]
        if air_temp_values != [first_state["air_temp_c"], second_state["air_temp_c"]]:
            errors.append(
                f"air_temp_c values should reflect both evaluate-zone calls, got {air_temp_values}"
            )

        dashboard_html = client.get("/dashboard")
        dashboard_html.raise_for_status()
        html = dashboard_html.text
        # Phase 4 replaced the sparkline view with a uPlot + SSE based realtime
        # chart. The /zones/{id}/history endpoint still serves sensor_series for
        # offline tools, so we keep the endpoint check above and update the
        # dashboard hook list to the new realtime renderer surface.
        required_hooks = (
            "Zone Realtime Chart",
            "zoneHistoryCharts",
            "refreshZoneHistory",
            "bootstrapTimeseries",
            "openStream",
            "TRACKED_METRICS",
            "historyWindow",
            "uPlot",
        )
        for hook in required_hooks:
            if hook not in html:
                errors.append(f"dashboard HTML missing hook {hook!r}")

        report = {
            "errors": errors,
            "status": "ok" if not errors else "failed",
            "sensor_series_metrics": sorted(sensor_series.keys()),
            "series_point_counts": {metric: len(points) for metric, points in sensor_series.items()},
            "air_temp_c_values": air_temp_values,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
