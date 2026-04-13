from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import load_enabled_policy_rules


@dataclass(frozen=True)
class PolicyPrecheckResult:
    policy_result: str
    policy_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    matched_flags: list[str] = field(default_factory=list)


def _merge_policy_result(*results: str) -> str:
    if any(result == "blocked" for result in results):
        return "blocked"
    if any(result == "approval_required" for result in results):
        return "approval_required"
    return "pass"


def _collect_flags(raw: dict[str, Any]) -> set[str]:
    flags: set[str] = set()

    operator_context = raw.get("operator_context")
    if isinstance(operator_context, dict):
        if bool(operator_context.get("operator_present")):
            flags.add("worker_present")
        if bool(operator_context.get("manual_override")) or bool(operator_context.get("manual_override_active")):
            flags.add("manual_override_active")
        if bool(operator_context.get("estop_active")):
            flags.add("estop_active")

    for field_name in ("active_interlocks", "active_constraints", "safety_interlocks", "policy_flags"):
        value = raw.get(field_name)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item.strip():
                flags.add(item.strip())

    sensor_quality = raw.get("sensor_quality")
    if isinstance(sensor_quality, dict):
        if sensor_quality.get("overall") == "bad" or sensor_quality.get("automation_gate") == "blocked":
            flags.add("sensor_quality_blocked")

    for field_name in (
        "worker_present",
        "manual_override_active",
        "safe_mode_active",
        "irrigation_path_degraded",
        "source_water_path_degraded",
        "dry_room_path_degraded",
        "climate_control_degraded",
        "rootzone_sensor_conflict",
        "zone_clearance_uncertain",
        "aisle_slip_hazard",
        "core_climate_interpretable",
        "rootzone_control_interpretable",
    ):
        if bool(raw.get(field_name)):
            flags.add(field_name)

    return flags


def _rule_matches(rule: dict[str, Any], flags: set[str]) -> tuple[bool, list[str]]:
    trigger_flags = [str(flag).strip() for flag in rule.get("trigger_flags", []) if str(flag).strip()]
    if not trigger_flags:
        return False, []
    return all(flag in flags for flag in trigger_flags), trigger_flags


def _device_rule_outcome(action_type: str, rule_id: str, mode: str, rule: dict[str, Any]) -> str:
    if mode == "approval_escalation":
        if rule_id == "HSV-09" and action_type == "adjust_fertigation":
            return "approval_required"
        return "pass"

    if mode == "rewrite_to_safe_pair":
        strip_action_types = {
            str(item).strip()
            for item in rule.get("enforcement", {}).get("strip_action_types", [])
            if str(item).strip()
        }
        if action_type in strip_action_types:
            return "blocked"
    return "pass"


def evaluate_device_policy_precheck(raw_request: dict[str, Any]) -> PolicyPrecheckResult:
    flags = _collect_flags(raw_request)
    action_type = str(raw_request.get("action_type") or "")
    snapshot = raw_request.get("policy_snapshot")
    snapshot_ids: list[str] = []
    snapshot_result = "pass"
    if isinstance(snapshot, dict):
        snapshot_ids = [str(item) for item in snapshot.get("policy_ids", []) if str(item).strip()]
        snapshot_result = str(snapshot.get("policy_result") or "pass")

    matched_ids: list[str] = list(snapshot_ids)
    reasons: list[str] = []
    matched_flags: list[str] = []
    computed_result = "pass"

    for rule in load_enabled_policy_rules(stages=("hard_safety", "output_contract")):
        rule_id = str(rule.get("rule_id") or "")
        mode = str(rule.get("enforcement", {}).get("mode") or "")
        matched, trigger_flags = _rule_matches(rule, flags)
        if not matched:
            continue
        outcome = _device_rule_outcome(action_type, rule_id, mode, rule)
        if outcome == "pass":
            continue
        if rule_id not in matched_ids:
            matched_ids.append(rule_id)
        for flag in trigger_flags:
            if flag not in matched_flags:
                matched_flags.append(flag)
        reasons.append(f"policy_precheck:{rule_id}")
        computed_result = _merge_policy_result(computed_result, outcome)

    return PolicyPrecheckResult(
        policy_result=_merge_policy_result(snapshot_result, computed_result),
        policy_ids=matched_ids,
        reasons=reasons,
        matched_flags=matched_flags,
    )


def evaluate_override_policy_precheck(raw_request: dict[str, Any]) -> PolicyPrecheckResult:
    snapshot = raw_request.get("policy_snapshot")
    snapshot_ids: list[str] = []
    snapshot_result = "pass"
    if isinstance(snapshot, dict):
        snapshot_ids = [str(item) for item in snapshot.get("policy_ids", []) if str(item).strip()]
        snapshot_result = str(snapshot.get("policy_result") or "pass")
    return PolicyPrecheckResult(
        policy_result=snapshot_result,
        policy_ids=snapshot_ids,
        reasons=[],
        matched_flags=[],
    )
