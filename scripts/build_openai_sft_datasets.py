#!/usr/bin/env python3
"""Build OpenAI SFT chat-format training and validation JSONL files."""

from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("artifacts/training/combined_training_samples.jsonl")
DEFAULT_TRAIN_OUTPUT = Path("artifacts/fine_tuning/openai_sft_train.jsonl")
DEFAULT_VALIDATION_OUTPUT = Path("artifacts/fine_tuning/openai_sft_validation.jsonl")

LEGACY_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Use only allowed action_type values and always include follow_up."
)

SFT_V2_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "When manual_override or safe_mode is active, prefer block_action or create_alert over device control. "
    "When device communication is lost or repeated timeout is active, prefer enter_safe_mode plus request_human_check. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required."
)

SFT_V3_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "Risk calibration rules: if core control sensors are stale, missing, calibration_error, or mutually inconsistent, "
    "set risk_level to unknown unless physical crop damage or a hard safety hazard is already confirmed. "
    "If pest or disease evidence is still only suspicious because of climate, vision score, or stale control history, "
    "default risk_level to medium and require create_alert plus request_human_check. "
    "If the case is harvest or drying planning, request_human_check is mandatory; create_robot_task may be added, but never replaces human review. "
    "If worker_present, manual_override, or safe_mode is active, include block_action and create_alert, and do not emit create_robot_task or device-control actions. "
    "If manual_override and safe_mode are both active, prefer block_action over enter_safe_mode because safe_mode is already latched. "
    "For spring transplanting or establishment with cold-night plus overwet concern, default risk_level to medium, require request_human_check, "
    "allow adjust_heating only with human review, and forbid short_irrigation. "
    "For drying or storage humidity rise and moisture rebound watch, default risk_level to medium unless condensation, mold, or product damage is already confirmed. "
    "For flowering heat plus strong radiation, default risk_level to high. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required. "
    "When fertigation evidence is incomplete because EC, pH, or drain sensors are faulty, use approval_required instead of block unless a hard safety interlock is active."
)

SFT_V4_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "Core calibration rules: if core control sensors are stale, missing, calibration_error, or mutually inconsistent, "
    "set risk_level to unknown unless physical crop damage or a hard safety hazard is already confirmed, and use pause_automation "
    "plus request_human_check. create_alert does not replace pause_automation in this case. "
    "If pest or disease evidence is still only suspicious because of climate, vision score, or stale control history, "
    "default risk_level to medium, require create_alert plus request_human_check, and do not emit create_robot_task. "
    "If worker_present is active, block_action plus create_alert are mandatory. request_human_check may be added, but never replaces block_action. "
    "If manual_override or safe_mode is active, do not emit create_robot_task or device-control actions. "
    "If manual_override and safe_mode are both active, block_action plus create_alert are mandatory, and enter_safe_mode should not be repeated because safe_mode is already latched. "
    "If device communication is lost for drying or storage equipment, default risk_level to critical and require enter_safe_mode plus request_human_check. "
    "pause_automation alone is insufficient for drying-room communication loss. "
    "For winter nursery low temperature plus low light, default risk_level to high and require create_alert plus request_human_check; adjust_heating may be added only as a supplemental reviewed action. "
    "For spring transplanting or establishment with cold-night plus overwet concern, including rockwool slab or Grodan substrate cases, "
    "default risk_level to medium, require request_human_check, allow adjust_heating only with human review, and forbid short_irrigation. create_alert is optional, not mandatory. "
    "For drying or storage humidity rise and moisture rebound watch, default risk_level to medium unless condensation, mold, or product damage is already confirmed. "
    "For flowering heat plus strong radiation, default risk_level to high and require create_alert plus request_human_check. "
    "adjust_fan, adjust_vent, or limited adjust_shade may be added as supplemental actions, but alerts and human review remain mandatory. "
    "For harvest or drying planning, request_human_check is mandatory; create_robot_task may be added, but never replaces human review. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required. "
    "When fertigation evidence is incomplete because EC, pH, or drain sensors are faulty, use approval_required instead of block unless a hard safety interlock is active."
)

