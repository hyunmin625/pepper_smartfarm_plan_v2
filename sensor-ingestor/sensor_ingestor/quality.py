from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SensorHistoryEntry:
    last_measured_at: str
    last_numeric_value: float | None
    same_value_count: int


@dataclass
class QualityAssessment:
    quality_flag: str
    quality_reason: str
    automation_gate: str
    details: dict[str, Any]


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_primary_numeric_value(values: dict[str, Any]) -> float | None:
    for value in values.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def select_any_value(values: dict[str, Any]) -> Any:
    for value in values.values():
        if value is not None:
            return value
    return None


def pct_delta(current: float, previous: float) -> float:
    baseline = max(abs(previous), 1e-6)
    return abs(current - previous) / baseline * 100.0


def evaluate_sensor_quality(
    *,
    measured_at: str,
    values: dict[str, Any],
    rule_set: dict[str, Any],
    sample_interval_seconds: int,
    previous: SensorHistoryEntry | None,
    transport_status: str = "ok",
    calibration_due: bool = False,
) -> tuple[QualityAssessment, SensorHistoryEntry]:
    current_any_value = select_any_value(values)
    current_numeric_value = select_primary_numeric_value(values)
    details: dict[str, Any] = {
        "transport_status": transport_status,
        "sample_interval_seconds": sample_interval_seconds,
    }

    if current_any_value is None:
        assessment = QualityAssessment("bad", "missing", "blocked", details)
    elif transport_status != "ok":
        assessment = QualityAssessment("bad", "communication_loss", "blocked", details)
    elif calibration_due:
        assessment = QualityAssessment("partial", "calibration_due", "degraded", details)
    elif previous is not None:
        stale_seconds = (parse_iso(measured_at) - parse_iso(previous.last_measured_at)).total_seconds()
        details["stale_seconds"] = stale_seconds
        if stale_seconds > rule_set.get("bad_after_seconds", 0):
            assessment = QualityAssessment("bad", "stale", "blocked", details)
        else:
            assessment = _evaluate_value_rules(
                current_numeric_value=current_numeric_value,
                rule_set=rule_set,
                sample_interval_seconds=sample_interval_seconds,
                previous=previous,
                details=details,
            )
    else:
        assessment = _evaluate_value_rules(
            current_numeric_value=current_numeric_value,
            rule_set=rule_set,
            sample_interval_seconds=sample_interval_seconds,
            previous=None,
            details=details,
        )

    same_value_count = 1
    if previous is not None and current_numeric_value is not None and previous.last_numeric_value == current_numeric_value:
        same_value_count = previous.same_value_count + 1
    next_history = SensorHistoryEntry(
        last_measured_at=measured_at,
        last_numeric_value=current_numeric_value,
        same_value_count=same_value_count,
    )
    return assessment, next_history


def _evaluate_value_rules(
    *,
    current_numeric_value: float | None,
    rule_set: dict[str, Any],
    sample_interval_seconds: int,
    previous: SensorHistoryEntry | None,
    details: dict[str, Any],
) -> QualityAssessment:
    allowed_range = rule_set.get("allowed_range")
    if allowed_range and current_numeric_value is not None:
        minimum = allowed_range["min"]
        maximum = allowed_range["max"]
        if current_numeric_value < minimum or current_numeric_value > maximum:
            details["allowed_range"] = allowed_range
            details["current_numeric_value"] = current_numeric_value
            return QualityAssessment("bad", "outlier", "blocked", details)

    if previous is not None and current_numeric_value is not None and previous.last_numeric_value is not None:
        jump_threshold_pct = rule_set.get("jump_threshold_pct")
        if isinstance(jump_threshold_pct, (int, float)):
            current_delta_pct = pct_delta(current_numeric_value, previous.last_numeric_value)
            details["jump_delta_pct"] = current_delta_pct
            if current_delta_pct > jump_threshold_pct:
                return QualityAssessment("partial", "jump", "degraded", details)

        flatline_window_seconds = rule_set.get("flatline_window_seconds")
        if isinstance(flatline_window_seconds, int) and current_numeric_value == previous.last_numeric_value:
            held_seconds = (previous.same_value_count + 1) * sample_interval_seconds
            details["flatline_held_seconds"] = held_seconds
            if held_seconds >= flatline_window_seconds:
                return QualityAssessment("partial", "flatline", "degraded", details)

    return QualityAssessment("good", "within_expected_range", "allowed", details)


def evaluate_device_quality(
    *,
    readback: dict[str, Any],
    transport_status: str = "ok",
) -> QualityAssessment:
    details = {"transport_status": transport_status}
    if transport_status != "ok":
        return QualityAssessment("bad", "communication_loss", "blocked", details)
    if readback.get("fault_state") in {True, "fault"}:
        return QualityAssessment("bad", "device_fault", "blocked", details)
    if readback.get("run_state") == "unknown":
        return QualityAssessment("partial", "unknown_state", "degraded", details)
    return QualityAssessment("good", "readback_ok", "allowed", details)
