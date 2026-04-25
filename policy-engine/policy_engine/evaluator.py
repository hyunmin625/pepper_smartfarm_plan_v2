from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import load_enabled_policy_rules


RUNTIME_POLICY_STAGES = (
    "hard_block",
    "approval",
    "range_limit",
    "scheduling",
    "sensor_quality",
    "robot_safety",
)

POLICY_RESULT_ORDER = {
    "pass": 0,
    "approval_required": 1,
    "blocked": 2,
}


@dataclass(frozen=True)
class PolicyRuleMatch:
    policy_id: str
    category: str
    result: str
    severity: str
    reason_code: str
    reason: str
    matched_fields: list[str] = field(default_factory=list)
    source_version: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "category": self.category,
            "result": self.result,
            "severity": self.severity,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "matched_fields": list(self.matched_fields),
            "source_version": self.source_version,
        }


@dataclass(frozen=True)
class PolicyEvaluationReport:
    policy_result: str
    policy_ids: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    matches: list[PolicyRuleMatch] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_result": self.policy_result,
            "policy_ids": list(self.policy_ids),
            "reason_codes": list(self.reason_codes),
            "reasons": list(self.reasons),
            "matches": [match.as_dict() for match in self.matches],
        }


def _merge_policy_result(*results: str) -> str:
    winner = "pass"
    for result in results:
        if POLICY_RESULT_ORDER.get(result, 0) > POLICY_RESULT_ORDER[winner]:
            winner = result
    return winner