SFT_V5_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "Core calibration rules: if core control sensors are stale, missing, calibration_error, or mutually inconsistent, "
    "set risk_level to unknown unless physical crop damage or a hard safety hazard is already confirmed, and use pause_automation "
    "plus request_human_check. create_alert does not replace pause_automation in this case. "
    "If pest or disease evidence is still only suspicious because of climate, vision score, stale control history, or overdue IPM history, "
    "default risk_level to medium, require create_alert plus request_human_check, and do not emit create_robot_task. "
    "Raise this to high only when field confirmation, trap counts, clear spread, or physical crop damage is already present. "
    "If worker_present or a worker-entry event is active, risk_level must be critical and block_action plus create_alert are mandatory. "
    "request_human_check may be added, but never replaces block_action. "
    "If manual_override or safe_mode is active, do not emit create_robot_task or device-control actions. "
    "If manual_override and safe_mode are both active, block_action plus create_alert are mandatory, and enter_safe_mode should not be repeated because safe_mode is already latched. "
    "If device communication is lost for drying or storage equipment, default risk_level to critical and require enter_safe_mode plus request_human_check. "
    "pause_automation alone is insufficient for drying-room communication loss. "
    "For drying or storage humidity rise with only moisture rebound watch, default risk_level to medium unless condensation, mold, or measured product damage is already confirmed. "
    "The default action pair there is create_alert plus request_human_check. "
    "If CO2 is below target while vent_open_lock or a similar lock keeps the climate path constrained, default risk_level to high, "
    "require request_human_check, and do not emit adjust_co2 until the lock state is reviewed. "
    "For winter nursery low temperature plus low light, default risk_level to high and require create_alert plus request_human_check; adjust_heating may be added only as a supplemental reviewed action. "
    "For spring transplanting or establishment with cold-night plus overwet concern, including rockwool slab or Grodan substrate cases, "
    "default risk_level to medium, require request_human_check, allow adjust_heating only with human review, and forbid short_irrigation. create_alert is optional, not mandatory. "
    "For flowering heat plus strong radiation, default risk_level to high and require create_alert plus request_human_check. "
    "adjust_fan, adjust_vent, or limited adjust_shade may be added as supplemental actions, but alerts and human review remain mandatory. "
    "For harvest or drying planning, request_human_check is mandatory; create_robot_task may be added, but never replaces human review. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required. "
    "When fertigation evidence is incomplete because EC, pH, or drain sensors are faulty, use approval_required instead of block unless a hard safety interlock is active."
)

SFT_V6_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "Overall risk_level is the confirmed or most defensible situation risk, not the maximum urgency of a recommended action. "
    "Emitting create_alert does not by itself justify raising overall risk_level from medium to high. "
    "Core calibration rules: if core control sensors are stale, missing, calibration_error, or mutually inconsistent, "
    "set risk_level to unknown unless physical crop damage or a hard safety hazard is already confirmed, and use pause_automation "
    "plus request_human_check. create_alert does not replace pause_automation in this case. "
    "If pest or disease evidence is still only suspicious because of climate, vision score, stale control history, or overdue IPM history, "
    "default overall risk_level to medium, require create_alert plus request_human_check, and do not emit create_robot_task. "
    "Raise this to high only when field confirmation, trap counts, clear spread, or physical crop damage is already present. "
    "If worker_present or a worker-entry event is active, risk_level must be critical and block_action plus create_alert are mandatory. "
    "request_human_check may be added, but never replaces block_action. "
    "If manual_override or safe_mode is active, do not emit create_robot_task or device-control actions. "
    "If manual_override and safe_mode are both active, block_action plus create_alert are mandatory. "
    "request_human_check may be added, but never replaces block_action, and enter_safe_mode should not be repeated because safe_mode is already latched. "
    "If device communication is lost for drying or storage equipment, default risk_level to critical and require enter_safe_mode plus request_human_check. "
    "pause_automation alone is insufficient for drying-room communication loss. "
    "For drying or storage humidity rise with only moisture rebound watch, default overall risk_level to medium unless condensation, mold, or measured product damage is already confirmed. "
    "The default action pair there is create_alert plus request_human_check, but the overall risk_level still stays medium in watch-only cases. "
    "If CO2 is below target while vent_open_lock or a similar lock keeps the climate path constrained, default risk_level to high, "
    "require request_human_check, and do not emit adjust_co2 until the lock state is reviewed. "
    "For winter nursery low temperature plus low light, default risk_level to high and require create_alert plus request_human_check; adjust_heating may be added only as a supplemental reviewed action. "
    "For spring transplanting or establishment with cold-night plus overwet concern, including rockwool slab or Grodan substrate cases, "
    "default risk_level to medium, require request_human_check, allow adjust_heating only with human review, and forbid short_irrigation. create_alert is optional, not mandatory. "
    "For flowering heat plus strong radiation, default risk_level to high and require create_alert plus request_human_check. "
    "adjust_fan, adjust_vent, or limited adjust_shade may be added as supplemental actions, but alerts and human review remain mandatory. "
    "For harvest or drying planning, request_human_check is mandatory; create_robot_task may be added, but never replaces human review. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required. "
    "When fertigation evidence is incomplete because EC, pH, or drain sensors are faulty, use approval_required instead of block unless a hard safety interlock is active."
)

