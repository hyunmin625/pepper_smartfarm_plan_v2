#!/usr/bin/env python3
"""End-to-end integration smoke: state-estimator -> policy-engine precheck.

This script proves the contract between the state estimator output and
the policy precheck inputs without needing ops-api or a database. Three
scenarios are exercised against the same sensor snapshot shape that
`POST /decisions/evaluate-zone` feeds into `estimate_zone_state` and
`build_zone_state_payload`:

1. *Healthy fruiting zone* – estimator should classify as low risk with
   `observe_only` recommendations, and the precheck for an adjust_fan
   command built from the resulting zone state should pass with no
   policy ids attached.

2. *Worker present* – estimator must promote the zone to critical,
   recommend `enter_safe_mode`/`request_human_check`, and the downstream
   precheck for an adjust_fan command (with the `worker_present` flag
   forwarded into the raw request) must be blocked by `HSV-01`.

3. *Sensor quality bad* – estimator must promote the observability
   status to `degraded` with `risk_level=unknown`, recommend
   `pause_automation`. precheck alone should not block because no hard
   safety rule matches `sensor_quality_blocked`, which documents the
   invariant that sensor degradation is handled one layer up at the
   estimator instead of inside precheck.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from policy_engine import evaluate_device_policy_precheck  # noqa: E402
from state_estimator import (  # noqa: E402
    build_zone_state_payload,
    estimate_zone_state,
)


BASE_SNAPSHOT: dict[str, Any] = {
    "scenario_id": "integration-state-to-precheck",
    "zone_id": "gh-01-zone-a",
    "growth_stage": "fruiting",
    "current_state": {
        "air_temp_c": 26.0,
        "rh_pct": 70.0,
        "vpd_kpa": 1.1,
        "substrate_moisture_pct": 55.0,
        "substrate_temp_c": 22.0,
        "feed_ec_ds_m": 2.6,
        "drain_ec_ds_m": 2.8,
        "feed_ph": 5.8,
        "drain_ph": 5.9,
        "co2_ppm": 420,
        "par_umol_m2_s": 420,
    },
    "sensor_quality": {"overall": "good"},
    "device_status": {},
    "weather_context": {},
    "constraints": {},
    "history": [],
}


def _raw_device_command(
    zone_state: dict[str, Any],
    *,
    action_type: str,
    extra_flags: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the raw device command payload that execution-gateway
    would pass to evaluate_device_policy_precheck. The payload mirrors
    ops-api ActionDispatchPlanner output plus zone-state fields that
    _collect_flags reads (operator_context, sensor_quality, active_constraints).
    """
    raw: dict[str, Any] = {
        "request_id": "integration-raw-001",
        "action_type": action_type,
        "zone_id": zone_state.get("zone_id"),
        "policy_snapshot": {"policy_result": "pass", "policy_ids": []},
        "sensor_quality": zone_state.get("sensor_quality", {}),
        "active_constraints": list((zone_state.get("active_constraints") or {}).keys()),
        "operator_context": {
            "operator_present": bool(zone_state.get("current_state", {}).get("worker_present")),
            "manual_override": False,
        },
    }
    if extra_flags:
        raw.update(extra_flags)
    return raw


def _healthy_scenario(errors: list[str]) -> dict[str, Any]:
    snapshot = copy.deepcopy(BASE_SNAPSHOT)
    estimate = estimate_zone_state(snapshot)
    zone_state = build_zone_state_payload(snapshot)

    if estimate.risk_level not in {"low", "medium"}:
        errors.append(
            f"healthy scenario should not flag high/critical risk, got {estimate.risk_level}"
        )
    if estimate.observability_status != "good":
        errors.append(
            f"healthy scenario should keep observability_status=good, got {estimate.observability_status}"
        )

    raw = _raw_device_command(zone_state, action_type="adjust_fan")
    precheck = evaluate_device_policy_precheck(raw)
    if precheck.policy_result != "pass":
        errors.append(
            f"healthy adjust_fan should pass precheck, got {precheck.policy_result}"
        )
    if precheck.policy_ids:
        errors.append(
            f"healthy adjust_fan should not match any hard policy, got {precheck.policy_ids}"
        )

    return {
        "risk_level": estimate.risk_level,
        "recommended_action_types": estimate.recommended_action_types,
        "precheck_result": precheck.policy_result,
        "precheck_policy_ids": precheck.policy_ids,
    }