def _runtime_value(rule: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in rule:
        return rule[key]
    enforcement = rule.get("enforcement")
    if isinstance(enforcement, dict) and key in enforcement:
        return enforcement[key]
    return default


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

    sensor_quality = raw.get("sensor_quality")
    if isinstance(sensor_quality, dict):
        if sensor_quality.get("overall") == "bad":
            flags.add("sensor_quality_bad")
        if sensor_quality.get("automation_gate") == "blocked":
            flags.add("sensor_quality_blocked")

    for field_name in ("active_interlocks", "active_constraints", "safety_interlocks", "policy_flags"):
        value = raw.get(field_name)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item.strip():
                flags.add(item.strip())

    for field_name in (
        "worker_present",
        "manual_override_active",
        "safe_mode_active",
        "estop_active",
        "irrigation_path_degraded",
        "source_water_path_degraded",
        "dry_room_path_degraded",
        "climate_control_degraded",
        "rootzone_sensor_conflict",
        "zone_clearance_uncertain",
        "aisle_slip_hazard",
    ):
        if bool(raw.get(field_name)):
            flags.add(field_name)

    return flags


def _build_context(raw: dict[str, Any]) -> dict[str, Any]:
    context = dict(raw)
    context["request"] = raw
    context["action_type"] = str(raw.get("action_type") or raw.get("override_type") or "")
    context["parameters"] = raw.get("parameters") if isinstance(raw.get("parameters"), dict) else {}
    context["zone_id"] = str(raw.get("zone_id") or raw.get("scope_id") or "")
    context["device_id"] = str(raw.get("device_id") or "")
    context["flags"] = sorted(_collect_flags(raw))

    time_context = raw.get("time_context") if isinstance(raw.get("time_context"), dict) else {}
    if "local_hour" not in context and "local_hour" in time_context:
        context["local_hour"] = time_context.get("local_hour")
    if "runtime_mode" not in context and isinstance(raw.get("runtime"), dict):
        context["runtime_mode"] = raw["runtime"].get("runtime_mode")
    return context


def _get_path(context: dict[str, Any], field_path: str) -> Any:
    if field_path in context:
        return context[field_path]
    current: Any = context
    for part in field_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _leaf_condition_matches(condition: dict[str, Any], context: dict[str, Any]) -> tuple[bool, list[str]]:
    field_path = str(condition.get("field") or "")
    if not field_path:
        return False, []
    operator = str(condition.get("operator") or "eq")
    actual = _get_path(context, field_path)
    expected = condition.get("value")
    matched = False

    if operator == "exists":
        matched = actual is not None
    elif operator == "missing":
        matched = actual is None
    elif operator == "truthy":
        matched = bool(actual)
    elif operator == "falsy":
        matched = not bool(actual)
    elif operator == "eq":
        matched = actual == expected
    elif operator == "ne":
        matched = actual != expected
    elif operator in {"gt", "gte", "lt", "lte"}:
        left = _to_float(actual)
        right = _to_float(expected)
        if left is not None and right is not None:
            if operator == "gt":
                matched = left > right
            elif operator == "gte":
                matched = left >= right
            elif operator == "lt":
                matched = left < right
            elif operator == "lte":
                matched = left <= right
    elif operator == "between":
        value = _to_float(actual)
        min_value = _to_float(condition.get("min_value"))
        max_value = _to_float(condition.get("max_value"))
        if value is not None and min_value is not None and max_value is not None:
            if bool(condition.get("wrap")) and min_value > max_value:
                matched = value >= min_value or value <= max_value
            else:
                matched = min_value <= value <= max_value
    elif operator == "in":
        values = expected if isinstance(expected, list) else [expected]
        matched = actual in values
    elif operator == "not_in":
        values = expected if isinstance(expected, list) else [expected]
        matched = actual not in values
    elif operator == "contains":
        if isinstance(actual, list):
            matched = expected in actual
        elif isinstance(actual, dict):
            matched = expected in actual
        elif isinstance(actual, str):
            matched = str(expected) in actual

    return matched, [field_path] if matched else []


def _condition_matches(condition: Any, context: dict[str, Any]) -> tuple[bool, list[str]]:
    if not isinstance(condition, dict) or not condition:
        return True, []

    if "all" in condition:
        matched_fields: list[str] = []
        for child in condition.get("all", []):
            matched, fields = _condition_matches(child, context)
            if not matched:
                return False, []
            matched_fields.extend(fields)
        return True, matched_fields

    if "any" in condition:
        matched_fields: list[str] = []
        for child in condition.get("any", []):
            matched, fields = _condition_matches(child, context)
            if matched:
                matched_fields.extend(fields)
        return bool(matched_fields), matched_fields

    if "not" in condition:
        matched, _ = _condition_matches(condition.get("not"), context)
        return not matched, []

    return _leaf_condition_matches(condition, context)


def _trigger_flags_match(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    trigger_flags = [str(flag).strip() for flag in rule.get("trigger_flags", []) if str(flag).strip()]
    if not trigger_flags:
        return True
    flags = set(context.get("flags") or [])
    return all(flag in flags for flag in trigger_flags)


def _target_action_matches(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    targets = _runtime_value(rule, "target_action_types", [])
    if not isinstance(targets, list) or not targets:
        return True
    action_type = str(context.get("action_type") or "")
    normalized = {str(item).strip() for item in targets if str(item).strip()}
    return "*" in normalized or action_type in normalized


def _scope_matches(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    scope = _runtime_value(rule, "scope", {"type": "global"})
    if not isinstance(scope, dict):
        return True
    scope_type = str(scope.get("type") or "global")
    if scope_type == "global":
        return True
    zone_id = str(context.get("zone_id") or "")
    if scope_type == "zone":
        zone_ids = scope.get("zone_ids", [])
        return isinstance(zone_ids, list) and zone_id in {str(item) for item in zone_ids}
    return True


def _policy_outcome(rule: dict[str, Any]) -> str:
    outcome = str(_runtime_value(rule, "outcome", "") or "")
    if outcome in POLICY_RESULT_ORDER:
        return outcome

    mode = str(rule.get("enforcement", {}).get("mode") or "")
    if mode == "approval_escalation":
        return "approval_required"
    if str(rule.get("stage") or "") in {"hard_block", "range_limit", "robot_safety"}:
        return "blocked"
    return "pass"


def evaluate_policy_rules(
    raw_request: dict[str, Any],
    *,
    rules: list[dict[str, Any]] | None = None,
) -> PolicyEvaluationReport:
    context = _build_context(raw_request)
    enabled_rules = rules if rules is not None else load_enabled_policy_rules(stages=RUNTIME_POLICY_STAGES)
    matches: list[PolicyRuleMatch] = []
    policy_result = "pass"

    for rule in enabled_rules:
        policy_id = str(rule.get("rule_id") or "")
        if not policy_id:
            continue
        if not _scope_matches(rule, context):
            continue
        if not _target_action_matches(rule, context):
            continue
        if not _trigger_flags_match(rule, context):
            continue

        condition = _runtime_value(rule, "condition", {})
        matched, matched_fields = _condition_matches(condition, context)
        if not matched:
            continue

        result = _policy_outcome(rule)
        if result == "pass":
            continue

        enforcement = rule.get("enforcement") if isinstance(rule.get("enforcement"), dict) else {}
        category = str(_runtime_value(rule, "category", rule.get("stage") or "runtime_policy"))
        reason_code = str(enforcement.get("reason_code") or f"policy:{policy_id}")
        reason = str(enforcement.get("message") or rule.get("description") or reason_code)
        source_version = str(rule.get("source_version") or _runtime_value(rule, "source_version", ""))
        matches.append(
            PolicyRuleMatch(
                policy_id=policy_id,
                category=category,
                result=result,
                severity=str(rule.get("severity") or "medium"),
                reason_code=reason_code,
                reason=reason,
                matched_fields=matched_fields,
                source_version=source_version,
            )
        )
        policy_result = _merge_policy_result(policy_result, result)

    policy_ids = [match.policy_id for match in matches]
    reason_codes = [match.reason_code for match in matches]
    reasons = [f"policy_precheck:{match.policy_id}" for match in matches]
    return PolicyEvaluationReport(
        policy_result=policy_result,
        policy_ids=policy_ids,
        reason_codes=reason_codes,
        reasons=reasons,
        matches=matches,
    )
