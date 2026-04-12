#!/usr/bin/env python3
"""Generate targeted batch11 training samples for safety, sensor, and robot slices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_OUTPUT = REPO_ROOT / "data" / "examples" / "state_judgement_samples_batch11.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data" / "examples" / "robot_task_samples_batch4.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-harvest-001": "RAG-SRC-001",
    "pepper-pest-001": "RAG-SRC-001",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
}


def citation(chunk_id: str) -> dict[str, str]:
    return {"chunk_id": chunk_id, "document_id": DOC_IDS[chunk_id]}


def action(
    sample_prefix: str,
    index: int,
    action_type: str,
    target_type: str,
    target_id: str,
    risk_level: str,
    approval_required: bool,
    reason: str,
    expected_effect: str,
    cooldown_minutes: int,
) -> dict[str, Any]:
    return {
        "action_id": f"{sample_prefix}-act-{index:03d}",
        "action_type": action_type,
        "target": {"target_type": target_type, "target_id": target_id},
        "risk_level": risk_level,
        "approval_required": approval_required,
        "reason": reason,
        "expected_effect": expected_effect,
        "cooldown_minutes": cooldown_minutes,
    }


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


def make_safety_sample(
    sample_number: int,
    growth_stage: str,
    zone_id: str,
    state_summary: str,
    active_constraints: list[str],
    retrieved_context: list[str],
    situation_summary: str,
    diagnosis: list[str],
    follow_up_description: str,
    skipped_actions: list[dict[str, str]],
) -> dict[str, Any]:
    sample_id = f"state-judgement-{sample_number:03d}"
    return {
        "sample_id": sample_id,
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": growth_stage,
            "zone_id": zone_id,
            "state_summary": state_summary,
            "active_constraints": active_constraints,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": situation_summary,
            "risk_level": "critical",
            "diagnosis": diagnosis,
            "recommended_actions": [
                action(
                    sample_id.replace("state-judgement", "state11"),
                    1,
                    "block_action",
                    "system",
                    f"{zone_id}-action-gate",
                    "critical",
                    False,
                    "작업자 개입, 수동 개입, safe mode 상태가 해제되기 전까지 자동 장치 제어와 로봇 작업을 차단 유지한다.",
                    "현장 작업과 자동 명령 충돌을 즉시 줄인다.",
                    0,
                ),
                action(
                    sample_id.replace("state-judgement", "state11"),
                    2,
                    "create_alert",
                    "zone",
                    zone_id,
                    "critical",
                    False,
                    "차단 유지 상태와 수동 확인 필요 사실을 즉시 운영자에게 알린다.",
                    "자동 복귀 전에 안전 해제 조건을 명확히 유지할 수 있다.",
                    5,
                ),
            ],
            "skipped_actions": skipped_actions,
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [follow_up("operator_confirm", 0, follow_up_description)],
            "confidence": 0.94,
            "retrieval_coverage": "sufficient",
            "citations": [citation(chunk_id) for chunk_id in retrieved_context],
        },
    }


def make_sensor_sample(
    sample_number: int,
    growth_stage: str,
    zone_id: str,
    state_summary: str,
    active_constraints: list[str],
    retrieved_context: list[str],
    situation_summary: str,
    diagnosis: list[str],
    automation_target_id: str,
    follow_up_description: str,
    skipped_actions: list[dict[str, str]],
) -> dict[str, Any]:
    sample_id = f"state-judgement-{sample_number:03d}"
    return {
        "sample_id": sample_id,
        "task_type": "sensor_fault",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": growth_stage,
            "zone_id": zone_id,
            "state_summary": state_summary,
            "active_constraints": active_constraints,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": situation_summary,
            "risk_level": "unknown",
            "diagnosis": diagnosis,
            "recommended_actions": [
                action(
                    sample_id.replace("state-judgement", "state11"),
                    1,
                    "pause_automation",
                    "system",
                    automation_target_id,
                    "high",
                    False,
                    "핵심 센서 근거가 복구될 때까지 자동 제어를 일시 보류한다.",
                    "센서 fault 상태에서 잘못된 자동 명령이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    sample_id.replace("state-judgement", "state11"),
                    2,
                    "request_human_check",
                    "operator",
                    "duty-manager",
                    "medium",
                    False,
                    "센서 통신, 대체 센서, 수동 측정값을 함께 확인한다.",
                    "센서 fault와 실제 환경 이상을 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": skipped_actions,
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [follow_up("sensor_recheck", 5, follow_up_description)],
            "confidence": 0.58,
            "retrieval_coverage": "partial",
            "citations": [citation(chunk_id) for chunk_id in retrieved_context],
        },
    }


def robot_task(
    task_type: str,
    candidate_id: str,
    target_type: str,
    target_id: str,
    priority: str,
    approval_required: bool,
    reason: str,
) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "candidate_id": candidate_id,
        "target": {"target_type": target_type, "target_id": target_id},
        "priority": priority,
        "approval_required": approval_required,
        "reason": reason,
    }


def make_robot_sample(
    sample_number: int,
    growth_stage: str,
    zone_id: str,
    state_summary: str,
    candidates: list[dict[str, Any]],
    safety_context: dict[str, Any],
    retrieved_context: list[str],
    situation_summary: str,
    risk_level: str,
    robot_tasks: list[dict[str, Any]],
    skipped_candidates: list[dict[str, str]],
    requires_human_approval: bool,
    follow_check_type: str,
    follow_up_description: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "sample_id": f"robot-task-{sample_number:03d}",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": growth_stage,
            "zone_id": zone_id,
            "state_summary": state_summary,
            "candidates": candidates,
            "safety_context": safety_context,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": situation_summary,
            "risk_level": risk_level,
            "robot_tasks": robot_tasks,
            "skipped_candidates": skipped_candidates,
            "requires_human_approval": requires_human_approval,
            "follow_up": [follow_up(follow_check_type, 15 if follow_check_type == "visual_inspection" else 0, follow_up_description)],
            "confidence": confidence,
            "retrieval_coverage": "sufficient",
            "citations": [citation(chunk_id) for chunk_id in retrieved_context],
        },
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def build_safety_samples() -> list[dict[str, Any]]:
    scenarios = [
        (56, "harvest", "gh-01-zone-a", "수확 aisle-a에서 작업자가 선별 중이라 같은 구역 로봇 수확 제어를 허용하면 안 된다.", ["worker_present", "robot_zone_not_clear", "manual_sorting_active"], ["pepper-agent-001", "pepper-harvest-001"], "작업자 선별이 진행 중인 동안에는 수확 후보가 있어도 자동 로봇 작업보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서는 같은 aisle의 로봇 수확 작업을 즉시 차단해야 한다.", "수확 후보 존재는 자동 작업 재개 근거가 아니라 차단 유지 상태에서 대기할 이유다."], "작업자 퇴장과 aisle-a 안전구역 clear 상태를 확인한다.", [{"action_type": "create_robot_task", "reason": "작업자 선별 중에는 로봇 작업 생성 자체를 금지한다."}]),
        (57, "harvest", "gh-01-zone-b", "작업자가 수확 상자를 교체 중이고 harvest belt 수동 조작이 active라 자동 이송 제어를 걸면 안 된다.", ["worker_present", "manual_override_active", "harvest_belt_service"], ["pepper-agent-001", "pepper-harvest-001"], "작업자와 수동 조작이 동시에 active인 동안에는 자동 이송 제어보다 차단과 경고 유지가 우선이다.", ["manual override active 상태에서 자동 이송 제어를 재개하면 작업자 수동 조작과 충돌할 수 있다.", "작업자 상자 교체가 끝나기 전까지는 자동 복귀를 허용하면 안 된다."], "작업자 퇴장과 수동조작 해제 여부를 확인한다.", [{"action_type": "adjust_vent", "reason": "이 케이스의 핵심은 환기 조정이 아니라 수확 belt 자동화 차단이다."}]),
        (58, "drying", "gh-01-dry-room", "건조실에서 operator가 수동 감압 시험을 진행 중이라 자동 송풍 재개를 허용하면 안 된다.", ["manual_override_active", "dry_room_manual_test"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "건조실 수동 시험이 진행 중인 동안에는 품질 watch가 있어도 자동 송풍보다 차단과 경고 유지가 우선이다.", ["manual override active 상태에서는 AI가 건조실 송풍 제어를 덮어쓰면 안 된다.", "수동 시험이 끝나기 전 자동 송풍을 재개하면 건조실 검증 절차를 깨뜨릴 수 있다."], "건조실 수동 시험 종료와 override 해제를 확인한다.", [{"action_type": "enter_safe_mode", "reason": "이미 수동 시험 중인 상황이라 중복 safe mode 진입보다 차단 유지가 먼저다."}]),
        (59, "drying", "gh-01-dry-room", "작업자가 건조실 내부 점검 중이라 dehumidifier 자동 제어를 바로 걸 수 없다.", ["worker_present", "dry_room_manual_inspection"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "작업자 점검이 진행 중인 동안에는 건조실 품질 이슈가 있어도 자동 제어보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서 건조실 장치 제어를 재개하면 작업자 점검과 충돌할 수 있다.", "이 상황은 품질 최적화가 아니라 작업자 안전 확보가 우선이다."], "작업자 퇴장과 점검 종료 여부를 확인한다.", [{"action_type": "adjust_heating", "reason": "점검 중에는 추가 자동 장치 조정보다 차단 유지가 우선이다."}]),
        (60, "vegetative_growth", "gh-01-zone-a", "recent timeout 이후 safe mode가 latch된 상태라 operator 승인 전 자동 복귀를 허용하면 안 된다.", ["safe_mode_active", "reentry_pending"], ["pepper-agent-001"], "safe mode latch가 남아 있는 동안에는 환경이 안정적이어도 자동 복귀보다 차단과 경고 유지가 우선이다.", ["latched safe mode는 단순 watch가 아니라 복귀 승인 절차가 남았다는 의미다.", "이 시점에는 추가 제어보다 차단 상태와 복귀 조건 확인이 먼저다."], "safe mode 해제 승인과 상태 동기화 완료 여부를 확인한다.", [{"action_type": "enter_safe_mode", "reason": "이미 safe mode가 active이므로 중복 진입 대신 차단 유지가 우선이다."}]),
        (61, "fruiting", "gh-01-zone-c", "fertigation line을 운영자가 수동 세척 중이라 자동 양액 재개를 허용하면 안 된다.", ["manual_override_active", "fertigation_manual_flush"], ["pepper-hydroponic-001", "pepper-agent-001"], "수동 세척이 진행 중인 동안에는 근권 지표가 있어도 자동 양액보다 차단과 경고 유지가 우선이다.", ["fertigation manual flush 중 자동 양액 제어를 재개하면 라인 세척과 충돌할 수 있다.", "수동 세척 해제 전에는 recipe 변경이나 관수 재개를 허용하면 안 된다."], "수동 세척 종료와 override 해제 여부를 확인한다.", [{"action_type": "adjust_fertigation", "reason": "세척 중에는 recipe 변경보다 자동 제어 차단이 먼저다."}]),
        (62, "fruit_expansion", "gh-01-zone-b", "작업자가 열매 예찰을 위해 row-b 내부에 진입해 있어 로봇 inspect를 허용하면 안 된다.", ["worker_present", "robot_zone_not_clear", "manual_scouting_active"], ["pepper-pest-001", "pepper-agent-001"], "작업자 예찰이 진행 중인 동안에는 로봇 inspect보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서는 같은 row 내부 로봇 inspect를 차단해야 한다.", "예찰 진행 사실은 inspect 생성 근거가 아니라 안전 대기 근거다."], "예찰 종료와 row-b 안전구역 clear 상태를 확인한다.", [{"action_type": "create_robot_task", "reason": "작업자 예찰 중에는 inspect task 생성 자체를 보류해야 한다."}]),
        (63, "flowering", "gh-01-zone-a", "operator가 CO2 doser를 수동 튜닝 중이라 자동 투입 재개를 허용하면 안 된다.", ["manual_override_active", "co2_manual_tuning"], ["pepper-climate-001", "pepper-agent-001"], "수동 CO2 튜닝이 진행 중인 동안에는 자동 투입보다 차단과 경고 유지가 우선이다.", ["manual override active 상태에서 AI가 CO2 doser를 다시 제어하면 수동 보정과 충돌할 수 있다.", "수동 튜닝 종료 전에는 자동 재개를 허용하면 안 된다."], "CO2 수동 튜닝 종료와 override 해제 여부를 확인한다.", [{"action_type": "adjust_fan", "reason": "핵심은 환기 조정보다 수동 튜닝과 자동 제어 충돌 차단이다."}]),
        (64, "flowering", "gh-01-zone-a", "작업자가 vent linkage 점검 중이라 환기창 자동 구동을 허용하면 안 된다.", ["worker_present", "vent_service_active"], ["pepper-climate-001", "pepper-agent-001"], "환기창 점검이 진행 중인 동안에는 기후 조정보다 차단과 경고 유지가 우선이다.", ["작업자가 linkage를 점검하는 동안 환기창 자동 구동은 즉시 차단해야 한다.", "이 상황의 핵심은 기후 최적화가 아니라 작업자 안전 확보다."], "환기창 점검 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "adjust_vent", "reason": "점검 중에는 환기창 자동 구동을 허용하면 안 된다."}]),
        (65, "fruit_expansion", "gh-01-zone-b", "작업자가 fogging nozzle을 교체 중이라 자동 미세안개 제어를 허용하면 안 된다.", ["worker_present", "fogging_service_active"], ["pepper-agent-001"], "노즐 교체가 진행 중인 동안에는 자동 미세안개 제어보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서 분무 라인을 구동하면 작업자 안전과 장치 점검에 모두 불리하다.", "교체 종료 전에는 자동 제어를 차단 유지해야 한다."], "노즐 교체 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "create_alert", "reason": "알림만으로 끝내면 자동 제어가 다시 들어갈 수 있어 block_action이 필요하다."}]),
        (66, "drying", "gh-01-dry-room", "manual override와 safe mode가 동시에 active인 상태에서 운영자가 belt 복구를 진행 중이다.", ["manual_override_active", "safe_mode_active", "operator_recovery_in_progress"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "manual override와 safe mode가 동시에 active인 동안에는 추가 자동 명령보다 차단과 경고 유지가 우선이다.", ["manual override와 safe mode 동시 active는 AI가 추가 제어를 시도하면 안 되는 대표적 hard block 상황이다.", "이 시점의 핵심은 수동 복구가 끝날 때까지 자동 명령을 차단 유지하는 것이다."], "건조실 belt 복구 종료와 override 해제 여부를 확인한다.", [{"action_type": "request_human_check", "reason": "운영자 복구가 이미 진행 중이므로 필수 조합은 block_action과 create_alert다."}]),
        (67, "vegetative_growth", "gh-01-zone-c", "climate controller timeout 이후 safe mode가 active라 operator 승인 전 자동 fan 복귀를 허용하면 안 된다.", ["safe_mode_active", "climate_timeout_recovery"], ["pepper-climate-001", "pepper-agent-001"], "timeout recovery 중인 safe mode 상태에서는 자동 fan 복귀보다 차단과 경고 유지가 우선이다.", ["timeout recovery가 끝나기 전 fan 자동 복귀를 시도하면 fault 원인 파악이 꼬일 수 있다.", "safe mode 해제 승인 전에는 자동 제어 재개를 금지해야 한다."], "climate controller timeout 원인 정리와 safe mode 해제 승인 여부를 확인한다.", [{"action_type": "adjust_fan", "reason": "safe mode recovery 중에는 자동 fan 명령을 허용하면 안 된다."}]),
        (68, "harvest", "gh-01-zone-a", "작업자가 robot battery를 교체 중이라 수확 로봇 task 재개를 허용하면 안 된다.", ["worker_present", "robot_service_active"], ["pepper-harvest-001", "pepper-agent-001"], "로봇 서비스가 진행 중인 동안에는 수확 후보가 있어도 차단과 경고 유지가 우선이다.", ["robot service active 상태에서는 로봇 task planner를 차단해야 한다.", "수확 후보 존재는 서비스 종료 전 자동 재개 근거가 아니다."], "배터리 교체 종료와 robot zone clear 상태를 확인한다.", [{"action_type": "create_robot_task", "reason": "로봇 서비스 중에는 task 생성 자체를 금지해야 한다."}]),
        (69, "flowering", "gh-01-zone-b", "작업자가 heater 점검을 위해 배선함을 열어 둔 상태라 자동 난방 명령을 허용하면 안 된다.", ["worker_present", "heater_service_active"], ["pepper-climate-001", "pepper-agent-001"], "heater 점검이 진행 중인 동안에는 온도 리스크가 있어도 자동 난방보다 차단과 경고 유지가 우선이다.", ["작업자가 배선함을 열어 둔 상태에서 난방기를 자동 구동하면 안 된다.", "점검 종료 전에는 온도 제어보다 작업자 안전이 우선이다."], "heater 점검 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "adjust_heating", "reason": "점검 중에는 난방 자동 제어를 차단해야 한다."}]),
        (70, "fruiting", "gh-01-zone-c", "작업자가 shade motor를 정렬 중이라 차광 커튼 자동 제어를 허용하면 안 된다.", ["worker_present", "shade_service_active"], ["pepper-climate-001", "pepper-agent-001"], "차광 모터 정렬이 진행 중인 동안에는 자동 차광보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서 shade motor를 자동 구동하면 작업자와 장치 충돌 위험이 있다.", "정렬 종료 전에는 자동 차광 복귀를 금지해야 한다."], "차광 모터 정렬 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "adjust_shade", "reason": "정렬 중에는 차광 커튼 자동 구동을 허용하면 안 된다."}]),
        (71, "drying", "gh-01-dry-room", "operator가 dehumidifier를 수동 시험 중이라 자동 제습 재개를 허용하면 안 된다.", ["manual_override_active", "dehumidifier_manual_test"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "수동 제습 시험이 진행 중인 동안에는 자동 제습보다 차단과 경고 유지가 우선이다.", ["manual override active 상태에서 자동 제습을 재개하면 수동 시험 절차와 충돌한다.", "시험 종료 전에는 자동 제습 명령을 차단해야 한다."], "제습기 수동 시험 종료와 override 해제 여부를 확인한다.", [{"action_type": "adjust_heating", "reason": "건조실 품질 조정 이전에 자동 제어 차단을 먼저 유지해야 한다."}]),
        (72, "transplanting", "gh-01-zone-b", "작업자가 irrigation line flush를 진행 중이라 자동 활착 관수를 허용하면 안 된다.", ["worker_present", "irrigation_line_flush"], ["pepper-rootzone-001", "pepper-agent-001"], "관수 라인 세척이 진행 중인 동안에는 활착 관리가 필요해도 자동 관수보다 차단과 경고 유지가 우선이다.", ["세척 중 자동 활착 관수를 재개하면 flush 절차와 충돌한다.", "라인 세척 종료 전에는 자동 관수를 차단해야 한다."], "관수 라인 flush 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "short_irrigation", "reason": "flush 중에는 자동 관수를 허용하면 안 된다."}]),
        (73, "fruit_set", "gh-01-zone-a", "operator가 source water valve를 수동 복구 중이라 자동 원수 제어를 허용하면 안 된다.", ["manual_override_active", "source_water_manual_recovery"], ["pepper-hydroponic-001", "pepper-agent-001"], "원수 수동 복구가 진행 중인 동안에는 자동 원수 제어보다 차단과 경고 유지가 우선이다.", ["manual override active 상태에서 source water 제어를 다시 걸면 복구 절차와 충돌할 수 있다.", "원수 복구 종료 전에는 자동 제어를 차단해야 한다."], "원수 수동 복구 종료와 override 해제 여부를 확인한다.", [{"action_type": "adjust_fertigation", "reason": "원수 복구 중에는 양액 조정보다 자동 차단이 우선이다."}]),
        (74, "harvest", "gh-01-zone-c", "작업자가 병해 예찰 중이라 같은 row의 inspect robot task를 허용하면 안 된다.", ["worker_present", "manual_scouting_active", "robot_zone_not_clear"], ["pepper-pest-001", "pepper-agent-001"], "병해 예찰이 진행 중인 동안에는 inspect robot task보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서 같은 row의 inspect robot task는 차단해야 한다.", "예찰 중인 row는 사람이 먼저 판단해야 하므로 자동 로봇 접근을 금지한다."], "병해 예찰 종료와 robot zone clear 상태를 확인한다.", [{"action_type": "create_robot_task", "reason": "병해 예찰 중에는 inspect task 생성 자체를 보류해야 한다."}]),
        (75, "drying", "gh-01-dry-room", "작업자가 건조실 세척을 진행 중이라 dry fan 자동 제어를 허용하면 안 된다.", ["worker_present", "sanitation_washdown_active"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "세척 작업이 진행 중인 동안에는 품질 제어보다 차단과 경고 유지가 우선이다.", ["worker_present 상태에서 dry fan 자동 제어를 재개하면 세척 작업과 충돌한다.", "세척 종료 전에는 건조실 자동 제어를 차단해야 한다."], "세척 종료와 작업자 퇴장 여부를 확인한다.", [{"action_type": "adjust_fan", "reason": "세척 중에는 송풍 자동 제어보다 차단 유지가 우선이다."}]),
    ]
    return [make_safety_sample(*scenario) for scenario in scenarios]


def build_sensor_samples() -> list[dict[str, Any]]:
    scenarios = [
        (76, "flowering", "gh-01-zone-a", "온도 센서가 stale이고 습도 추세와 VPD 계산이 서로 맞지 않아 기후 판단 근거가 무너졌다.", ["air_temp_stale", "temp_humidity_inconsistent"], ["pepper-climate-001", "pepper-agent-001"], "핵심 기후 센서 stale와 상호 불일치가 함께 발생해 자동 기후 판단을 정상 위험도로 단정할 수 없다.", ["온도 센서 stale 상태에서는 환기와 차광 판단 근거가 무너진다.", "습도와 VPD가 함께 어긋나면 실제 고온인지 센서 fault인지 즉시 구분하기 어렵다."], "gh-01-zone-a-auto-control", "온도 센서 최신값, 대체 센서, 현장 체감온도를 확인한다.", [{"action_type": "adjust_vent", "reason": "핵심 온도 근거가 없는 상태에서 자동 환기 제어를 바로 실행하면 안 된다."}]),
        (77, "fruit_set", "gh-01-zone-a", "야간 습도 센서가 missing이라 결로 위험 판단 근거가 부족하다.", ["humidity_sensor_missing", "night_condensation_watch"], ["pepper-climate-001", "pepper-agent-001"], "야간 핵심 습도 센서가 missing이라 자동 결로 대응을 정상 위험도로 단정할 수 없다.", ["야간 결로 판단은 습도 센서가 핵심 근거인데 현재 missing 상태다.", "실제 결로인지 센서 fault인지 수동 확인이 먼저다."], "gh-01-zone-a-auto-control", "습도 센서 통신 상태와 수동 결로 여부를 확인한다.", [{"action_type": "adjust_fan", "reason": "습도 근거가 없는 상태에서 자동 송풍을 강화하면 과건조를 유발할 수 있다."}]),
        (78, "flowering", "gh-01-zone-c", "CO2 센서가 flatline이고 backup 센서와 180ppm 이상 벌어져 자동 CO2 판단을 신뢰하기 어렵다.", ["co2_flatline", "co2_backup_inconsistent"], ["pepper-climate-001", "pepper-agent-001"], "CO2 센서 flatline와 backup 불일치가 함께 발생해 자동 CO2 판단을 정상 위험도로 단정할 수 없다.", ["CO2 센서 flatline 상태에서는 실제 저CO2인지 센서 fault인지 즉시 구분하기 어렵다.", "backup 센서와 큰 차이가 나면 자동 투입보다 센서 확인이 우선이다."], "gh-01-zone-c-auto-control", "CO2 센서 통신, backup 센서, 현장 측정값을 확인한다.", [{"action_type": "adjust_fertigation", "reason": "현재 문제는 양액이 아니라 CO2 센서 신뢰도다."}]),
        (79, "flowering", "gh-01-zone-a", "PAR 센서가 flatline이고 차광 상태와 일사량 체감이 맞지 않는다.", ["par_flatline", "radiation_inconsistent"], ["pepper-climate-001", "pepper-agent-001"], "광 센서 flatline와 차광 불일치가 발생해 자동 차광 판단을 정상 위험도로 단정할 수 없다.", ["PAR 센서 flatline이면 차광 제어 근거가 무너진다.", "현재 일사 감각과 센서가 맞지 않아 자동 차광보다 수동 확인이 우선이다."], "gh-01-zone-a-auto-control", "PAR 센서 최신값과 실제 일사 상태를 확인한다.", [{"action_type": "adjust_shade", "reason": "광 센서 근거가 없는 상태에서 자동 차광을 바로 걸면 안 된다."}]),
        (80, "transplanting", "gh-01-zone-b", "정식 직후 slab 함수율 센서가 missing이라 활착 관수 판단 근거가 부족하다.", ["slab_wc_missing", "transplant_establishment"], ["pepper-rootzone-001", "pepper-agent-001"], "활착 초기 핵심 함수율 센서가 missing이라 자동 관수 판단을 정상 위험도로 단정할 수 없다.", ["정식 직후에는 slab 함수율 센서가 핵심 판단 근거다.", "실제 과건조와 센서 fault를 즉시 구분하기 어려워 자동 관수보다 현장 확인이 먼저다."], "gh-01-zone-b-irrigation-auto-control", "slab 함수율 센서 통신 상태와 수동 측정값을 확인한다.", [{"action_type": "short_irrigation", "reason": "핵심 함수율 센서 missing 상태에서는 자동 관수를 실행하면 안 된다."}]),
        (81, "fruit_expansion", "gh-01-zone-b", "배액 EC 센서가 stale라 최근 염류 상승 신호를 자동으로 확정하기 어렵다.", ["drain_ec_stale", "fertigation_evidence_incomplete"], ["pepper-hydroponic-001", "pepper-agent-001"], "배액 EC 센서 stale 상태라 자동 근권 염류 판단을 정상 위험도로 단정할 수 없다.", ["배액 EC는 근권 염류 판단 핵심 근거인데 현재 stale 상태다.", "센서 복구 전에는 세척 여부를 자동으로 결정하면 안 된다."], "gh-01-zone-b-fertigation-auto-control", "배액 EC 수동 측정값과 센서 최신값을 확인한다.", [{"action_type": "adjust_fertigation", "reason": "배액 EC 근거가 stale인 상태에서 recipe를 자동 조정하면 안 된다."}]),
        (82, "fruit_expansion", "gh-01-zone-b", "배액량 센서가 flatline이라 실제 배수 회복 여부를 자동으로 판단하기 어렵다.", ["drain_volume_flatline", "rootzone_evidence_incomplete"], ["pepper-rootzone-001", "pepper-hydroponic-001"], "배액량 센서 flatline 상태라 자동 배수 회복 판단을 정상 위험도로 단정할 수 없다.", ["배액량 flatline이면 실제 배수 회복과 정체를 구분하기 어렵다.", "센서 복구 전에는 관수 패턴을 자동 조정하면 안 된다."], "gh-01-zone-b-rootzone-auto-control", "배액량 수동 측정값과 센서 통신 상태를 확인한다.", [{"action_type": "short_irrigation", "reason": "배액량 근거가 없는 상태에서 추가 관수를 자동 실행하면 안 된다."}]),
        (83, "nursery", "gh-01-zone-a", "육묘 구역 온도 센서 calibration error가 발생해 보온 판단을 신뢰하기 어렵다.", ["air_temp_calibration_error", "nursery_temp_watch"], ["pepper-climate-001", "pepper-agent-001"], "육묘 구역 핵심 온도 센서 calibration error로 자동 보온 판단을 정상 위험도로 단정할 수 없다.", ["calibration error가 있는 온도 센서는 보온 판단 근거로 쓰면 안 된다.", "육묘 구역은 작은 온도 오차도 영향이 커 수동 검증이 우선이다."], "gh-01-zone-a-auto-control", "육묘 구역 온도 센서 보정 상태와 대체 온도계를 확인한다.", [{"action_type": "adjust_heating", "reason": "보정 실패 센서 기준으로 자동 난방을 바로 걸면 안 된다."}]),
        (84, "drying", "gh-01-dry-room", "건조실 습도 센서가 jump를 반복해 실제 재흡습인지 센서 fault인지 구분이 어렵다.", ["dry_room_humidity_jump", "rehydration_watch"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "건조실 습도 센서 jump 반복으로 자동 건조 판단을 정상 위험도로 단정할 수 없다.", ["습도 jump가 반복되면 실제 재흡습과 센서 fault를 즉시 구분하기 어렵다.", "건조실은 품질 영향이 커 수동 확인 전 자동 조정이 위험하다."], "gh-01-dry-room-auto-control", "건조실 습도 수동 측정값과 센서 drift 여부를 확인한다.", [{"action_type": "adjust_fan", "reason": "jump 반복 상태에서 송풍을 자동 강화하면 과건조 또는 품질 편차를 키울 수 있다."}]),
        (85, "flowering", "gh-01-zone-c", "주 CO2 센서와 backup 센서가 서로 반대 추세를 보여 실제 CO2 상태를 자동 확정하기 어렵다.", ["co2_mutual_inconsistency", "backup_sensor_conflict"], ["pepper-climate-001", "pepper-agent-001"], "CO2 센서 상호 불일치로 자동 CO2 상태 판단을 정상 위험도로 단정할 수 없다.", ["주 센서와 backup 센서가 반대 추세면 실제 CO2 변화를 신뢰하기 어렵다.", "센서 fault 해소 전에는 자동 투입 제어보다 수동 검증이 먼저다."], "gh-01-zone-c-auto-control", "주 CO2 센서와 backup 센서의 최근 로그를 비교 확인한다.", [{"action_type": "adjust_fan", "reason": "이 상황은 환기 조정보다 CO2 센서 검증이 우선이다."}]),
        (86, "vegetative_growth", "gh-01-zone-a", "온도는 낮다고 보고하지만 상대습도와 VPD 계산이 물리적으로 맞지 않아 센서 조합을 신뢰하기 어렵다.", ["temp_humidity_physics_mismatch", "vpd_invalid"], ["pepper-climate-001", "pepper-agent-001"], "온습도 조합이 물리적으로 맞지 않아 자동 기후 판단을 정상 위험도로 단정할 수 없다.", ["온습도 조합이 물리적으로 불가능한 값이면 센서 fault를 우선 의심해야 한다.", "VPD 계산이 무너진 상태에서는 기후 제어 추천을 자동 실행하면 안 된다."], "gh-01-zone-a-auto-control", "온습도 센서 쌍의 최근값과 대체 측정기를 비교 확인한다.", [{"action_type": "adjust_vent", "reason": "VPD 근거가 무너진 상태에서 자동 환기를 바로 조정하면 안 된다."}]),
        (87, "fruit_set", "gh-01-zone-b", "최근 관수 이후 slab 함수율 센서가 같은 값으로 고정돼 실제 회복 여부를 판단하기 어렵다.", ["slab_wc_flatline", "post_irrigation_recovery_unknown"], ["pepper-rootzone-001", "pepper-hydroponic-001"], "관수 이후 slab 함수율 센서 flatline로 자동 회복 판단을 정상 위험도로 단정할 수 없다.", ["관수 직후에도 함수율이 고정이면 센서 flatline 가능성이 크다.", "센서 복구 전에는 추가 관수나 양액 조정보다 확인이 먼저다."], "gh-01-zone-b-rootzone-auto-control", "관수 직후 slab 함수율 수동 측정과 센서 로그를 확인한다.", [{"action_type": "short_irrigation", "reason": "함수율 회복 근거가 없는 상태에서 추가 관수를 자동 실행하면 안 된다."}]),
        (88, "fruit_expansion", "gh-01-zone-b", "배액 pH 센서가 missing이라 급액-배액 괴리를 자동 판단하기 어렵다.", ["drain_ph_missing", "fertigation_evidence_incomplete"], ["pepper-hydroponic-001", "pepper-agent-001"], "배액 pH 센서 missing으로 자동 양액 괴리 판단을 정상 위험도로 단정할 수 없다.", ["배액 pH는 양액 불균형 판단 핵심 근거인데 missing 상태다.", "센서 복구 전에는 자동 recipe 조정보다 수동 측정이 우선이다."], "gh-01-zone-b-fertigation-auto-control", "배액 pH 수동 측정값과 센서 통신 상태를 확인한다.", [{"action_type": "adjust_fertigation", "reason": "배액 pH 근거가 없는 상태에서 자동 recipe 조정을 하면 안 된다."}]),
        (89, "flowering", "gh-01-zone-c", "외부 radiation 센서가 stale라 일사 급상승 여부를 자동 판단하기 어렵다.", ["outside_radiation_stale", "sunload_watch"], ["pepper-climate-001", "pepper-agent-001"], "외부 radiation 센서 stale로 자동 일사 판단을 정상 위험도로 단정할 수 없다.", ["외부 radiation 센서 stale면 일사 급상승 여부를 자동 확정할 수 없다.", "센서 복구 전에는 차광과 환기 조합을 자동으로 확대하면 안 된다."], "gh-01-zone-c-auto-control", "외부 radiation 센서 최신값과 실제 일사 상태를 확인한다.", [{"action_type": "adjust_shade", "reason": "외부 radiation 근거가 stale인 상태에서 자동 차광을 바로 강화하면 안 된다."}]),
        (90, "flowering", "gh-01-zone-a", "canopy temperature 센서가 missing이라 열스트레스 hotspot 판단 근거가 부족하다.", ["canopy_temp_missing", "heat_stress_hotspot_unknown"], ["pepper-climate-001", "pepper-agent-001"], "canopy temperature 센서 missing으로 자동 열스트레스 hotspot 판단을 정상 위험도로 단정할 수 없다.", ["canopy temperature는 열스트레스 hotspot 판단 핵심 근거인데 missing 상태다.", "센서 복구 전에는 hotspot 대응을 자동으로 걸면 안 된다."], "gh-01-zone-a-auto-control", "canopy temperature 대체 측정과 hotspot 구역 체감 온도를 확인한다.", [{"action_type": "adjust_fan", "reason": "hotspot 근거가 없는 상태에서 자동 송풍 강화만으로 판단하면 안 된다."}]),
        (91, "fruit_set", "gh-01-zone-b", "rootzone temperature 센서가 야간 내내 missing이라 난방 영향 판단 근거가 부족하다.", ["rootzone_temp_missing", "night_rootzone_watch"], ["pepper-rootzone-001", "pepper-agent-001"], "근권 온도 센서 missing으로 야간 난방 영향 판단을 정상 위험도로 단정할 수 없다.", ["근권 온도 센서는 야간 난방 영향 판단의 핵심 근거다.", "missing 상태에서는 난방과 관수 조합을 자동으로 바꾸면 안 된다."], "gh-01-zone-b-rootzone-auto-control", "근권 온도 대체 측정값과 센서 통신 상태를 확인한다.", [{"action_type": "adjust_heating", "reason": "근권 온도 근거가 없는 상태에서 자동 난방을 바로 조정하면 안 된다."}]),
        (92, "fruit_expansion", "gh-01-mixing-room", "source water EC 센서가 stale라 원수 염도 변화를 자동 판단하기 어렵다.", ["source_water_ec_stale", "mixing_input_unknown"], ["pepper-hydroponic-001", "pepper-agent-001"], "원수 EC 센서 stale로 양액 혼합 입력 상태를 정상 위험도로 단정할 수 없다.", ["원수 EC는 recipe 입력값인데 stale 상태면 자동 혼합을 신뢰하면 안 된다.", "센서 복구 전에는 자동 recipe 계산보다 수동 측정이 우선이다."], "gh-01-mixing-room-fertigation-auto-control", "원수 EC 수동 측정값과 센서 최신 로그를 확인한다.", [{"action_type": "adjust_fertigation", "reason": "원수 EC 근거가 stale이면 자동 recipe 계산을 바로 실행하면 안 된다."}]),
        (93, "fruit_expansion", "gh-01-zone-b", "배액률 센서가 0으로 고정돼 실제 배액 회복 여부를 자동 판단하기 어렵다.", ["drain_ratio_stuck_zero", "rootzone_evidence_incomplete"], ["pepper-rootzone-001", "pepper-hydroponic-001"], "배액률 센서 0 고정으로 자동 배수 회복 판단을 정상 위험도로 단정할 수 없다.", ["배액률 센서가 0으로 고정되면 실제 무배액인지 센서 fault인지 구분하기 어렵다.", "센서 복구 전에는 관수 pulse 조정이 아니라 확인이 우선이다."], "gh-01-zone-b-rootzone-auto-control", "배액률 수동 측정과 센서 drift 여부를 확인한다.", [{"action_type": "short_irrigation", "reason": "배액률 근거가 없는 상태에서 추가 관수 pulse를 자동 실행하면 안 된다."}]),
        (94, "flowering", "gh-01-roof", "weather station 풍속 센서가 stale라 강풍 시 vent 제약 판단 근거가 부족하다.", ["wind_sensor_stale", "vent_lock_uncertain"], ["pepper-climate-001", "pepper-agent-001"], "풍속 센서 stale로 vent 제약 여부를 정상 위험도로 단정할 수 없다.", ["강풍 시 vent lock 판단은 풍속 센서가 핵심 근거인데 stale 상태다.", "센서 복구 전에는 자동 vent 개폐를 확대하면 안 된다."], "gh-01-zone-a-auto-control", "풍속 센서 최신값과 외부 체감 바람 상태를 확인한다.", [{"action_type": "adjust_vent", "reason": "풍속 근거가 stale인 상태에서 자동 vent 제어를 바꾸면 안 된다."}]),
        (95, "drying", "gh-01-dry-room", "건조실 습도 센서가 flatline이라 재흡습 watch를 자동 판단하기 어렵다.", ["dry_room_humidity_flatline", "rehydration_watch"], ["pepper-house-drying-hygiene-001", "pepper-agent-001"], "건조실 습도 센서 flatline로 자동 재흡습 판단을 정상 위험도로 단정할 수 없다.", ["건조실 습도 센서 flatline이면 실제 재흡습과 센서 fault를 즉시 구분하기 어렵다.", "센서 복구 전에는 자동 제습이나 송풍 강화를 바로 걸면 안 된다."], "gh-01-dry-room-auto-control", "건조실 습도 수동 측정값과 센서 통신 상태를 확인한다.", [{"action_type": "adjust_fan", "reason": "습도 근거가 없는 상태에서 자동 송풍을 바로 강화하면 안 된다."}]),
    ]
    return [make_sensor_sample(*scenario) for scenario in scenarios]


def build_robot_samples() -> list[dict[str, Any]]:
    return [
        make_robot_sample(25, "harvest", "gh-01-zone-a", "숙도 높은 수확 후보가 aisle-a 전면에 있고 작업자 출입은 없다.", [{"candidate_id": "cand-71", "ripeness_score": 0.97, "disease_score": 0.03, "reachable": True}, {"candidate_id": "cand-72", "ripeness_score": 0.94, "disease_score": 0.05, "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001"], "명확한 수확 후보가 있고 안전 조건이 충족돼 review 기반 수확 task를 생성할 수 있다.", "medium", [robot_task("harvest_candidate_review", "cand-71", "candidate", "cand-71", "high", True, "숙도 score가 가장 높고 도달 가능하다."), robot_task("harvest_candidate_review", "cand-72", "candidate", "cand-72", "medium", True, "숙도는 높지만 병징 여부를 함께 확인해야 한다.")], [], True, "visual_inspection", "상위 수확 후보의 실제 숙도와 병징 여부를 확인한다.", 0.82),
        make_robot_sample(26, "fruiting", "gh-01-zone-b", "국소 병해 의심 hotspot이 row-b 끝단에 표시됐다.", [{"candidate_id": "hotspot-11", "disease_score": 0.74, "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-agent-001"], "병해 의심 hotspot은 inspect 기반 로봇 task로 등록할 수 있다.", "medium", [robot_task("inspect_crop", "hotspot-11", "zone", "gh-01-zone-b-hotspot-11", "high", True, "의심 hotspot을 먼저 재확인해야 한다.")], [], True, "visual_inspection", "inspect 후보 구역의 실제 병징 여부를 확인한다.", 0.8),
        make_robot_sample(27, "harvest", "gh-01-zone-b", "aisle-b 바닥이 젖어 있어 해당 구역은 임시 우회가 필요하다.", [{"candidate_id": "aisle-b-wet", "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-agent-001"], "접근 위험 구간은 수확 task보다 우회 task를 먼저 생성해야 한다.", "high", [robot_task("skip_area", "aisle-b-wet", "zone", "gh-01-zone-b-aisle-b", "high", True, "젖은 통로는 미끄럼 위험이 있어 우회가 우선이다.")], [], True, "operator_confirm", "통로 건조 여부와 우회 해제 가능 시점을 확인한다.", 0.84),
        make_robot_sample(28, "harvest", "gh-01-zone-c", "숙도 후보는 많지만 비전 confidence가 낮아 자동 수확보다 수동 검토가 우선이다.", [{"candidate_id": "cand-73", "ripeness_score": 0.85, "disease_score": 0.04, "reachable": True, "vision_confidence": 0.38}, {"candidate_id": "cand-74", "ripeness_score": 0.83, "disease_score": 0.05, "reachable": True, "vision_confidence": 0.41}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001", "pepper-agent-001"], "비전 confidence가 낮아 자동 수확 후보보다 manual review task를 먼저 생성해야 한다.", "medium", [robot_task("manual_review", "cand-73", "candidate", "cand-73", "high", True, "비전 confidence가 낮아 수동 검토가 우선이다."), robot_task("manual_review", "cand-74", "candidate", "cand-74", "medium", True, "동일 구역 다른 후보도 confidence가 낮다.")], [], True, "visual_inspection", "낮은 confidence 후보의 실제 숙도와 병징 여부를 확인한다.", 0.79),
        make_robot_sample(29, "harvest", "gh-01-zone-a", "수확 후보는 있으나 작업자가 aisle-a 내부에서 박스 적재 중이다.", [{"candidate_id": "cand-75", "ripeness_score": 0.96, "disease_score": 0.02, "reachable": True}], {"worker_present": True, "robot_zone_clear": False}, ["pepper-agent-001", "pepper-harvest-001"], "작업자 출입이 active인 동안에는 로봇 수확 task를 생성하면 안 된다.", "critical", [], [{"candidate_id": "cand-75", "reason": "작업자 적재 작업이 진행 중이라 robot zone이 clear하지 않다."}], False, "operator_confirm", "작업자 퇴장과 aisle-a 안전구역 clear 상태를 확인한다.", 0.9),
        make_robot_sample(30, "fruiting", "gh-01-zone-b", "inspect 후보는 있으나 row-b에 작업자가 예찰 중이라 접근이 불가하다.", [{"candidate_id": "hotspot-12", "disease_score": 0.77, "reachable": True}], {"worker_present": True, "robot_zone_clear": False}, ["pepper-pest-001", "pepper-agent-001"], "작업자 예찰 중인 구역은 inspect 후보가 있어도 로봇 task를 생성하면 안 된다.", "critical", [], [{"candidate_id": "hotspot-12", "reason": "작업자 예찰이 active인 동안에는 inspect 접근을 금지한다."}], False, "operator_confirm", "예찰 종료와 row-b robot zone clear 상태를 확인한다.", 0.91),
        make_robot_sample(31, "harvest", "gh-01-zone-c", "숙도 높은 후보가 단일 cluster에 모여 있어 우선 검토 대상으로 적합하다.", [{"candidate_id": "cand-76", "ripeness_score": 0.98, "disease_score": 0.03, "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001"], "단일 cluster의 숙도 높은 후보는 harvest review task로 우선 등록할 수 있다.", "medium", [robot_task("harvest_candidate_review", "cand-76", "candidate", "cand-76", "high", True, "숙도 score와 도달성이 모두 높아 우선 검토 대상이다.")], [], True, "visual_inspection", "단일 cluster 후보의 실제 숙도와 병징 여부를 확인한다.", 0.83),
        make_robot_sample(32, "fruiting", "gh-01-zone-a", "병해 의심 hotspot 두 곳이 있으나 한 곳은 confidence가 낮아 수동 확인이 필요하다.", [{"candidate_id": "hotspot-13", "disease_score": 0.81, "reachable": True, "vision_confidence": 0.72}, {"candidate_id": "hotspot-14", "disease_score": 0.68, "reachable": True, "vision_confidence": 0.42}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-agent-001"], "고신뢰 hotspot은 inspect, 저신뢰 hotspot은 manual review로 분기해야 한다.", "medium", [robot_task("inspect_crop", "hotspot-13", "zone", "gh-01-zone-a-hotspot-13", "high", True, "병해 의심 score와 confidence가 모두 높다."), robot_task("manual_review", "hotspot-14", "zone", "gh-01-zone-a-hotspot-14", "medium", True, "confidence가 낮아 수동 검토가 우선이다.")], [], True, "visual_inspection", "두 hotspot의 실제 병징 여부를 각각 확인한다.", 0.81),
        make_robot_sample(33, "harvest", "gh-01-zone-b", "aisle-c 끝단이 pallet로 막혀 있어 해당 후보는 우회가 필요하다.", [{"candidate_id": "cand-77", "ripeness_score": 0.93, "disease_score": 0.04, "reachable": False}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-agent-001", "pepper-harvest-001"], "접근 불가 aisle은 수확 review보다 skip_area task를 먼저 생성해야 한다.", "high", [robot_task("skip_area", "cand-77", "zone", "gh-01-zone-b-aisle-c", "high", True, "pallet 적치로 접근이 불가해 우회가 우선이다.")], [], True, "operator_confirm", "pallet 제거 여부와 접근 가능 시점을 확인한다.", 0.85),
        make_robot_sample(34, "fruit_expansion", "gh-01-zone-c", "열매 hotspot은 보이지만 촬영 각도가 나빠 confidence가 낮다.", [{"candidate_id": "hotspot-15", "disease_score": 0.63, "reachable": True, "vision_confidence": 0.36}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-agent-001"], "confidence가 낮은 inspect 후보는 manual review로 우선 전환해야 한다.", "medium", [robot_task("manual_review", "hotspot-15", "zone", "gh-01-zone-c-hotspot-15", "high", True, "촬영 각도 문제로 confidence가 낮아 수동 검토가 우선이다.")], [], True, "visual_inspection", "촬영 각도 문제를 보정해 실제 병징 여부를 확인한다.", 0.77),
        make_robot_sample(35, "harvest", "gh-01-zone-a", "수확 후보가 있으나 작업자가 통로를 가로지르고 있어 즉시 실행은 불가하다.", [{"candidate_id": "cand-78", "ripeness_score": 0.95, "disease_score": 0.05, "reachable": True}], {"worker_present": True, "robot_zone_clear": False}, ["pepper-agent-001", "pepper-harvest-001"], "작업자 통로 횡단이 끝나기 전에는 로봇 수확 task를 생성하면 안 된다.", "critical", [], [{"candidate_id": "cand-78", "reason": "작업자 통로 횡단이 active라 접근이 불가하다."}], False, "operator_confirm", "작업자 통로 횡단 종료와 안전구역 clear 상태를 확인한다.", 0.9),
        make_robot_sample(36, "fruiting", "gh-01-zone-b", "병해 의심 후보와 수확 후보가 동시에 보이지만 inspect가 더 시급하다.", [{"candidate_id": "hotspot-16", "disease_score": 0.79, "reachable": True}, {"candidate_id": "cand-79", "ripeness_score": 0.92, "disease_score": 0.08, "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-harvest-001", "pepper-agent-001"], "병해 inspect 후보와 수확 후보가 동시에 있으면 inspect를 우선 task로 올려야 한다.", "high", [robot_task("inspect_crop", "hotspot-16", "zone", "gh-01-zone-b-hotspot-16", "high", True, "병해 의심 hotspot 확인이 수확보다 시급하다."), robot_task("harvest_candidate_review", "cand-79", "candidate", "cand-79", "medium", True, "수확 후보는 존재하지만 inspect 이후 검토가 적절하다.")], [], True, "visual_inspection", "병해 inspect 결과를 먼저 확인한 뒤 수확 후보를 검토한다.", 0.83),
        make_robot_sample(37, "harvest", "gh-01-zone-c", "숙도 후보는 많지만 camera blur로 일부 후보 confidence가 낮다.", [{"candidate_id": "cand-80", "ripeness_score": 0.94, "disease_score": 0.03, "reachable": True, "vision_confidence": 0.44}, {"candidate_id": "cand-81", "ripeness_score": 0.96, "disease_score": 0.02, "reachable": True, "vision_confidence": 0.76}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001", "pepper-agent-001"], "고신뢰 후보는 harvest review, 저신뢰 후보는 manual review로 분리해야 한다.", "medium", [robot_task("harvest_candidate_review", "cand-81", "candidate", "cand-81", "high", True, "숙도 score와 confidence가 모두 높다."), robot_task("manual_review", "cand-80", "candidate", "cand-80", "medium", True, "camera blur로 confidence가 낮아 수동 검토가 필요하다.")], [], True, "visual_inspection", "camera blur가 있었던 후보의 실제 숙도와 영상 품질을 확인한다.", 0.8),
        make_robot_sample(38, "fruiting", "gh-01-zone-a", "작업자가 클립 고정을 하고 있어 inspect robot 접근이 불가하다.", [{"candidate_id": "hotspot-17", "disease_score": 0.72, "reachable": True}], {"worker_present": True, "robot_zone_clear": False}, ["pepper-agent-001", "pepper-pest-001"], "작업자 클립 작업이 끝나기 전에는 inspect robot task를 생성하면 안 된다.", "critical", [], [{"candidate_id": "hotspot-17", "reason": "클립 작업으로 robot zone이 clear하지 않다."}], False, "operator_confirm", "클립 작업 종료와 안전구역 clear 상태를 확인한다.", 0.9),
        make_robot_sample(39, "harvest", "gh-01-zone-b", "하역 pallet이 aisle 일부를 막고 있어 해당 구역은 먼저 우회해야 한다.", [{"candidate_id": "cand-82", "ripeness_score": 0.91, "disease_score": 0.06, "reachable": False}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-agent-001", "pepper-harvest-001"], "하역 pallet이 막고 있는 구역은 harvest review보다 skip_area task가 먼저다.", "high", [robot_task("skip_area", "cand-82", "zone", "gh-01-zone-b-pallet-block", "high", True, "하역 pallet로 접근이 막혀 우회가 우선이다.")], [], True, "operator_confirm", "하역 pallet 이동과 aisle 접근 가능 시점을 확인한다.", 0.84),
        make_robot_sample(40, "fruiting", "gh-01-zone-c", "병해 의심 hotspot은 있으나 조명이 약해 재촬영 전 수동 검토가 필요하다.", [{"candidate_id": "hotspot-18", "disease_score": 0.67, "reachable": True, "vision_confidence": 0.33}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-agent-001"], "조명 부족으로 confidence가 낮은 hotspot은 manual review로 먼저 분기해야 한다.", "medium", [robot_task("manual_review", "hotspot-18", "zone", "gh-01-zone-c-hotspot-18", "high", True, "조명 부족으로 confidence가 낮아 수동 검토가 우선이다.")], [], True, "visual_inspection", "조명 상태를 보정해 hotspot 실제 병징 여부를 확인한다.", 0.76),
        make_robot_sample(41, "harvest", "gh-01-zone-a", "숙도 높은 후보가 연속으로 보이지만 작업 가능 시간은 하나만 승인 가능하다.", [{"candidate_id": "cand-83", "ripeness_score": 0.97, "disease_score": 0.02, "reachable": True}, {"candidate_id": "cand-84", "ripeness_score": 0.96, "disease_score": 0.03, "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001", "pepper-agent-001"], "작업 가능 시간이 제한되면 가장 시급한 harvest review 후보를 하나만 우선 승인해야 한다.", "medium", [robot_task("harvest_candidate_review", "cand-83", "candidate", "cand-83", "high", True, "숙도 score가 가장 높고 즉시 검토 가치가 크다.")], [{"candidate_id": "cand-84", "reason": "동일 시간대에는 상위 후보 하나만 먼저 승인한다."}], True, "visual_inspection", "우선 승인 후보의 실제 숙도와 병징 여부를 확인한다.", 0.82),
        make_robot_sample(42, "fruiting", "gh-01-zone-b", "inspect hotspot은 존재하지만 row 일부가 젖어 있어 특정 구역은 우회가 필요하다.", [{"candidate_id": "hotspot-19", "disease_score": 0.75, "reachable": True}, {"candidate_id": "row-b-wet", "reachable": True}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-pest-001", "pepper-agent-001"], "병해 inspect와 위험 구역 우회를 함께 관리해야 한다.", "high", [robot_task("inspect_crop", "hotspot-19", "zone", "gh-01-zone-b-hotspot-19", "high", True, "병해 의심 hotspot을 먼저 확인해야 한다."), robot_task("skip_area", "row-b-wet", "zone", "gh-01-zone-b-wet-area", "high", True, "젖은 구역은 접근보다 우회가 우선이다.")], [], True, "operator_confirm", "젖은 구역 건조 여부와 inspect 접근 가능 시점을 확인한다.", 0.83),
        make_robot_sample(43, "harvest", "gh-01-zone-c", "camera 오염으로 후보 두 개 모두 confidence가 낮아 자동 수확보다 수동 검토가 적절하다.", [{"candidate_id": "cand-85", "ripeness_score": 0.9, "disease_score": 0.04, "reachable": True, "vision_confidence": 0.35}, {"candidate_id": "cand-86", "ripeness_score": 0.89, "disease_score": 0.05, "reachable": True, "vision_confidence": 0.37}], {"worker_present": False, "robot_zone_clear": True}, ["pepper-harvest-001", "pepper-agent-001"], "camera 오염으로 confidence가 낮은 경우 harvest review보다 manual review가 우선이다.", "medium", [robot_task("manual_review", "cand-85", "candidate", "cand-85", "high", True, "camera 오염으로 confidence가 낮아 수동 검토가 우선이다."), robot_task("manual_review", "cand-86", "candidate", "cand-86", "medium", True, "같은 이유로 수동 검토가 필요하다.")], [], True, "visual_inspection", "camera 렌즈 상태와 두 후보의 실제 숙도 여부를 확인한다.", 0.75),
        make_robot_sample(44, "fruiting", "gh-01-zone-a", "작업자가 row-a 하부 정리를 하는 동안 inspect 후보가 생겼지만 즉시 접근할 수 없다.", [{"candidate_id": "hotspot-20", "disease_score": 0.7, "reachable": True}], {"worker_present": True, "robot_zone_clear": False}, ["pepper-agent-001", "pepper-pest-001"], "작업자 하부 정리가 끝나기 전에는 inspect robot task를 생성하면 안 된다.", "critical", [], [{"candidate_id": "hotspot-20", "reason": "작업자 하부 정리가 끝나기 전까지 robot zone이 clear하지 않다."}], False, "operator_confirm", "작업자 하부 정리 종료와 robot zone clear 상태를 확인한다.", 0.9),
    ]


def main() -> None:
    state_rows = build_safety_samples() + build_sensor_samples()
    robot_rows = build_robot_samples()
    write_jsonl(STATE_OUTPUT, state_rows)
    write_jsonl(ROBOT_OUTPUT, robot_rows)
    print(f"state_output,{STATE_OUTPUT.as_posix()},{len(state_rows)}")
    print(f"robot_output,{ROBOT_OUTPUT.as_posix()},{len(robot_rows)}")


if __name__ == "__main__":
    main()
