from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_ACTION_TYPES = {
    "observe_only", "create_alert", "request_human_check", "adjust_fan", "adjust_shade",
    "adjust_vent", "short_irrigation", "adjust_fertigation", "adjust_heating", "adjust_co2",
    "pause_automation", "enter_safe_mode", "create_robot_task", "block_action",
}
ALLOWED_RETRIEVAL_COVERAGE = {"sufficient", "partial", "insufficient", "not_used"}
ALLOWED_ROBOT_TASK_TYPES = {"harvest_candidate_review", "inspect_crop", "skip_area", "manual_review"}
ALLOWED_FOLLOW_UP_TYPES = {
    "sensor_recheck", "visual_inspection", "device_readback", "operator_confirm",
    "trend_review", "lab_test", "other", "manual_review", "operator_review",
}
RUN_STATE_VALUES = {"off", "on", "open", "closed"}
RECIPE_VALUES = {"hold", "veg_a", "veg_b", "flush", "sanitize", "default-recipe"}


@dataclass(frozen=True)
class ResponseContractReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings)}


def validate_response_contract(
    output: dict[str, Any],
    *,
    retrieved_chunk_ids: set[str] | None = None,
    raw_text: str | None = None,
    strict_json_ok: bool | None = None,
) -> ResponseContractReport:
    errors: list[str] = []
    warnings: list[str] = []
    retrieved_chunk_ids = retrieved_chunk_ids or set()

    if raw_text is not None:
        _validate_no_natural_language_leakage(raw_text, strict_json_ok=strict_json_ok, errors=errors)
    coverage = output.get("retrieval_coverage")
    if coverage not in ALLOWED_RETRIEVAL_COVERAGE:
        errors.append("retrieval_coverage:invalid_or_missing")
    confidence = output.get("confidence")
    if not isinstance(confidence, int | float) or isinstance(confidence, bool) or not 0 <= float(confidence) <= 1:
        errors.append("confidence:must_be_number_0_to_1")
    _validate_actions(output.get("recommended_actions", []), errors=errors, warnings=warnings)
    _validate_follow_up(output, errors=errors)
    _validate_citations(
        output.get("citations"),
        retrieved_chunk_ids=retrieved_chunk_ids,
        coverage=str(coverage or ""),
        errors=errors,
        warnings=warnings,
    )
    _validate_robot_tasks(output.get("robot_tasks", []), errors=errors)
    return ResponseContractReport(errors=errors, warnings=warnings)


def _validate_no_natural_language_leakage(raw_text: str, *, strict_json_ok: bool | None, errors: list[str]) -> None:
    stripped = raw_text.strip()
    if not stripped:
        errors.append("natural_language_leakage:empty_response")
        return
    if stripped.startswith("```"):
        errors.append("natural_language_leakage:markdown_fence")
    if not stripped.startswith("{") or not stripped.endswith("}"):
        errors.append("natural_language_leakage:non_json_prefix_or_suffix")
    if strict_json_ok is False:
        errors.append("natural_language_leakage:recovered_not_strict_json")


def _validate_actions(raw_actions: Any, *, errors: list[str], warnings: list[str]) -> None:
    if raw_actions is None:
        return
    if not isinstance(raw_actions, list):
        errors.append("recommended_actions:must_be_array")
        return
    for index, action in enumerate(raw_actions):
        prefix = f"recommended_actions[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{prefix}:must_be_object")
            continue
        action_type = action.get("action_type")
        if action_type not in ALLOWED_ACTION_TYPES:
            errors.append(f"{prefix}.action_type:invalid")
        if "approval_required" in action and not isinstance(action.get("approval_required"), bool):
            errors.append(f"{prefix}.approval_required:must_be_boolean")
        if "risk_level" in action and action.get("risk_level") not in {"low", "medium", "high", "critical", "unknown"}:
            errors.append(f"{prefix}.risk_level:invalid")
        target = action.get("target")
        if target is not None and not _valid_target(target):
            errors.append(f"{prefix}.target:invalid")
        parameters = action.get("parameters")
        if parameters is not None:
            _validate_action_parameters(str(action_type or ""), parameters, prefix=prefix, errors=errors, warnings=warnings)


def _valid_target(target: Any) -> bool:
    return (
        isinstance(target, dict)
        and isinstance(target.get("target_type"), str)
        and isinstance(target.get("target_id"), str)
        and bool(target.get("target_type"))
        and bool(target.get("target_id"))
    )


