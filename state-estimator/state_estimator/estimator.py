from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .features import build_feature_snapshot, build_zone_state_payload


UNTRUSTED_QUALITY_MARKERS = {
    "stale",
    "missing",
    "flatline",
    "communication_loss",
    "calibration_due",
    "calibration_error",
    "readback_mismatch",
    "unknown_state",
}


@dataclass(frozen=True)
class StateEstimate:
    scenario_id: str
    zone_id: str
    growth_stage: str
    observability_status: str
    risk_level: str
    recommended_action_types: list[str]
    unknown_reasons: list[str]
    notes: list[str]
    feature_snapshot: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "zone_id": self.zone_id,
            "growth_stage": self.growth_stage,
            "observability_status": self.observability_status,
            "risk_level": self.risk_level,
            "recommended_action_types": self.recommended_action_types,
            "unknown_reasons": self.unknown_reasons,
            "notes": self.notes,
            "feature_snapshot": self.feature_snapshot,
        }


def estimate_zone_state(scenario: dict[str, Any]) -> StateEstimate:
    scenario_id = str(scenario.get("scenario_id") or "unknown-scenario")
    zone_id = str(scenario.get("zone_id") or "unknown-zone")
    growth_stage = str(scenario.get("growth_stage") or "unknown")
    sensor_quality = scenario.get("sensor_quality")
    current_state = scenario.get("current_state")

    sensor_quality = sensor_quality if isinstance(sensor_quality, dict) else {}
    current_state = current_state if isinstance(current_state, dict) else {}

    feature_snapshot = build_feature_snapshot(scenario)
    climate = feature_snapshot["climate"]
    rootzone = feature_snapshot["rootzone"]
    risk_scores = feature_snapshot["risk_scores"]

    unknown_reasons: list[str] = []
    notes: list[str] = []
    overall_quality = str(sensor_quality.get("overall") or "unknown")

    if overall_quality == "bad":
        unknown_reasons.append("sensor_quality.overall=bad")
    for field_name, value in sorted(sensor_quality.items()):
        if field_name == "overall":
            continue
        if isinstance(value, str) and value in UNTRUSTED_QUALITY_MARKERS:
            unknown_reasons.append(f"{field_name}={value}")

    if risk_scores["sensor_reliability_score"]["score"] is not None and risk_scores["sensor_reliability_score"]["score"] <= 0.25:
        unknown_reasons.append("sensor_reliability_score<=0.25")

    if str(current_state.get("device_state_sync") or "") == "unknown":
        notes.append("device_state_sync_unknown")

    if unknown_reasons:
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="degraded",
            risk_level="unknown",
            recommended_action_types=["pause_automation", "request_human_check"],
            unknown_reasons=unknown_reasons,
            notes=notes or ["sensor_quality_guard_promoted_unknown"],
            feature_snapshot=feature_snapshot,
        )

    if _is_hard_critical(current_state):
        note = "robot_safety_breach" if current_state.get("worker_present") and current_state.get("robot_task_state") else "hard_safety_interlock"
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="critical",
            recommended_action_types=["enter_safe_mode", "request_human_check"],
            unknown_reasons=[],
            notes=notes + [note],
            feature_snapshot=feature_snapshot,
        )

    climate_heat = climate["heat_stress_risk"]["level"]
    condensation = climate["condensation_risk"]["level"]
    rootzone_risk = rootzone["rootzone_stress_risk"]["level"]
    overall_stress = risk_scores["overall_stress_score"]["score"] or 0.0
    safety_score = risk_scores["automation_safety_score"]["score"] or 0.0

    if current_state.get("power_state") == "recovered" or _boolish(scenario, "derived_features", "safe_mode_entry"):
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="limited",
            risk_level="critical",
            recommended_action_types=["enter_safe_mode", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["safe_mode_entry_required"],
            feature_snapshot=feature_snapshot,
        )

    if climate_heat == "critical" or condensation == "critical":
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="critical",
            recommended_action_types=["create_alert", "request_human_check"],
            unknown_reasons=[],
            notes=notes + [f"critical_risk:{climate_heat}/{condensation}"],
            feature_snapshot=feature_snapshot,
        )

    if overall_stress >= 0.7 or rootzone_risk == "high" or climate_heat == "high":
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="high",
            recommended_action_types=["create_alert", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["stress_score_high"],
            feature_snapshot=feature_snapshot,
        )

    if safety_score <= 0.45 or overall_stress >= 0.4:
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="medium",
            recommended_action_types=["create_alert", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["manual_review_band"],
            feature_snapshot=feature_snapshot,
        )

    return StateEstimate(
        scenario_id=scenario_id,
        zone_id=zone_id,
        growth_stage=growth_stage,
        observability_status="good",
        risk_level="low",
        recommended_action_types=["observe_only", "trend_review"],
        unknown_reasons=[],
        notes=notes or ["stable_signal"],
        feature_snapshot=feature_snapshot,
    )


def build_state_snapshot(scenario: dict[str, Any]) -> dict[str, Any]:
    return build_zone_state_payload(scenario)


def _is_hard_critical(current_state: dict[str, Any]) -> bool:
    return (
        current_state.get("worker_present") is True
        or current_state.get("operator_present") is True
        or current_state.get("manual_override") is True
        or current_state.get("safe_mode") is True
        or current_state.get("estop_active") is True
        or _boolish({"current_state": current_state}, "current_state", "robot_safety_breach")
    )


def _boolish(container: dict[str, Any], *path: str) -> bool:
    cursor: Any = container
    for key in path:
        if not isinstance(cursor, dict):
            return False
        cursor = cursor.get(key)
    if isinstance(cursor, bool):
        return cursor
    if isinstance(cursor, str):
        return cursor.lower() in {"true", "required", "active", "yes"}
    return False