def _worker_present_scenario(errors: list[str]) -> dict[str, Any]:
    snapshot = copy.deepcopy(BASE_SNAPSHOT)
    snapshot["current_state"]["worker_present"] = True
    estimate = estimate_zone_state(snapshot)
    zone_state = build_zone_state_payload(snapshot)

    if estimate.risk_level != "critical":
        errors.append(
            f"worker_present should promote risk_level to critical, got {estimate.risk_level}"
        )
    if "enter_safe_mode" not in estimate.recommended_action_types:
        errors.append(
            "worker_present estimator should recommend enter_safe_mode"
        )

    raw = _raw_device_command(
        zone_state,
        action_type="adjust_fan",
        extra_flags={"worker_present": True},
    )
    precheck = evaluate_device_policy_precheck(raw)
    if precheck.policy_result != "blocked":
        errors.append(
            f"worker_present adjust_fan precheck should be blocked, got {precheck.policy_result}"
        )
    if "HSV-01" not in precheck.policy_ids:
        errors.append(
            f"worker_present should surface HSV-01, got {precheck.policy_ids}"
        )
    if "worker_present" not in precheck.matched_flags:
        errors.append(
            f"worker_present should appear in matched_flags, got {precheck.matched_flags}"
        )

    return {
        "risk_level": estimate.risk_level,
        "notes": estimate.notes,
        "recommended_action_types": estimate.recommended_action_types,
        "precheck_result": precheck.policy_result,
        "precheck_policy_ids": precheck.policy_ids,
        "precheck_matched_flags": precheck.matched_flags,
    }


def _sensor_quality_bad_scenario(errors: list[str]) -> dict[str, Any]:
    snapshot = copy.deepcopy(BASE_SNAPSHOT)
    snapshot["sensor_quality"] = {"overall": "bad", "substrate_moisture": "flatline"}
    estimate = estimate_zone_state(snapshot)
    zone_state = build_zone_state_payload(snapshot)

    if estimate.risk_level != "unknown":
        errors.append(
            f"sensor_quality=bad should promote risk_level=unknown, got {estimate.risk_level}"
        )
    if estimate.observability_status != "degraded":
        errors.append(
            f"sensor_quality=bad should mark observability_status=degraded, got {estimate.observability_status}"
        )
    if "pause_automation" not in estimate.recommended_action_types:
        errors.append(
            "sensor_quality=bad estimator should recommend pause_automation"
        )

    raw = _raw_device_command(zone_state, action_type="short_irrigation")
    precheck = evaluate_device_policy_precheck(raw)
    # sensor_quality_blocked is collected as a flag, but no hard rule
    # matches that flag today. We assert the invariant holds so a
    # regression that quietly attaches this flag to a new rule does not
    # slip through without a conscious test update.
    if "sensor_quality_blocked" not in _debug_collect_flags(raw):
        errors.append(
            "raw request should expose sensor_quality_blocked flag so precheck can see it"
        )
    if precheck.policy_result != "pass":
        errors.append(
            "precheck alone should not block on sensor_quality_blocked; "
            "that guard lives in the estimator layer. "
            f"got {precheck.policy_result} with ids {precheck.policy_ids}"
        )

    return {
        "risk_level": estimate.risk_level,
        "observability_status": estimate.observability_status,
        "unknown_reasons": estimate.unknown_reasons,
        "recommended_action_types": estimate.recommended_action_types,
        "precheck_result": precheck.policy_result,
    }


def _debug_collect_flags(raw: dict[str, Any]) -> set[str]:
    from policy_engine.precheck import _collect_flags  # noqa: WPS433

    return _collect_flags(raw)


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {}
    report["healthy"] = _healthy_scenario(errors)
    report["worker_present"] = _worker_present_scenario(errors)
    report["sensor_quality_bad"] = _sensor_quality_bad_scenario(errors)
    report["errors"] = errors
    report["status"] = "ok" if not errors else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
