#!/usr/bin/env python3
"""Validate dashboard section 14 completions end-to-end.

This smoke exercises the dashboard expansion described in todo.md §14:

- ``/dashboard/data`` must expose ``robot_candidates``, ``device_status``
  per zone, and ``active_constraints`` per zone after a seeded
  ``/decisions/evaluate-zone`` call.
- ``/robot/candidates`` must return seeded candidates with zone and
  status filters.
- ``/zones/{id}/history`` must include pH columns (``feed_ph``,
  ``drain_ph``) in ``sensor_series`` when the underlying decisions
  carry pH readings.
- ``GET /dashboard`` HTML must wire the new cards
  (``robotCandidateList``, ``deviceStatusList``, ``activeConstraintsList``)
  and the new action buttons (``executeAction``, ``flagCase``).
- The ``flagCase`` JS helper must hit the existing ``/shadow/reviews``
  endpoint with a ``flag:`` prefix, so this smoke also posts the same
  payload shape directly and checks it is persisted as an
  operator_review row with the flag note intact.
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
from sqlalchemy import select  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.models import OperatorReviewRecord, RobotCandidateRecord  # noqa: E402


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
        chat_provider="stub",
        chat_model_id="pepper-ops-local-stub-chat",
    )


def _service_headers() -> dict[str, str]:
    return {"x-actor-id": "dashboard-smoke", "x-actor-role": "service"}


def _evaluate(
    client: TestClient,
    request_id: str,
    *,
    current_state: dict[str, Any],
    device_status: dict[str, Any],
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> None:
    payload = {
        "request_id": request_id,
        "zone_id": "gh-01-zone-a",
        "task_type": "action_recommendation",
        "growth_stage": "fruiting",
        "current_state": current_state,
        "sensor_quality": {"overall": "good"},
        "device_status": device_status,
        "constraints": constraints,
        "candidates": candidates,
    }
    resp = client.post("/decisions/evaluate-zone", json=payload, headers=_service_headers())
    resp.raise_for_status()


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    with tempfile.TemporaryDirectory(prefix="ops-api-section14-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        client = TestClient(app)

        _evaluate(
            client,
            "section14-001",
            current_state={
                "air_temp_c": 26.0,
                "rh_pct": 70.0,
                "vpd_kpa": 1.1,
                "substrate_moisture_pct": 55.0,
                "co2_ppm": 420,
                "feed_ec_ds_m": 2.6,
                "drain_ec_ds_m": 2.8,
                "feed_ph": 5.9,
                "drain_ph": 6.0,
            },
            device_status={
                "gh-01-zone-a--circulation-fan--01": {"status": "on"},
                "gh-01-zone-a--shade-curtain--01": {"status": "closed"},
            },
            constraints={"irrigation_path_degraded": False},
            candidates=[
                {
                    "candidate_id": "gh-01-zone-a-candidate-001",
                    "candidate_type": "harvest_candidate",
                    "priority": "high",
                    "status": "observed",
                    "notes": "ripe fruit cluster",
                },
                {
                    "candidate_id": "gh-01-zone-a-candidate-002",
                    "candidate_type": "inspect_candidate",
                    "priority": "medium",
                    "status": "rejected",
                    "notes": "false positive",
                },
            ],
        )

        _evaluate(
            client,
            "section14-002",
            current_state={
                "air_temp_c": 28.5,
                "rh_pct": 72.0,
                "vpd_kpa": 1.3,
                "substrate_moisture_pct": 53.0,
                "co2_ppm": 430,
                "feed_ec_ds_m": 2.7,
                "drain_ec_ds_m": 2.9,
                "feed_ph": 5.8,
                "drain_ph": 5.95,
            },
            device_status={
                "gh-01-zone-a--circulation-fan--01": {"status": "on"},
                "gh-01-zone-a--shade-curtain--01": {"status": "open"},
            },
            constraints={"irrigation_path_degraded": True, "rootzone_sensor_conflict": False},
            candidates=[
                {
                    "candidate_id": "gh-01-zone-a-candidate-001",
                    "candidate_type": "harvest_candidate",
                    "priority": "high",
                    "status": "approved",
                    "notes": "ripe fruit cluster",
                },
            ],
        )

        dashboard = client.get("/dashboard/data")
        dashboard.raise_for_status()
        data = dashboard.json().get("data") or {}

        # Robot candidates exposed on dashboard payload. _refresh_robot_records_for_decision
        # upserts by candidate_id and only deletes rows tied to the current decision,
        # so earlier candidates remain visible until their decision is overwritten.
        candidates = data.get("robot_candidates") or []
        if not candidates:
            errors.append("dashboard payload should expose robot_candidates after evaluate-zone")
        else:
            latest = {row["candidate_id"]: row for row in candidates}
            if latest.get("gh-01-zone-a-candidate-001", {}).get("status") != "approved":
                errors.append("robot_candidates should reflect the latest status from the second evaluate call")
            if "gh-01-zone-a-candidate-002" not in latest:
                errors.append(
                    "robot_candidates should keep the earlier candidate-002 so operators can see prior rejections"
                )
            elif latest["gh-01-zone-a-candidate-002"].get("status") != "rejected":
                errors.append("candidate-002 should keep its rejected status from the first evaluate call")

        # Summary count
        summary = data.get("summary") or {}
        if summary.get("robot_candidate_count", 0) < 1:
            errors.append("summary.robot_candidate_count should be >= 1")

        # Device status and active constraints per zone
        zone_a = next((z for z in data.get("zones", []) if z.get("zone_id") == "gh-01-zone-a"), None)
        if zone_a is None:
            errors.append("zones payload missing gh-01-zone-a after evaluate-zone")
        else:
            device_status = zone_a.get("device_status") or {}
            if "gh-01-zone-a--circulation-fan--01" not in device_status:
                errors.append("zone device_status should expose circulation fan entry")
            if device_status.get("gh-01-zone-a--shade-curtain--01", {}).get("status") != "open":
                errors.append("zone device_status should reflect the latest decision snapshot")
            active_constraints = zone_a.get("active_constraints") or {}
            if active_constraints.get("irrigation_path_degraded") is not True:
                errors.append("zone active_constraints should carry irrigation_path_degraded=true")

        # /robot/candidates endpoint
        candidates_resp = client.get("/robot/candidates")
        candidates_resp.raise_for_status()
        candidate_items = (candidates_resp.json().get("data") or {}).get("items") or []
        if not candidate_items:
            errors.append("/robot/candidates should return seeded rows")
        status_filter = client.get("/robot/candidates?status=approved")
        status_filter.raise_for_status()
        filtered = (status_filter.json().get("data") or {}).get("items") or []
        if len(filtered) != 1 or filtered[0].get("candidate_id") != "gh-01-zone-a-candidate-001":
            errors.append("/robot/candidates status filter should narrow to approved candidates")

        # pH series in zone history
        history = client.get("/zones/gh-01-zone-a/history?limit=30")
        history.raise_for_status()
        series = (history.json().get("data") or {}).get("sensor_series") or {}
        if "feed_ph" not in series or "drain_ph" not in series:
            errors.append("zone sensor_series should include feed_ph and drain_ph columns")
        elif len(series["feed_ph"]) != 2 or len(series["drain_ph"]) != 2:
            errors.append("feed_ph/drain_ph should accumulate two points after two evaluate calls")

        # Dashboard HTML hooks
        dashboard_html = client.get("/dashboard")
        dashboard_html.raise_for_status()
        html = dashboard_html.text
        required_hooks = (
            "robotCandidateList",
            "deviceStatusList",
            "activeConstraintsList",
            "renderRobotCandidates",
            "renderDeviceStatus",
            "renderActiveConstraints",
            "executeAction",
            "flagCase",
            "수동 Execute",
            "문제 사례 태깅",
        )
        for hook in required_hooks:
            if hook not in html:
                errors.append(f"dashboard HTML missing hook {hook!r}")

        # flagCase end-to-end: the dashboard JS hits /shadow/reviews with a flag: prefix.
        flag_resp = client.post(
            "/shadow/reviews",
            json={
                "decision_id": 1,
                "actor_id": "dashboard-operator",
                "agreement_status": "disagree",
                "note": "flag: false positive on fan decision",
            },
        )
        flag_resp.raise_for_status()
        session = app.state.services.session_factory()
        try:
            flag_row = session.execute(
                select(OperatorReviewRecord).where(OperatorReviewRecord.decision_id == 1).order_by(
                    OperatorReviewRecord.id.desc()
                )
            ).scalars().first()
            if flag_row is None:
                errors.append("flag review should be persisted as an operator_review row")
            elif not (flag_row.note or "").startswith("flag:"):
                errors.append(
                    f"flag review should keep the 'flag:' prefix, got {flag_row.note!r}"
                )

            persisted = session.execute(select(RobotCandidateRecord)).scalars().all()
            if not persisted:
                errors.append("RobotCandidateRecord rows should be persisted by evaluate-zone")
        finally:
            session.close()

        report = {
            "errors": errors,
            "status": "ok" if not errors else "failed",
            "robot_candidate_summary": [
                {"candidate_id": c.get("candidate_id"), "status": c.get("status")}
                for c in candidate_items
            ],
            "device_status_zone_a": (zone_a or {}).get("device_status"),
            "active_constraints_zone_a": (zone_a or {}).get("active_constraints"),
            "ph_point_counts": {
                "feed_ph": len(series.get("feed_ph", [])),
                "drain_ph": len(series.get("drain_ph", [])),
            },
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
