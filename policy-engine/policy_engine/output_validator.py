from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE_PATH = REPO_ROOT / "data/examples/policy_output_validator_rules_seed.json"

ALLOWED_ACTION_TYPES = {
    "observe_only",
    "create_alert",
    "request_human_check",
    "adjust_fan",
    "adjust_shade",
    "adjust_vent",
    "short_irrigation",
    "adjust_fertigation",
    "adjust_heating",
    "adjust_co2",
    "pause_automation",
    "enter_safe_mode",
    "create_robot_task",
    "block_action",
}

ALLOWED_ROBOT_TASK_TYPES = {
    "harvest_candidate_review",
    "inspect_crop",
    "skip_area",
    "manual_review",
}

HIGH_APPROVAL_ACTIONS = {
    "adjust_fertigation",
    "adjust_heating",
    "adjust_co2",
    "create_robot_task",
}


@dataclass(frozen=True)
class ValidatorContext:
    farm_id: str
    zone_id: str
    task_type: str
    summary: str
    requires_citations: bool = False
    worker_present: bool = False
    manual_override_active: bool = False
    safe_mode_active: bool = False
    zone_clearance_uncertain: bool = False
    aisle_slip_hazard: bool = False
    irrigation_path_degraded: bool = False
    source_water_path_degraded: bool = False
    dry_room_path_degraded: bool = False
    climate_control_degraded: bool = False
    rootzone_sensor_conflict: bool = False
    rootzone_control_interpretable: bool = True
    core_climate_interpretable: bool = True

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ValidatorContext":
        return cls(
            farm_id=str(raw.get("farm_id") or "demo-farm"),
            zone_id=str(raw.get("zone_id") or "unknown-zone"),
            task_type=str(raw.get("task_type") or "unknown_task"),
            summary=str(raw.get("summary") or ""),
            requires_citations=bool(raw.get("requires_citations")),
            worker_present=bool(raw.get("worker_present")),
            manual_override_active=bool(raw.get("manual_override_active")),
            safe_mode_active=bool(raw.get("safe_mode_active")),
            zone_clearance_uncertain=bool(raw.get("zone_clearance_uncertain")),
            aisle_slip_hazard=bool(raw.get("aisle_slip_hazard")),
            irrigation_path_degraded=bool(raw.get("irrigation_path_degraded")),
            source_water_path_degraded=bool(raw.get("source_water_path_degraded")),
            dry_room_path_degraded=bool(raw.get("dry_room_path_degraded")),
            climate_control_degraded=bool(raw.get("climate_control_degraded")),
            rootzone_sensor_conflict=bool(raw.get("rootzone_sensor_conflict")),
            rootzone_control_interpretable=bool(raw.get("rootzone_control_interpretable", True)),
            core_climate_interpretable=bool(raw.get("core_climate_interpretable", True)),
        )


@dataclass(frozen=True)
class ValidatorResult:
    output: dict[str, Any]
    applied_rules: list[str]
    decision: str