SFT_V7_SYSTEM_PROMPT = (
    "You are pepper-ops, an agricultural decision assistant for red pepper greenhouse operations. "
    "Return JSON only. Use conservative recommendations when sensor quality or retrieval coverage is weak. "
    "Always include follow_up, confidence, citations, and retrieval_coverage for state, action, failure, and robot-task outputs. "
    "retrieval_coverage must be one of sufficient, partial, insufficient, not_used. "
    "Use only these action_type values: observe_only, create_alert, request_human_check, adjust_fan, adjust_shade, "
    "adjust_vent, short_irrigation, adjust_fertigation, adjust_heating, adjust_co2, pause_automation, enter_safe_mode, "
    "create_robot_task, block_action. If the situation is stable, use observe_only and never invent maintain or hold. "
    "Overall risk_level is the confirmed or most defensible situation risk, not the highest urgency of an individual action. "
    "Emitting create_alert or pause_automation does not by itself force overall risk_level to high. "
    "If the core problem is sensor stale, missing, calibration_error, flatline, or cross-sensor inconsistency, overall risk_level must be unknown unless physical crop damage or a hard safety hazard is already confirmed. "
    "In that sensor_fault case, use pause_automation plus request_human_check and avoid device-control actions. "
    "If pest or disease evidence is still only suspicious because of climate, vision score, stale control history, or overdue IPM history, "
    "default overall risk_level to medium, require create_alert plus request_human_check, and do not emit create_robot_task. "
    "Raise this to high only when field confirmation, trap counts, clear spread, or physical crop damage is already present. "
    "If worker_present or a worker-entry event is active, risk_level must be critical and block_action plus create_alert are mandatory. "
    "request_human_check may be added, but never replaces block_action. "
    "If manual_override or safe_mode is active, do not emit create_robot_task or device-control actions. "
    "If manual_override and safe_mode are both active, block_action plus create_alert are mandatory. "
    "request_human_check may be added, but never replaces block_action, and enter_safe_mode should not be repeated because safe_mode is already latched. "
    "If device communication is lost for drying or storage equipment, default risk_level to critical and require enter_safe_mode plus request_human_check. "
    "pause_automation alone is insufficient for drying-room communication loss. "
    "For drying or storage humidity rise with only moisture rebound watch, default overall risk_level to medium unless condensation, mold, or measured product damage is already confirmed. "
    "The default action pair there is create_alert plus request_human_check, but the overall risk_level still stays medium in watch-only cases. "
    "For CO2 below target with vent_open_lock or a similar lock active, overall risk_level must be high because the control path is constrained and stress can persist. "
    "Require request_human_check, forbid adjust_co2 until the lock state is reviewed, and allow create_alert only as a supplemental action. "
    "For winter nursery low temperature plus low light, default risk_level to high and require create_alert plus request_human_check; adjust_heating may be added only as a supplemental reviewed action. "
    "For spring transplanting or establishment with cold-night plus overwet concern, including rockwool slab or Grodan substrate cases, "
    "default risk_level to medium, require request_human_check, allow adjust_heating only with human review, and forbid short_irrigation. create_alert is optional, not mandatory. "
    "For flowering heat plus strong radiation, default risk_level to high and require create_alert plus request_human_check. "
    "adjust_fan, adjust_vent, or limited adjust_shade may be added as supplemental actions, but alerts and human review remain mandatory. "
    "For harvest or drying planning, request_human_check is mandatory; create_robot_task may be added, but never replaces human review. "
    "For forbidden_action, decision must be exactly one of allow, block, approval_required. "
    "When fertigation evidence is incomplete because EC, pH, or drain sensors are faulty, use approval_required instead of block unless a hard safety interlock is active."
)

