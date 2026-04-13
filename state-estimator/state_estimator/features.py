from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


UNTRUSTED_SENSOR_FLAGS = {
    "bad",
    "blocked",
    "stale",
    "missing",
    "flatline",
    "communication_loss",
    "calibration_due",
    "calibration_error",
    "readback_mismatch",
    "unknown_state",
}

SUSPECT_SENSOR_FLAGS = {
    "partial",
    "degraded",
    "jump",
    "reboot_recovery",
    "readback_warning",
}


@dataclass(frozen=True)
class AggregatedSignal:
    value: float | None
    quality: str
    source_window: str | None = None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_feature_snapshot(snapshot: dict[str, Any], *, calculated_at: str | None = None) -> dict[str, Any]:
    current_state = _dict(snapshot.get("current_state"))
    history = _dict(snapshot.get("history"))
    sensor_quality = _dict(snapshot.get("sensor_quality"))
    growth_stage = str(snapshot.get("growth_stage") or "unknown")

    climate_temp = _aggregate_metric(
        history=history,
        current_state=current_state,
        metric_names=("air_temp_c", "temperature_c"),
        preferred_window="5m",
    )
    climate_rh = _aggregate_metric(
        history=history,
        current_state=current_state,
        metric_names=("rh_pct", "relative_humidity_pct", "humidity_pct"),
        preferred_window="5m",
    )
    climate_par = _aggregate_metric(
        history=history,
        current_state=current_state,
        metric_names=("par_umol_m2_s", "par"),
        preferred_window="daily",
    )
    moisture = _aggregate_metric(
        history=history,
        current_state=current_state,
        metric_names=("substrate_moisture_pct", "soil_moisture_pct"),
        preferred_window="5m",
    )
    drain_rate = _aggregate_metric(
        history=history,
        current_state=current_state,
        metric_names=("drain_rate_pct",),
        preferred_window="1h",
    )

    vpd_value = _calculate_vpd_kpa(climate_temp.value, climate_rh.value)
    dli_value = _calculate_dli_mol_m2_day(climate_par, current_state, history)
    air_temp_delta_30m = _metric_delta(
        history=history,
        current_state=current_state,
        metric_names=("air_temp_c", "temperature_c"),
        window="30m",
    )
    rh_delta_30m = _metric_delta(
        history=history,
        current_state=current_state,
        metric_names=("rh_pct", "relative_humidity_pct", "humidity_pct"),
        window="30m",
    )
    moisture_delta_30m = _metric_delta(
        history=history,
        current_state=current_state,
        metric_names=("substrate_moisture_pct", "soil_moisture_pct"),
        window="30m",
    )
    recovery_value = _calculate_post_irrigation_recovery(current_state, history)
    feed_ec = _first_number(current_state, "feed_ec_ds_m", "supply_ec_ds_m")
    drain_ec = _first_number(current_state, "drain_ec_ds_m")
    feed_ph = _first_number(current_state, "feed_ph", "supply_ph")
    drain_ph = _first_number(current_state, "drain_ph")

    condensation_risk = _condensation_risk(
        rh_pct=climate_rh.value,
        vpd_kpa=vpd_value,
        leaf_wetness_minutes=_first_number(current_state, "leaf_wetness_minutes"),
    )
    heat_risk = _heat_stress_risk(
        growth_stage=growth_stage,
        air_temp_c=climate_temp.value,
        vpd_kpa=vpd_value,
        par_umol_m2_s=_current_or_window_value(climate_par, current_state, "par_umol_m2_s"),
    )
    rootzone_risk = _rootzone_stress_risk(
        moisture_pct=moisture.value,
        moisture_delta_30m=moisture_delta_30m,
        recovery_pct=recovery_value,
        drain_rate_pct=drain_rate.value,
    )
    nutrient_risk = _nutrient_imbalance_risk(
        feed_drain_ec_gap=_gap(feed_ec, drain_ec),
        feed_drain_ph_gap=_gap(feed_ph, drain_ph),
        drain_rate_pct=drain_rate.value,
    )
    flower_fruit_risk = _flower_fruit_risk(growth_stage, heat_risk["level"], condensation_risk["level"])
    disease_score = _disease_suspicion_score(
        condensation_level=condensation_risk["level"],
        leaf_wetness_minutes=_first_number(current_state, "leaf_wetness_minutes"),
        disease_pressure=current_state.get("disease_pressure"),
    )
    overall_stress = max(
        _risk_to_score(heat_risk["level"]),
        _risk_to_score(rootzone_risk["level"]),
        disease_score,
    )
    reliability_score = _sensor_reliability_score(sensor_quality)
    automation_safety_score = _automation_safety_score(snapshot, reliability_score)
    vigor_score = max(0.0, min(1.0, 1.0 - ((overall_stress * 0.65) + ((1.0 - reliability_score) * 0.35))))
    ripeness_score = _ripeness_score(current_state)
    harvest_priority = _harvest_priority_score(current_state, ripeness_score, flower_fruit_risk["level"])

    return {
        "schema_version": "features.v1",
        "calculated_at": calculated_at or utc_now(),
        "climate": {
            "vpd_kpa": _feature_value(vpd_value, "kPa", _field_quality(sensor_quality, "temperature", "humidity"), "5m"),
            "dli_mol_m2_d": _feature_value(dli_value, "mol/m2/d", _field_quality(sensor_quality, "par", "light"), "daily"),
            "air_temperature_5m_avg_c": _feature_value(climate_temp.value, "C", climate_temp.quality, climate_temp.source_window),
            "air_temperature_30m_delta_c": _feature_value(air_temp_delta_30m, "delta_C", climate_temp.quality, "30m"),
            "relative_humidity_30m_delta_pct": _feature_value(rh_delta_30m, "delta_pct", climate_rh.quality, "30m"),
            "condensation_risk": condensation_risk,
            "heat_stress_risk": heat_risk,
        },
        "rootzone": {
            "substrate_moisture_5m_avg_pct": _feature_value(moisture.value, "pct", moisture.quality, moisture.source_window),
            "substrate_moisture_30m_delta_pct": _feature_value(moisture_delta_30m, "delta_pct", moisture.quality, "30m"),
            "post_irrigation_recovery_pct": _feature_value(
                recovery_value,
                "pct",
                _field_quality(sensor_quality, "substrate", "moisture", "rootzone"),
                "30m",
            ),
            "drain_rate_1h_avg_pct": _feature_value(
                drain_rate.value,
                "pct",
                drain_rate.quality,
                drain_rate.source_window,
            ),
            "feed_drain_ec_gap_ds_m": _feature_value(
                _gap(feed_ec, drain_ec),
                "dS/m",
                _field_quality(sensor_quality, "ec", "drain"),
                "5m",
            ),
            "feed_drain_ph_gap": _feature_value(
                _gap(feed_ph, drain_ph),
                "delta_pH",
                _field_quality(sensor_quality, "ph", "drain"),
                "5m",
            ),
            "rootzone_stress_risk": rootzone_risk,
            "nutrient_imbalance_risk": nutrient_risk,
        },
        "crop_signals": {
            "growth_vigor_score": _score_value(vigor_score, _overall_quality(sensor_quality), "derived_from_climate_rootzone"),
            "flower_fruit_risk": flower_fruit_risk,
            "ripeness_score": _score_value(ripeness_score, "good", "ripe_fruit_count_and_stage"),
            "disease_suspicion_score": _score_value(disease_score, _overall_quality(sensor_quality), "leaf_wetness_and_humidity"),
            "harvest_priority_score": _score_value(harvest_priority, "good", "ripeness_and_quality_pressure"),
        },
        "risk_scores": {
            "overall_stress_score": _score_value(overall_stress, _overall_quality(sensor_quality), "max_heat_rootzone_disease"),
            "automation_safety_score": _score_value(
                automation_safety_score,
                "good" if reliability_score >= 0.6 else "suspect",
                "sensor_reliability_and_manual_lock",
            ),
            "sensor_reliability_score": _score_value(reliability_score, "good", "sensor_quality_flags"),
        },
    }


