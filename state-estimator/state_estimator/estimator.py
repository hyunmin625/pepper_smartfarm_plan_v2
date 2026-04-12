from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
HIGH_RISK_FEATURE_KEYS = {
    "heat_risk",
    "fruit_burn_risk",
    "water_stress_risk",
    "disease_pressure",
    "condensation_risk",
    "solar_gain_risk",
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
        }


def estimate_zone_state(scenario: dict[str, Any]) -> StateEstimate:
    scenario_id = str(scenario.get("scenario_id") or "unknown-scenario")
    zone_id = str(scenario.get("zone_id") or "unknown-zone")
    growth_stage = str(scenario.get("growth_stage") or "unknown")
    sensor_quality = scenario.get("sensor_quality")
    current_state = scenario.get("current_state")
    derived_features = scenario.get("derived_features")
    expected_focus = scenario.get("expected_focus")

    sensor_quality = sensor_quality if isinstance(sensor_quality, dict) else {}
    current_state = current_state if isinstance(current_state, dict) else {}
    derived_features = derived_features if isinstance(derived_features, dict) else {}
    expected_focus = expected_focus if isinstance(expected_focus, list) else []

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

    if str(derived_features.get("automation_confidence") or "") == "unsafe":
        unknown_reasons.append("derived_features.automation_confidence=unsafe")

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
        )

    if derived_features.get("safe_mode_entry") == "required":
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="limited",
            risk_level="critical",
            recommended_action_types=["enter_safe_mode", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["safe_mode_entry_required"],
        )

    if derived_features.get("robot_safety_breach") is True:
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="critical",
            recommended_action_types=["enter_safe_mode", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["robot_safety_breach"],
        )

    if current_state.get("manual_override") is True and current_state.get("operator_present") is True:
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="critical",
            recommended_action_types=["pause_automation", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["manual_override_active"],
        )

    for key in sorted(HIGH_RISK_FEATURE_KEYS):
        if derived_features.get(key) == "critical":
            return StateEstimate(
                scenario_id=scenario_id,
                zone_id=zone_id,
                growth_stage=growth_stage,
                observability_status="good",
                risk_level="critical",
                recommended_action_types=["create_alert", "request_human_check"],
                unknown_reasons=[],
                notes=notes + [f"{key}=critical"],
            )
        if derived_features.get(key) == "high":
            return StateEstimate(
                scenario_id=scenario_id,
                zone_id=zone_id,
                growth_stage=growth_stage,
                observability_status="good",
                risk_level="high",
                recommended_action_types=["create_alert", "request_human_check"],
                unknown_reasons=[],
                notes=notes + [f"{key}=high"],
            )

    if any(isinstance(item, str) and item in {"create_alert", "request_human_check"} for item in expected_focus):
        return StateEstimate(
            scenario_id=scenario_id,
            zone_id=zone_id,
            growth_stage=growth_stage,
            observability_status="good",
            risk_level="medium",
            recommended_action_types=["create_alert", "request_human_check"],
            unknown_reasons=[],
            notes=notes + ["expected_focus_requires_manual_review"],
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
    )