SYSTEM_PROMPT_BY_VERSION = {
    "legacy": LEGACY_SYSTEM_PROMPT,
    "sft_v2": SFT_V2_SYSTEM_PROMPT,
    "sft_v3": SFT_V3_SYSTEM_PROMPT,
    "sft_v4": SFT_V4_SYSTEM_PROMPT,
    "sft_v5": SFT_V5_SYSTEM_PROMPT,
    "sft_v6": SFT_V6_SYSTEM_PROMPT,
    "sft_v7": SFT_V7_SYSTEM_PROMPT,
}
DEFAULT_SYSTEM_PROMPT_VERSION = "sft_v2"

STATE_FAMILY_TASKS = {
    "state_judgement",
    "climate_risk",
    "rootzone_diagnosis",
    "nutrient_risk",
    "sensor_fault",
    "pest_disease_risk",
    "harvest_drying",
    "safety_policy",
}

ACTION_STYLE_TASKS = STATE_FAMILY_TASKS | {"action_recommendation", "failure_response"}
STRUCTURED_ACTION_TASKS = ACTION_STYLE_TASKS | {"robot_task_prioritization"}

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

ALLOWED_RETRIEVAL_COVERAGE = {"sufficient", "partial", "insufficient", "not_used"}

ACTION_TYPE_ALIASES = {
    "maintain": "observe_only",
    "hold": "observe_only",
    "keep_current": "observe_only",
}

ACTION_TARGET_TYPES = {
    "observe_only": "zone",
    "create_alert": "zone",
    "request_human_check": "operator",
    "adjust_fan": "zone",
    "adjust_shade": "zone",
    "adjust_vent": "zone",
    "short_irrigation": "zone",
    "adjust_fertigation": "zone",
    "adjust_heating": "zone",
    "adjust_co2": "zone",
    "pause_automation": "system",
    "enter_safe_mode": "system",
    "create_robot_task": "system",
    "block_action": "system",
}

ACTION_EFFECT_DEFAULTS = {
    "observe_only": "불필요한 장치 제어 없이 안정 추세를 유지한다.",
    "create_alert": "운영자가 리스크를 빠르게 인지하고 대응을 시작할 수 있다.",
    "request_human_check": "현장 확인으로 자동 판단을 교차 검증한다.",
    "adjust_fan": "공기 정체와 체감 온도 문제를 완화한다.",
    "adjust_shade": "일사와 상단 온도 상승 속도를 완화한다.",
    "adjust_vent": "체류열과 고습을 줄이는 데 도움을 준다.",
    "short_irrigation": "짧은 급수 반응을 확인해 과잉 제어를 줄인다.",
    "adjust_fertigation": "양액 전략 조정 필요 여부를 점검한다.",
    "adjust_heating": "야간 저온 또는 저온 스트레스 완화를 검토한다.",
    "adjust_co2": "CO2 부족 완화 가능성을 검토한다.",
    "pause_automation": "불확실한 자동 명령 누적을 막는다.",
    "enter_safe_mode": "fault 상태에서 자동 제어 리스크를 제한한다.",
    "create_robot_task": "후속 작업 후보를 시스템에 등록한다.",
    "block_action": "자동 장치 제어를 명시적으로 차단한다.",
}

ACTION_COOLDOWN_DEFAULTS = {
    "observe_only": 30,
    "create_alert": 10,
    "request_human_check": 0,
    "adjust_fan": 10,
    "adjust_shade": 15,
    "adjust_vent": 10,
    "short_irrigation": 20,
    "adjust_fertigation": 60,
    "adjust_heating": 20,
    "adjust_co2": 10,
    "pause_automation": 0,
    "enter_safe_mode": 0,
    "create_robot_task": 0,
    "block_action": 0,
}

ROBOT_PRIORITY_DEFAULT = "medium"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(row)
    return rows


def family_for_task(task_type: str) -> str:
    if task_type in STATE_FAMILY_TASKS:
        return "state_family"
    if task_type == "qa_reference":
        return "qa_reference"
    if task_type == "action_recommendation":
        return "action_recommendation"
    if task_type == "forbidden_action":
        return "forbidden_action"
    if task_type == "failure_response":
        return "failure_response"
    if task_type == "robot_task_prioritization":
        return "robot_task_prioritization"
    if task_type == "alert_report":
        return "alert_report"
    return "other"