def load_rule_catalog(path: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = json.loads((path or DEFAULT_RULE_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("policy output validator rule catalog must be a JSON object")
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("policy output validator rules must be a list")
    catalog: dict[str, dict[str, Any]] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("policy output validator rule entries must be JSON objects")
        rule_id = str(rule.get("rule_id") or "")
        if not rule_id:
            raise ValueError("policy output validator rule_id is required")
        catalog[rule_id] = rule
    return catalog


def _target(context: ValidatorContext, *, target_type: str = "zone", target_id: str | None = None) -> dict[str, str]:
    return {"target_type": target_type, "target_id": target_id or context.zone_id}


def _follow_up(description: str) -> list[dict[str, Any]]:
    return [
        {
            "check_type": "operator_confirm",
            "due_in_minutes": 0,
            "description": description,
        }
    ]


def _citations(context: ValidatorContext) -> list[dict[str, str]]:
    return [
        {
            "document_id": "VALIDATOR-AUTO",
            "chunk_id": f"validator-{context.task_type}",
        }
    ]


def _make_action(
    context: ValidatorContext,
    *,
    action_type: str,
    risk_level: str,
    reason: str,
    target_type: str = "zone",
    target_id: str | None = None,
    approval_required: bool = False,
    cooldown_minutes: int = 0,
    expected_effect: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": f"validator-{action_type}",
        "action_type": action_type,
        "target": _target(context, target_type=target_type, target_id=target_id),
        "risk_level": risk_level,
        "approval_required": approval_required,
        "reason": reason,
        "expected_effect": expected_effect or "validator applied a conservative fallback.",
        "cooldown_minutes": cooldown_minutes,
    }


def _rewrite_actions(
    output: dict[str, Any],
    *,
    risk_level: str,
    actions: list[dict[str, Any]],
    keep_alert: bool = False,
) -> None:
    existing = output.get("recommended_actions")
    kept: list[dict[str, Any]] = []
    if keep_alert and isinstance(existing, list):
        kept = [
            action
            for action in existing
            if isinstance(action, dict) and action.get("action_type") == "create_alert"
        ]
    deduped: dict[str, dict[str, Any]] = {}
    for action in kept + actions:
        deduped[str(action["action_type"])] = action
    output["recommended_actions"] = list(deduped.values())
    output["risk_level"] = risk_level


def _normalize_action_contract(output: dict[str, Any], context: ValidatorContext, applied_rules: list[str]) -> None:
    actions = output.get("recommended_actions")
    normalized: list[dict[str, Any]] = []
    if not isinstance(actions, list):
        actions = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get("action_type") not in ALLOWED_ACTION_TYPES:
            applied_rules.append("OV-01")
            continue
        normalized_action = copy.deepcopy(action)
        normalized_action.setdefault("reason", "validator supplied missing action reason")
        normalized_action.setdefault("risk_level", output.get("risk_level", "unknown"))
        normalized_action.setdefault("approval_required", False)
        normalized_action.setdefault("cooldown_minutes", 0)
        normalized_action.setdefault("expected_effect", "validator supplied missing expected effect")
        if not isinstance(normalized_action.get("target"), dict):
            normalized_action["target"] = _target(context)
            applied_rules.append("OV-03")
        if normalized_action["action_type"] in HIGH_APPROVAL_ACTIONS and normalized_action.get("approval_required") is not True:
            normalized_action["approval_required"] = True
            applied_rules.append("OV-08")
        normalized.append(normalized_action)
    output["recommended_actions"] = normalized


def _normalize_robot_contract(output: dict[str, Any], context: ValidatorContext, applied_rules: list[str]) -> None:
    tasks = output.get("robot_tasks")
    normalized: list[dict[str, Any]] = []
    if not isinstance(tasks, list):
        tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        normalized_task = copy.deepcopy(task)
        if normalized_task.get("task_type") not in ALLOWED_ROBOT_TASK_TYPES:
            normalized_task["task_type"] = "skip_area" if context.zone_clearance_uncertain or context.aisle_slip_hazard else "manual_review"
            applied_rules.append("OV-02")
        normalized_task.setdefault("priority", "medium")
        normalized_task.setdefault("approval_required", True)
        normalized_task.setdefault("reason", "validator supplied missing robot task reason")
        if not normalized_task.get("candidate_id") and not isinstance(normalized_task.get("target"), dict):
            normalized_task["target"] = _target(context)
            applied_rules.append("OV-04")
        normalized.append(normalized_task)
    output["robot_tasks"] = normalized


def apply_output_validator(
    raw_output: dict[str, Any],
    context: ValidatorContext,
    *,
    rule_catalog: dict[str, dict[str, Any]] | None = None,
) -> ValidatorResult:
    catalog = rule_catalog or load_rule_catalog()
    output = copy.deepcopy(raw_output)
    applied_rules: list[str] = []
    decision = "pass"

    output.setdefault("situation_summary", context.summary or "validator supplied situation summary")
    output.setdefault("risk_level", "unknown")
    output.setdefault("retrieval_coverage", "partial")
    output.setdefault("confidence", 0.5)
    output.setdefault("requires_human_approval", False)

    worker_or_lock = context.worker_present or context.manual_override_active or context.safe_mode_active
    path_degraded = context.irrigation_path_degraded or context.source_water_path_degraded or context.dry_room_path_degraded
    rootzone_degraded = context.rootzone_sensor_conflict or not context.rootzone_control_interpretable
    climate_degraded = context.climate_control_degraded
    climate_unknown = (not context.core_climate_interpretable) and not climate_degraded

    if worker_or_lock and any(catalog.get(rule_id, {}).get("enabled", True) for rule_id in ("HSV-01", "HSV-02", "HSV-03")):
        _rewrite_actions(
            output,
            risk_level="critical",
            actions=[
                _make_action(
                    context,
                    action_type="block_action",
                    risk_level="critical",
                    reason="validator blocked action because a worker/manual override/safe mode safety lock is active.",
                    target_type="system",
                ),
                _make_action(
                    context,
                    action_type="create_alert",
                    risk_level="critical",
                    reason="validator raised an operator alert for the active safety lock.",
                    cooldown_minutes=10,
                ),
            ],
        )
        output["robot_tasks"] = []
        output["requires_human_approval"] = False
        applied_rules.extend(
            [
                rule_id
                for rule_id, active in (
                    ("HSV-01", context.worker_present),
                    ("HSV-02", context.manual_override_active),
                    ("HSV-03", context.safe_mode_active),
                )
                if active
            ]
        )
        decision = "rewritten"

    if path_degraded and any(catalog.get(rule_id, {}).get("enabled", True) for rule_id in ("HSV-04", "HSV-05", "HSV-06")):
        _rewrite_actions(
            output,
            risk_level="critical",
            actions=[
                _make_action(
                    context,
                    action_type="enter_safe_mode",
                    risk_level="critical",
                    reason="validator forced safe mode because a control path communication/readback loss is active.",
                    target_type="system",
                ),
                _make_action(
                    context,
                    action_type="request_human_check",
                    risk_level="critical",
                    reason="validator requested manual confirmation of the degraded path before restart.",
                    target_type="operator",
                    target_id="duty-manager",
                ),
            ],
        )
        output["robot_tasks"] = []
        applied_rules.extend(
            [
                rule_id
                for rule_id, active in (
                    ("HSV-04", context.irrigation_path_degraded),
                    ("HSV-05", context.source_water_path_degraded),
                    ("HSV-06", context.dry_room_path_degraded),
                )
                if active
            ]
        )
        decision = "rewritten"
    elif climate_degraded and catalog.get("HSV-07", {}).get("enabled", True):
        _rewrite_actions(
            output,
            risk_level="high",
            actions=[
                _make_action(
                    context,
                    action_type="pause_automation",
                    risk_level="high",
                    reason="validator paused automation because climate control already ran on degraded sensor evidence.",
                    target_type="system",
                ),
                _make_action(
                    context,
                    action_type="request_human_check",
                    risk_level="high",
                    reason="validator requested manual climate sensor and command history confirmation.",
                    target_type="operator",
                    target_id="duty-manager",
                ),
            ],
            keep_alert=True,
        )
        applied_rules.append("HSV-07")
        decision = "rewritten"
    elif (rootzone_degraded or climate_unknown) and any(catalog.get(rule_id, {}).get("enabled", True) for rule_id in ("HSV-07", "HSV-08")):
        unsafe = {
            "short_irrigation",
            "adjust_fertigation",
            "adjust_heating",
            "adjust_co2",
            "adjust_fan",
            "adjust_shade",
            "adjust_vent",
        }
        existing_actions = [
            action
            for action in output.get("recommended_actions", [])
            if isinstance(action, dict) and action.get("action_type") not in unsafe
        ]
        _rewrite_actions(
            output,
            risk_level="unknown",
            actions=existing_actions
            + [
                _make_action(
                    context,
                    action_type="pause_automation",
                    risk_level="unknown",
                    reason="validator paused automation because control evidence is degraded.",
                    target_type="system",
                ),
                _make_action(
                    context,
                    action_type="request_human_check",
                    risk_level="unknown",
                    reason="validator requested manual sensor or measurement confirmation.",
                    target_type="operator",
                    target_id="duty-manager",
                ),
            ],
            keep_alert=True,
        )
        if climate_unknown:
            applied_rules.append("HSV-07")
        if rootzone_degraded:
            applied_rules.append("HSV-08")
        decision = "rewritten"

    if context.zone_clearance_uncertain or context.aisle_slip_hazard:
        tasks = output.get("robot_tasks")
        if not isinstance(tasks, list):
            tasks = []
        if tasks:
            output["robot_tasks"] = [
                {
                    "task_type": "skip_area",
                    "priority": "high",
                    "approval_required": True,
                    "reason": "validator forced skip_area because worker clearance is uncertain or the aisle is unsafe.",
                    "target": _target(context),
                }
            ]
        applied_rules.append("HSV-10")
        decision = "rewritten"

    _normalize_action_contract(output, context, applied_rules)
    _normalize_robot_contract(output, context, applied_rules)

    if context.requires_citations and not output.get("citations"):
        output["citations"] = _citations(context)
        applied_rules.append("OV-06")
    if output.get("recommended_actions") and not output.get("follow_up"):
        output["follow_up"] = _follow_up("validator inserted follow-up for required review.")
        applied_rules.append("OV-05")

    output["requires_human_approval"] = any(
        bool(action.get("approval_required"))
        for action in output.get("recommended_actions", [])
        if isinstance(action, dict)
    )
    output["validator_reason_codes"] = sorted(set(applied_rules))
    output["validator_decision"] = "pass" if not applied_rules else decision
    return ValidatorResult(
        output=output,
        applied_rules=sorted(set(applied_rules)),
        decision=output["validator_decision"],
    )