def _validate_action_parameters(action_type: str, parameters: Any, *, prefix: str, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(parameters, dict):
        errors.append(f"{prefix}.parameters:must_be_object")
        return
    allowed_by_action = {
        "adjust_fan": {"run_state", "speed_pct"},
        "adjust_shade": {"position_pct"},
        "adjust_vent": {"position_pct"},
        "short_irrigation": {"run_state", "duration_seconds"},
        "adjust_fertigation": {"recipe_id", "mix_volume_l"},
        "adjust_heating": {"run_state", "stage"},
        "adjust_co2": {"run_state", "dose_pct"},
        "pause_automation": {"run_state", "reason"},
        "enter_safe_mode": {"reason"},
        "create_alert": {"severity", "summary", "reason"},
        "request_human_check": {"reason", "check_type"},
        "observe_only": {"reason"},
        "block_action": {"blocked_action_type", "reason"},
        "create_robot_task": {"task_type", "candidate_id", "priority"},
    }
    allowed = allowed_by_action.get(action_type, set())
    for key in sorted(key for key in parameters if allowed and key not in allowed):
        warnings.append(f"{prefix}.parameters.{key}:unknown_for_action")
    for key, value in parameters.items():
        if key in {"position_pct", "speed_pct", "dose_pct"}:
            _validate_number_range(value, minimum=0, maximum=100, field=f"{prefix}.parameters.{key}", errors=errors)
        elif key == "duration_seconds":
            _validate_number_range(value, minimum=30, maximum=900, field=f"{prefix}.parameters.duration_seconds", errors=errors)
        elif key == "stage":
            _validate_number_range(value, minimum=0, maximum=2, field=f"{prefix}.parameters.stage", errors=errors)
        elif key == "mix_volume_l":
            _validate_number_range(value, minimum=50, maximum=1000, field=f"{prefix}.parameters.mix_volume_l", errors=errors)
        elif key == "run_state" and value not in RUN_STATE_VALUES:
            errors.append(f"{prefix}.parameters.run_state:invalid")
        elif key == "recipe_id" and value not in RECIPE_VALUES:
            errors.append(f"{prefix}.parameters.recipe_id:invalid")


def _validate_number_range(value: Any, *, minimum: float, maximum: float, field: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        errors.append(f"{field}:must_be_number")
        return
    if not minimum <= float(value) <= maximum:
        errors.append(f"{field}:out_of_range")


def _validate_follow_up(output: dict[str, Any], *, errors: list[str]) -> None:
    follow_up = output.get("follow_up")
    required_follow_up = output.get("required_follow_up")
    if not isinstance(follow_up, list) and not isinstance(required_follow_up, list):
        errors.append("follow_up:missing")
        return
    for field_name, items in (("follow_up", follow_up), ("required_follow_up", required_follow_up)):
        if items is None:
            continue
        if not isinstance(items, list) or not items:
            errors.append(f"{field_name}:must_be_non_empty_array")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{field_name}[{index}]:must_be_object")
                continue
            check_type = item.get("check_type") or item.get("type")
            if check_type is not None and check_type not in ALLOWED_FOLLOW_UP_TYPES:
                errors.append(f"{field_name}[{index}].type:invalid")
            if not any(isinstance(item.get(key), str) and item.get(key) for key in ("description", "note", "reason")):
                errors.append(f"{field_name}[{index}]:missing_description_note_or_reason")


def _validate_citations(citations: Any, *, retrieved_chunk_ids: set[str], coverage: str, errors: list[str], warnings: list[str]) -> None:
    if citations is None:
        if coverage in {"sufficient", "partial"}:
            errors.append("citations:missing_for_retrieved_output")
        return
    if not isinstance(citations, list):
        errors.append("citations:must_be_array")
        return
    if coverage in {"sufficient", "partial"} and not citations:
        errors.append("citations:empty_for_retrieved_output")
    for index, citation in enumerate(citations):
        prefix = f"citations[{index}]"
        if not isinstance(citation, dict):
            errors.append(f"{prefix}:must_be_object")
            continue
        chunk_id = citation.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            errors.append(f"{prefix}.chunk_id:missing")
            continue
        if retrieved_chunk_ids and chunk_id not in retrieved_chunk_ids:
            errors.append(f"{prefix}.chunk_id:not_in_retrieved_context")
        if not citation.get("document_id"):
            warnings.append(f"{prefix}.document_id:missing")


def _validate_robot_tasks(raw_tasks: Any, *, errors: list[str]) -> None:
    if raw_tasks is None:
        return
    if not isinstance(raw_tasks, list):
        errors.append("robot_tasks:must_be_array")
        return
    for index, task in enumerate(raw_tasks):
        prefix = f"robot_tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix}:must_be_object")
            continue
        if task.get("task_type") not in ALLOWED_ROBOT_TASK_TYPES:
            errors.append(f"{prefix}.task_type:invalid")
        if not isinstance(task.get("reason"), str) or not task.get("reason"):
            errors.append(f"{prefix}.reason:missing")
        if "approval_required" in task and not isinstance(task.get("approval_required"), bool):
            errors.append(f"{prefix}.approval_required:must_be_boolean")
        if not task.get("candidate_id") and not isinstance(task.get("target"), dict):
            errors.append(f"{prefix}:candidate_id_or_target_required")