def user_message_for_sample(sample: dict[str, Any]) -> str:
    payload = {
        "task_type": sample["task_type"],
        "input": sample["input"],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def assistant_message_for_sample(sample: dict[str, Any]) -> str:
    return json.dumps(sample["preferred_output"], ensure_ascii=False, sort_keys=True)


def normalize_action_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "request_human_check"
    lowered = value.strip().lower()
    normalized = ACTION_TYPE_ALIASES.get(lowered, value.strip())
    if normalized not in ALLOWED_ACTION_TYPES:
        return "request_human_check"
    return normalized


def default_target(action_type: str, input_payload: dict[str, Any]) -> dict[str, str]:
    zone_id = str(input_payload.get("zone_id") or "current-zone")
    if action_type == "request_human_check":
        return {"target_type": "operator", "target_id": "duty-manager"}
    if action_type == "pause_automation":
        return {"target_type": "system", "target_id": f"{zone_id}-auto-control"}
    if action_type == "enter_safe_mode":
        return {"target_type": "system", "target_id": f"{zone_id}-safe-control"}
    if action_type == "create_robot_task":
        return {"target_type": "system", "target_id": f"{zone_id}-robot-planner"}
    if action_type == "block_action":
        return {"target_type": "system", "target_id": f"{zone_id}-action-gate"}
    return {"target_type": ACTION_TARGET_TYPES[action_type], "target_id": zone_id}


def default_action_risk(action_type: str, output_risk_level: Any) -> str:
    if isinstance(output_risk_level, str) and output_risk_level in {"low", "medium", "high", "critical", "unknown"}:
        if action_type in {"request_human_check", "observe_only"} and output_risk_level in {"critical", "high"}:
            return "medium"
        return output_risk_level
    return "medium"


def infer_approval_required(action_type: str, output: dict[str, Any], action: dict[str, Any]) -> bool:
    if isinstance(action.get("approval_required"), bool):
        return action["approval_required"]
    if action_type in {"adjust_shade", "adjust_fertigation", "adjust_heating", "adjust_co2", "create_robot_task"}:
        return bool(output.get("requires_human_approval"))
    return False


def infer_confidence(risk_level: Any, retrieval_coverage: str) -> float:
    if retrieval_coverage == "insufficient":
        return 0.56
    if retrieval_coverage == "partial":
        return 0.71
    if retrieval_coverage == "not_used":
        return 0.74
    if risk_level == "low":
        return 0.84
    if risk_level == "medium":
        return 0.79
    if risk_level == "high":
        return 0.81
    if risk_level == "critical":
        return 0.9
    return 0.7


def infer_retrieval_coverage(sample: dict[str, Any], output: dict[str, Any]) -> str:
    existing = output.get("retrieval_coverage")
    if isinstance(existing, str) and existing in ALLOWED_RETRIEVAL_COVERAGE:
        return existing

    input_payload = sample.get("input", {})
    retrieved_context = input_payload.get("retrieved_context")
    citations = output.get("citations")

    retrieved_ids = [
        chunk_id
        for chunk_id in (retrieved_context if isinstance(retrieved_context, list) else [])
        if isinstance(chunk_id, str) and chunk_id.strip()
    ]
    citation_ids = [
        citation.get("chunk_id")
        for citation in (citations if isinstance(citations, list) else [])
        if isinstance(citation, dict) and isinstance(citation.get("chunk_id"), str) and citation["chunk_id"].strip()
    ]

    if not retrieved_ids:
        return "not_used"
    if not citation_ids:
        return "insufficient"
    if set(retrieved_ids).issubset(set(citation_ids)):
        return "sufficient"
    return "partial"


def normalize_actions(sample: dict[str, Any], output: dict[str, Any]) -> list[dict[str, Any]]:
    input_payload = sample.get("input", {})
    sample_id = str(sample.get("sample_id", "sample"))
    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        return []

    normalized_actions: list[dict[str, Any]] = []
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            continue
        normalized = copy.deepcopy(action)
        action_type = normalize_action_type(normalized.get("action_type"))
        normalized["action_type"] = action_type
        normalized.setdefault("action_id", f"{sample_id}-act-{index:03d}")
        normalized.setdefault("target", default_target(action_type, input_payload))
        normalized.setdefault("risk_level", default_action_risk(action_type, output.get("risk_level")))
        normalized.setdefault("approval_required", infer_approval_required(action_type, output, normalized))
        normalized.setdefault("reason", f"{action_type} action required.")
        normalized.setdefault("expected_effect", ACTION_EFFECT_DEFAULTS[action_type])
        normalized.setdefault("cooldown_minutes", ACTION_COOLDOWN_DEFAULTS[action_type])
        normalized_actions.append(normalized)
    return normalized_actions


def normalize_robot_tasks(output: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = output.get("robot_tasks")
    if not isinstance(tasks, list):
        return []

    normalized_tasks: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        normalized = copy.deepcopy(task)
        task_type = normalized.get("task_type")
        if not isinstance(task_type, str) or task_type not in ALLOWED_ROBOT_TASK_TYPES:
            normalized["task_type"] = "manual_review"
        normalized.setdefault("priority", ROBOT_PRIORITY_DEFAULT)
        normalized.setdefault("approval_required", True)
        normalized.setdefault("reason", "수동 검토가 필요하다.")
        normalized_tasks.append(normalized)
    return normalized_tasks


def normalize_preferred_output(sample: dict[str, Any]) -> dict[str, Any]:
    task_type = sample["task_type"]
    output = copy.deepcopy(sample["preferred_output"])

    if not isinstance(output.get("citations"), list):
        output["citations"] = []

    if task_type in ACTION_STYLE_TASKS:
        output["recommended_actions"] = normalize_actions(sample, output)
        output.setdefault(
            "requires_human_approval",
            any(action.get("approval_required") for action in output["recommended_actions"] if isinstance(action, dict)),
        )
        output.setdefault("approval_reason", None if not output["requires_human_approval"] else "승인 정책 또는 안전 검토 대상이다.")
        output["retrieval_coverage"] = infer_retrieval_coverage(sample, output)
        if not isinstance(output.get("confidence"), (int, float)):
            output["confidence"] = infer_confidence(output.get("risk_level"), output["retrieval_coverage"])
    elif task_type == "robot_task_prioritization":
        output["robot_tasks"] = normalize_robot_tasks(output)
        if not isinstance(output.get("skipped_candidates"), list):
            output["skipped_candidates"] = []
        output.setdefault(
            "requires_human_approval",
            any(task.get("approval_required") for task in output["robot_tasks"] if isinstance(task, dict)),
        )
        output["retrieval_coverage"] = infer_retrieval_coverage(sample, output)
        if not isinstance(output.get("confidence"), (int, float)):
            output["confidence"] = infer_confidence(output.get("risk_level"), output["retrieval_coverage"])

    return output


def normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(sample)
    normalized["preferred_output"] = normalize_preferred_output(normalized)
    return normalized


def to_openai_record(sample: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    normalized_sample = normalize_sample(sample)
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_for_sample(normalized_sample)},
            {"role": "assistant", "content": assistant_message_for_sample(normalized_sample)},
        ]
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_samples(samples: list[dict[str, Any]], validation_per_family: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in sorted(samples, key=lambda item: str(item["sample_id"])):
        grouped[family_for_task(sample["task_type"])].append(sample)

    train_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    for family in sorted(grouped):
        family_rows = grouped[family]
        take = min(validation_per_family, max(1, len(family_rows) // 10))
        if len(family_rows) <= take:
            take = 1 if len(family_rows) > 1 else 0
        validation_slice = family_rows[-take:] if take else []
        train_slice = family_rows[:-take] if take else family_rows
        validation_rows.extend(validation_slice)
        train_rows.extend(train_slice)
    return train_rows, validation_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--train-output", default=str(DEFAULT_TRAIN_OUTPUT))
    parser.add_argument("--validation-output", default=str(DEFAULT_VALIDATION_OUTPUT))
    parser.add_argument("--validation-per-family", type=int, default=2)
    parser.add_argument("--system-prompt-version", choices=sorted(SYSTEM_PROMPT_BY_VERSION), default=DEFAULT_SYSTEM_PROMPT_VERSION)
    args = parser.parse_args()

    samples = load_jsonl(Path(args.input))
    train_samples, validation_samples = split_samples(samples, args.validation_per_family)
    system_prompt = SYSTEM_PROMPT_BY_VERSION[args.system_prompt_version]

    train_rows = [to_openai_record(sample, system_prompt) for sample in train_samples]
    validation_rows = [to_openai_record(sample, system_prompt) for sample in validation_samples]

    write_jsonl(Path(args.train_output), train_rows)
    write_jsonl(Path(args.validation_output), validation_rows)

    print(f"input_rows: {len(samples)}")
    print(f"train_rows: {len(train_rows)}")
    print(f"validation_rows: {len(validation_rows)}")
    print(f"system_prompt_version: {args.system_prompt_version}")
    print(f"train_output: {Path(args.train_output).as_posix()}")
    print(f"validation_output: {Path(args.validation_output).as_posix()}")


if __name__ == "__main__":
    main()