def build_zone_state_payload(snapshot: dict[str, Any], *, calculated_at: str | None = None) -> dict[str, Any]:
    feature_snapshot = build_feature_snapshot(snapshot, calculated_at=calculated_at)
    current_state = _dict(snapshot.get("current_state"))
    device_status = _dict(snapshot.get("device_status"))
    weather_context = _dict(snapshot.get("weather_context"))
    constraints = _dict(snapshot.get("constraints"))
    return {
        "zone_id": str(snapshot.get("zone_id") or current_state.get("zone_id") or "unknown-zone"),
        "growth_stage": str(snapshot.get("growth_stage") or current_state.get("growth_stage") or "unknown"),
        "current_state": current_state,
        "derived_features": feature_snapshot,
        "device_status": device_status,
        "weather_context": weather_context,
        "constraints": constraints,
        "active_constraints": constraints,
        "sensor_quality": _dict(snapshot.get("sensor_quality")),
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_quality_flag(raw_value: Any) -> str:
    text = str(raw_value or "").strip().lower()
    if not text:
        return "missing"
    if text in UNTRUSTED_SENSOR_FLAGS:
        return "bad"
    if text in SUSPECT_SENSOR_FLAGS:
        return "suspect"
    return "good"


def _overall_quality(sensor_quality: dict[str, Any]) -> str:
    overall_flag = _normalize_quality_flag(sensor_quality.get("overall"))
    if overall_flag != "good":
        return overall_flag
    field_flags = [_normalize_quality_flag(value) for key, value in sensor_quality.items() if key != "overall"]
    if "bad" in field_flags:
        return "bad"
    if "suspect" in field_flags:
        return "suspect"
    return "good"


def _field_quality(sensor_quality: dict[str, Any], *needles: str) -> str:
    quality = "good"
    for key, value in sensor_quality.items():
        key_text = str(key).lower()
        if key == "overall":
            continue
        if any(needle in key_text for needle in needles):
            normalized = _normalize_quality_flag(value)
            if normalized == "bad":
                return "bad"
            if normalized == "suspect":
                quality = "suspect"
    return quality if quality != "good" else _overall_quality(sensor_quality)


def _aggregate_metric(
    *,
    history: dict[str, Any],
    current_state: dict[str, Any],
    metric_names: tuple[str, ...],
    preferred_window: str,
) -> AggregatedSignal:
    history_bucket = _history_bucket(history, metric_names, preferred_window)
    if history_bucket:
        values = [item for item in history_bucket if item is not None]
        if values:
            return AggregatedSignal(
                value=sum(values) / len(values),
                quality="good",
                source_window=preferred_window,
            )
    current_value = _first_number(current_state, *metric_names)
    if current_value is None:
        return AggregatedSignal(value=None, quality="missing", source_window=None)
    return AggregatedSignal(value=current_value, quality="good", source_window="current")


def _metric_delta(
    *,
    history: dict[str, Any],
    current_state: dict[str, Any],
    metric_names: tuple[str, ...],
    window: str,
) -> float | None:
    delta_field_candidates = [f"{name}_{window}_delta" for name in metric_names] + [
        f"{name}_delta_{window}" for name in metric_names
    ]
    delta_value = _first_number(current_state, *delta_field_candidates)
    if delta_value is not None:
        return delta_value

    bucket = _history_bucket(history, metric_names, window)
    current_value = _first_number(current_state, *metric_names)
    if current_value is None or not bucket:
        return None
    previous_values = [item for item in bucket if item is not None]
    if not previous_values:
        return None
    return current_value - (sum(previous_values) / len(previous_values))


def _history_bucket(history: dict[str, Any], metric_names: tuple[str, ...], window: str) -> list[float]:
    for metric_name in metric_names:
        metric_history = history.get(metric_name)
        if isinstance(metric_history, dict):
            window_values = metric_history.get(window)
            values = _numbers_from_iterable(window_values)
            if values:
                return values
        values = _numbers_from_iterable(metric_history)
        if values:
            return values
    return []


def _numbers_from_iterable(value: Any) -> list[float]:
    if isinstance(value, dict):
        if "values" in value:
            return _numbers_from_iterable(value.get("values"))
        return []
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return []
    numbers: list[float] = []
    for item in value:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            numbers.append(float(item))
        elif isinstance(item, dict):
            raw = item.get("value")
            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                numbers.append(float(raw))
    return numbers


def _first_number(container: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = container.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _current_or_window_value(signal: AggregatedSignal, current_state: dict[str, Any], key: str) -> float | None:
    current = _first_number(current_state, key)
    return current if current is not None else signal.value


def _calculate_vpd_kpa(air_temp_c: float | None, rh_pct: float | None) -> float | None:
    if air_temp_c is None or rh_pct is None:
        return None
    saturation_vapor_pressure = 0.6108 * math.exp((17.27 * air_temp_c) / (air_temp_c + 237.3))
    return round(saturation_vapor_pressure * (1 - max(0.0, min(rh_pct, 100.0)) / 100.0), 3)


def _calculate_dli_mol_m2_day(par_signal: AggregatedSignal, current_state: dict[str, Any], history: dict[str, Any]) -> float | None:
    explicit = _first_number(current_state, "dli_mol_m2_day", "dli_mol_m2_d")
    if explicit is not None:
        return explicit
    daily_samples = _history_bucket(history, ("par_umol_m2_s", "par"), "daily")
    if daily_samples:
        return round(sum(daily_samples) * 300.0 / 1_000_000.0, 3)
    if par_signal.value is None:
        return None
    daylight_hours = _first_number(current_state, "daylight_hours") or 12.0
    return round((par_signal.value * daylight_hours * 3600.0) / 1_000_000.0, 3)


def _calculate_post_irrigation_recovery(current_state: dict[str, Any], history: dict[str, Any]) -> float | None:
    explicit = _first_number(current_state, "post_irrigation_recovery_pct", "substrate_recovery_rate_pct_h")
    if explicit is not None:
        return explicit
    irrigation_window = _history_bucket(history, ("substrate_moisture_pct", "soil_moisture_pct"), "30m")
    if len(irrigation_window) < 2:
        return None
    baseline = min(irrigation_window)
    peak = max(irrigation_window)
    if peak <= 0:
        return None
    return round(max(0.0, min(100.0, ((peak - baseline) / peak) * 100.0)), 2)


def _gap(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(right - left, 3)


def _risk_value(level: str, confidence: float, reason: str) -> dict[str, Any]:
    return {
        "level": level,
        "confidence": round(max(0.0, min(confidence, 1.0)), 3),
        "reason": reason,
    }


def _score_value(score: float | None, quality: str, reason: str) -> dict[str, Any]:
    normalized_score = None if score is None else round(max(0.0, min(score, 1.0)), 3)
    return {
        "score": normalized_score,
        "quality": quality,
        "reason": reason,
    }


def _feature_value(value: float | None, unit: str, quality: str, source_window: str | None) -> dict[str, Any]:
    normalized = None if value is None else round(value, 3)
    return {
        "value": normalized,
        "unit": unit,
        "quality": quality,
        "source_window": source_window,
    }


def _risk_to_score(level: str) -> float:
    return {
        "low": 0.15,
        "medium": 0.4,
        "high": 0.7,
        "critical": 0.95,
        "unknown": 0.6,
    }.get(level, 0.4)


def _condensation_risk(*, rh_pct: float | None, vpd_kpa: float | None, leaf_wetness_minutes: float | None) -> dict[str, Any]:
    if rh_pct is None:
        return _risk_value("unknown", 0.55, "humidity_signal_missing")
    if rh_pct >= 95 and ((vpd_kpa is not None and vpd_kpa <= 0.15) or (leaf_wetness_minutes or 0) >= 90):
        return _risk_value("critical", 0.9, "very_high_humidity_and_leaf_wetness")
    if rh_pct >= 90 and ((vpd_kpa is not None and vpd_kpa <= 0.3) or (leaf_wetness_minutes or 0) >= 45):
        return _risk_value("high", 0.82, "persistent_humid_boundary_layer")
    if rh_pct >= 82:
        return _risk_value("medium", 0.68, "humid_watch")
    return _risk_value("low", 0.72, "humidity_in_control_range")


def _heat_stress_risk(
    *,
    growth_stage: str,
    air_temp_c: float | None,
    vpd_kpa: float | None,
    par_umol_m2_s: float | None,
) -> dict[str, Any]:
    if air_temp_c is None:
        return _risk_value("unknown", 0.55, "temperature_signal_missing")
    critical_threshold = 36.0 if growth_stage == "harvest_drying_storage" else 35.0
    high_threshold = 33.0 if growth_stage in {"flowering", "fruiting"} else 34.0
    if air_temp_c >= critical_threshold or ((air_temp_c >= high_threshold) and (par_umol_m2_s or 0) >= 1000):
        return _risk_value("critical", 0.9, "temperature_above_critical_threshold")
    if growth_stage in {"flowering", "fruiting"} and air_temp_c >= 30.0 and (par_umol_m2_s or 0) >= 1100:
        return _risk_value("high", 0.82, "moderate_heat_with_extreme_radiation")
    if air_temp_c >= high_threshold or ((vpd_kpa or 0) >= 1.6 and air_temp_c >= 31.0):
        return _risk_value("high", 0.84, "high_temperature_or_vpd")
    if air_temp_c >= 29.0:
        return _risk_value("medium", 0.7, "warming_trend")
    return _risk_value("low", 0.72, "temperature_within_operating_band")


def _rootzone_stress_risk(
    *,
    moisture_pct: float | None,
    moisture_delta_30m: float | None,
    recovery_pct: float | None,
    drain_rate_pct: float | None,
) -> dict[str, Any]:
    if moisture_pct is None:
        return _risk_value("unknown", 0.58, "rootzone_signal_missing")
    if moisture_pct <= 18 or (recovery_pct is not None and recovery_pct <= 10):
        return _risk_value("high", 0.82, "overdry_or_poor_recovery")
    if moisture_pct >= 68 and ((drain_rate_pct is not None and drain_rate_pct <= 4) or (moisture_delta_30m or 0) >= 6):
        return _risk_value("high", 0.84, "persistent_overwet")
    if moisture_pct <= 24 or moisture_pct >= 60:
        return _risk_value("medium", 0.72, "rootzone_watch_band")
    return _risk_value("low", 0.7, "rootzone_within_target_band")


def _nutrient_imbalance_risk(
    *,
    feed_drain_ec_gap: float | None,
    feed_drain_ph_gap: float | None,
    drain_rate_pct: float | None,
) -> dict[str, Any]:
    if feed_drain_ec_gap is None and feed_drain_ph_gap is None:
        return _risk_value("unknown", 0.55, "ec_ph_signals_missing")
    if (feed_drain_ec_gap or 0) >= 0.8 or abs(feed_drain_ph_gap or 0) >= 0.6:
        severity = "high" if (drain_rate_pct or 100) <= 10 else "medium"
        return _risk_value(severity, 0.8, "drain_gap_outside_normal_band")
    return _risk_value("low", 0.7, "nutrient_gap_stable")


def _flower_fruit_risk(growth_stage: str, heat_level: str, condensation_level: str) -> dict[str, Any]:
    if growth_stage not in {"flowering", "fruiting"}:
        return _risk_value("low", 0.68, "non_flower_fruit_stage")
    severity = max(_risk_to_score(heat_level), _risk_to_score(condensation_level))
    if severity >= 0.9:
        return _risk_value("critical", 0.86, "flower_fruit_loss_pressure_critical")
    if severity >= 0.7:
        return _risk_value("high", 0.8, "flower_fruit_loss_pressure_high")
    if severity >= 0.4:
        return _risk_value("medium", 0.72, "flower_fruit_watch")
    return _risk_value("low", 0.7, "flower_fruit_conditions_stable")


def _disease_suspicion_score(
    *,
    condensation_level: str,
    leaf_wetness_minutes: float | None,
    disease_pressure: Any,
) -> float:
    if isinstance(disease_pressure, str):
        return _risk_to_score(disease_pressure)
    base = _risk_to_score(condensation_level) * 0.65
    if leaf_wetness_minutes is None:
        return round(base, 3)
    if leaf_wetness_minutes >= 120:
        return round(min(1.0, base + 0.25), 3)
    if leaf_wetness_minutes >= 60:
        return round(min(1.0, base + 0.12), 3)
    return round(base, 3)


def _sensor_reliability_score(sensor_quality: dict[str, Any]) -> float:
    overall = _overall_quality(sensor_quality)
    if overall == "bad":
        return 0.2
    if overall == "suspect":
        return 0.55
    if overall == "missing":
        return 0.0
    return 0.9


def _automation_safety_score(snapshot: dict[str, Any], reliability_score: float) -> float:
    current_state = _dict(snapshot.get("current_state"))
    deductions = 0.0
    if current_state.get("manual_override") is True:
        deductions += 0.35
    if current_state.get("safe_mode") is True or current_state.get("estop_active") is True:
        deductions += 0.45
    if current_state.get("worker_present") is True or current_state.get("operator_present") is True:
        deductions += 0.25
    return round(max(0.0, min(1.0, reliability_score - deductions)), 3)


def _ripeness_score(current_state: dict[str, Any]) -> float:
    ripe_count = _first_number(current_state, "ripe_fruit_count", "ripe_candidate_count")
    if ripe_count is None:
        return 0.25
    if ripe_count >= 180:
        return 0.9
    if ripe_count >= 90:
        return 0.7
    if ripe_count >= 30:
        return 0.5
    return 0.25


def _harvest_priority_score(current_state: dict[str, Any], ripeness_score: float, flower_fruit_level: str) -> float:
    drying_risk = _risk_to_score(str(current_state.get("drying_risk_level") or "low"))
    pressure = max(ripeness_score, drying_risk, _risk_to_score(flower_fruit_level) * 0.8)
    return round(max(0.0, min(1.0, pressure)), 3)
