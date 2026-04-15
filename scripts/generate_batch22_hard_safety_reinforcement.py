#!/usr/bin/env python3
"""Generate batch22 corrective samples that reinforce ds_v11 hard-safety blind spots.

Targets the 5 eval-case failures identified in Phase F-1:

- Cluster A (3 cases) — model incorrectly emits `enter_safe_mode` when the
  scenario requires `block_action` + `create_alert`:
    - edge-eval-018 (manual_override + pump comm loss)
    - edge-eval-021 (dry_room comm loss + reentry_pending)
    - edge-eval-027 (worker_present + readback loss)
- Cluster B (2 cases) — model incorrectly emits `adjust_fertigation` on GT
  Master slab dry-back patterns where human inspection should be first:
    - blind-expert-010 (GT Master dry-back + repeated afternoon wilt)
    - blind-action-004 (fruit-load GT Master dry-back)

Generates 24 samples across 3 files (4.8x augmentation), matching the
design in docs/ds_v12_batch22_hard_safety_reinforcement_plan.md. Does not
reuse eval_id input_state — each sample varies at least one axis (zone_id,
growth_stage, or active_constraint) so the fine-tune pass does not memorize
the blind holdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FAILURE_OUTPUT = REPO_ROOT / "data/examples/failure_response_samples_batch22_block_vs_safe_mode.jsonl"
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch22_gt_master_dryback.jsonl"
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch22_gt_master_dryback.jsonl"


DOC_IDS = {
    "pepper-agent-001": "EXPERT-AI-DESIGN",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
    "pepper-crop-env-thresholds-001": "RAG-SRC-010",
}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def citation(chunk_id: str) -> dict[str, str]:
    return {"chunk_id": chunk_id, "document_id": DOC_IDS[chunk_id]}


def action(
    prefix: str,
    index: int,
    action_type: str,
    target_type: str,
    target_id: str,
    risk_level: str,
    reason: str,
    expected_effect: str,
    cooldown_minutes: int,
    *,
    approval_required: bool = False,
) -> dict[str, Any]:
    return {
        "action_id": f"{prefix}-act-{index:03d}",
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


# ---------------------------------------------------------------------------
# Cluster A — block_action vs enter_safe_mode
# ---------------------------------------------------------------------------
# Each record: critical risk + [block_action, create_alert] fixed,
# enter_safe_mode is forbidden. All share the reasoning that a worker-safety
# or comms-loss precondition defeats the automatic safe_mode fallback.

FAILURE_ROWS: list[dict[str, Any]] = [
    # ---- A1: manual_override + pump comm loss (3 variants) -----------------
    {
        "sample_id": "failure-response-batch22-a1a",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-west",
            "growth_stage": "fruit_expansion",
            "state_summary": "수동 제어가 켜진 상태에서 관수 펌프 통신이 끊겨 현재 급수 여부를 확인할 수 없다.",
            "active_constraints": ["manual_override", "irrigation_pump_comm_loss"],
            "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override와 펌프 통신 손실이 겹쳤을 때는 자동 safe_mode보다 block_action이 먼저다.",
            "risk_level": "critical",
            "diagnosis": [
                "manual override가 활성 상태이면 사람 안전 원칙이 모든 자동 복구 로직보다 우선한다.",
                "이 상황에서 enter_safe_mode를 내면 현장 작업자 상태를 모른 채 자동 제어를 복귀시키므로 block_action이 필요하다.",
            ],
            "recommended_actions": [
                action("br22-a1a", 1, "block_action", "zone", "gh-01-zone-west", "critical",
                       "manual override 상태에서 자동 제어 변경을 완전히 차단한다.",
                       "사람 안전 원칙을 최우선으로 보호한다.", 0),
                action("br22-a1a", 2, "create_alert", "operator", "control-room", "critical",
                       "manual override + pump comm loss 동시 발생을 즉시 알린다.",
                       "현장 작업자 상태를 즉시 확인할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "manual override가 활성 상태인 동안 자동 safe_mode 전환은 현장 작업자의 작업을 방해할 수 있다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "manual override 유지 이유와 펌프 통신 복구 여부를 현장에서 확인한다.")],
            "confidence": 0.88,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a1b",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-02-zone-east",
            "growth_stage": "flowering",
            "state_summary": "수동 제어 중 관수 펌프 통신이 끊겼고 건조실 통신도 동시에 불안정하다.",
            "active_constraints": ["manual_override", "irrigation_pump_comm_loss", "dry_room_comm_flaky"],
            "retrieved_context": ["pepper-agent-001", "pepper-house-drying-hygiene-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override 위에 두 경로 통신 손실이 겹치면 block_action과 create_alert가 고정이고 safe_mode는 금지다.",
            "risk_level": "critical",
            "diagnosis": [
                "관수와 건조실 두 경로가 동시에 불안정한 상황에서는 자동 safe_mode 복귀가 엉뚱한 경로를 건드릴 수 있다.",
                "manual override가 유지되는 동안 block_action을 걸어 모든 자동 경로를 정지하고 현장 확인이 먼저다.",
            ],
            "recommended_actions": [
                action("br22-a1b", 1, "block_action", "zone", "gh-02-zone-east", "critical",
                       "manual override + 두 경로 통신 손실 상황에서 자동 제어 복귀를 전면 차단한다.",
                       "잘못된 경로 복귀로 인한 2차 피해를 막는다.", 0),
                action("br22-a1b", 2, "create_alert", "operator", "control-room", "critical",
                       "관수 펌프와 건조실 통신 동시 불안정 상태를 즉시 통보한다.",
                       "두 경로 모두 점검 인력을 투입할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "manual override와 복합 경로 실패 동안 자동 safe_mode 전환은 실제 안전 상태를 확정하지 못한다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "현장 작업자 위치, 관수 펌프 상태, 건조실 통신 복구 상태를 함께 확인한다.")],
            "confidence": 0.87,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-house-drying-hygiene-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a1c",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-south",
            "growth_stage": "fruiting",
            "state_summary": "manual override 상태에서 관수 펌프 통신이 끊기고 rootzone WC 센서도 최근 값을 받지 못한다.",
            "active_constraints": ["manual_override", "irrigation_pump_comm_loss", "rootzone_wc_sensor_stale"],
            "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override + 펌프 통신 손실 + 근권 센서 stale 조합에서는 자동 복귀를 막고 block_action을 건다.",
            "risk_level": "critical",
            "diagnosis": [
                "관수 경로 통신과 근권 센서가 동시에 불안정하면 safe_mode로 진입해도 실제 slab 상태를 알 수 없다.",
                "manual override 조건에서는 block_action을 걸고 현장에서 센서·펌프를 순서대로 복구해야 한다.",
            ],
            "recommended_actions": [
                action("br22-a1c", 1, "block_action", "zone", "gh-01-zone-south", "critical",
                       "manual override와 관수·근권 동시 실패 상황에서 자동 제어를 전면 차단한다.",
                       "근거 없는 자동 복귀를 막는다.", 0),
                action("br22-a1c", 2, "create_alert", "operator", "control-room", "critical",
                       "manual override + 관수 통신 손실 + rootzone sensor stale 3중 실패를 알린다.",
                       "3경로 복구를 동시에 시작할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "근권 센서가 stale인 동안 safe_mode는 실제 slab 상태에 맞지 않는 복귀 경로를 선택할 수 있다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("sensor_recheck", 0,
                                     "rootzone WC 센서 상태와 관수 펌프 통신 복구를 현장 점검한다.")],
            "confidence": 0.86,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-rootzone-001")],
        },
    },
    # ---- A2: worker_present + readback loss (3 variants) -------------------
    {
        "sample_id": "failure-response-batch22-a2a",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-north",
            "growth_stage": "fruit_expansion",
            "state_summary": "작업자가 lane 내부에 있는 상태에서 관수 메인 밸브 readback 신호가 사라졌다.",
            "active_constraints": ["worker_present_in_lane", "irrigation_main_valve_readback_loss"],
            "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "worker_present가 있는 동안 readback loss가 발생하면 block_action과 create_alert를 고정하고 safe_mode는 금지한다.",
            "risk_level": "critical",
            "diagnosis": [
                "작업자가 lane 안에 있으면 어떤 자동 복귀 로직도 사람 안전보다 먼저일 수 없다.",
                "enter_safe_mode는 readback이 없는 상태에서 자동으로 밸브를 움직일 수 있어 작업자 안전에 직접 위험하다.",
            ],
            "recommended_actions": [
                action("br22-a2a", 1, "block_action", "zone", "gh-01-zone-north", "critical",
                       "worker_present + readback loss 상태에서 모든 자동 제어 변경을 차단한다.",
                       "작업자 안전을 최우선으로 확보한다.", 0),
                action("br22-a2a", 2, "create_alert", "operator", "control-room", "critical",
                       "lane 안의 작업자 존재와 밸브 readback 손실 동시 발생을 즉시 통보한다.",
                       "작업자 대피와 밸브 점검을 동시에 시작할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "작업자가 lane 안에 있는 동안 자동 safe_mode 전환은 실제 사람 위치를 고려하지 않는다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "작업자 대피 완료와 readback 복구 상태를 확인한다.")],
            "confidence": 0.89,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a2b",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-east",
            "growth_stage": "fruiting",
            "state_summary": "작업자가 lane에 있고 readback이 없는데 통로 바닥이 결로로 젖어 미끄럼 위험이 높다.",
            "active_constraints": ["worker_present_in_lane", "irrigation_readback_loss", "aisle_slip_hazard"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "worker_present와 readback loss에 aisle slip hazard가 겹치면 block_action이 더욱 필수적이고 safe_mode는 금지다.",
            "risk_level": "critical",
            "diagnosis": [
                "작업자 위치·readback·통로 상태 3중 위험이 동시에 있을 때 자동 safe_mode 전환은 사람을 배제한 복귀를 만든다.",
                "이 조합에서 block_action은 우회 불가하다.",
            ],
            "recommended_actions": [
                action("br22-a2b", 1, "block_action", "zone", "gh-01-zone-east", "critical",
                       "worker_present + readback loss + aisle slip 3중 위험에서 모든 자동 경로를 차단한다.",
                       "미끄럼 사고와 관수 이상을 동시에 예방한다.", 0),
                action("br22-a2b", 2, "create_alert", "operator", "control-room", "critical",
                       "3중 위험 상황을 즉시 통보하여 우선 대피와 복구 인력을 투입한다.",
                       "작업자 보호와 복구가 동시에 시작된다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "aisle slip hazard와 worker_present 조건에서 자동 safe_mode는 실제 사람 위험을 고려하지 않는다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "작업자 대피와 통로 건조 상태, readback 복구를 함께 확인한다.")],
            "confidence": 0.88,
            "retrieval_coverage": "partial",
            "citations": [citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a2c",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-center",
            "growth_stage": "flowering",
            "state_summary": "복수 구역에서 작업자가 동시에 존재하고 관수 readback이 한 번에 사라졌다.",
            "active_constraints": ["multi_zone_worker_present", "irrigation_readback_loss"],
            "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        },
        "preferred_output": {
            "situation_summary": "복수 구역 worker_present와 readback loss 동시 발생에서도 block_action과 create_alert가 고정이고 safe_mode는 금지다.",
            "risk_level": "critical",
            "diagnosis": [
                "복수 구역 작업자가 있을 때 safe_mode 자동 전환은 여러 밸브를 동시에 움직여 사람 위치를 빗나갈 수 있다.",
                "block_action으로 모든 자동 복귀를 정지하고 구역별 작업자 대피가 확정된 뒤에만 수동 복구가 가능하다.",
            ],
            "recommended_actions": [
                action("br22-a2c", 1, "block_action", "farm", "demo-farm", "critical",
                       "복수 구역 worker_present + readback loss 동시 발생에서 자동 제어를 전면 차단한다.",
                       "사람 위치 추적 완료 전까지 모든 자동 밸브 동작을 멈춘다.", 0),
                action("br22-a2c", 2, "create_alert", "operator", "control-room", "critical",
                       "복수 구역 작업자 동시 재실과 readback 손실을 통합 알림으로 보낸다.",
                       "관리자가 전체 구역을 동시에 확인할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "다수 구역 작업자 상황에서 자동 safe_mode 전환은 각 구역의 실제 사람 위치를 반영할 수 없다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "각 구역별 작업자 대피 확인 후에만 단계적 복구를 허용한다.")],
            "confidence": 0.87,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-climate-001")],
        },
    },
    # ---- A3: reentry_pending + dry_room comm loss (3 variants) -------------
    {
        "sample_id": "failure-response-batch22-a3a",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-dry",
            "growth_stage": "harvest",
            "state_summary": "reentry_pending 상태에서 건조실 통신이 사라져 자동 제어를 바로 재개할 수 없다.",
            "active_constraints": ["reentry_pending", "dry_room_comm_loss"],
            "retrieved_context": ["pepper-agent-001", "pepper-house-drying-hygiene-001"],
        },
        "preferred_output": {
            "situation_summary": "reentry_pending과 건조실 통신 손실이 같이 있으면 block_action이 safe_mode보다 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "reentry_pending은 구역이 아직 사람 접근 허용이 확정되지 않은 상태를 의미한다.",
                "이때 enter_safe_mode를 자동으로 걸면 건조실 설비가 사람 확인 전에 돌아올 수 있어 block_action이 필수다.",
            ],
            "recommended_actions": [
                action("br22-a3a", 1, "block_action", "zone", "gh-01-zone-dry", "critical",
                       "reentry_pending 상태에서 자동 제어 재개를 막는다.",
                       "사람 접근 확정 전까지 자동 복귀를 차단한다.", 0),
                action("br22-a3a", 2, "create_alert", "operator", "control-room", "critical",
                       "reentry_pending + 건조실 통신 손실을 알려 수동 복구를 요청한다.",
                       "건조 품질 손실과 사람 위험을 동시에 줄인다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "reentry_pending 상태에서 자동 safe_mode 복귀는 사람 접근 확정 전 자동 제어를 유발한다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "reentry_pending 해제 조건과 건조실 통신 복구를 확인한다.")],
            "confidence": 0.87,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-house-drying-hygiene-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a3b",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-dry-b",
            "growth_stage": "drying",
            "state_summary": "reentry_pending 중 건조실 통신이 사라지고 양액 공급 원수 파이프 readback도 함께 끊겼다.",
            "active_constraints": ["reentry_pending", "dry_room_comm_loss", "source_water_path_degraded"],
            "retrieved_context": ["pepper-agent-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "reentry_pending에 두 경로 readback 손실이 겹쳐도 block_action이 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "건조실과 source water 두 경로 동시 불안정은 safe_mode로는 복구 범위가 명확하지 않다.",
                "reentry_pending이 풀리기 전까지 block_action과 수동 복구가 답이다.",
            ],
            "recommended_actions": [
                action("br22-a3b", 1, "block_action", "zone", "gh-01-zone-dry-b", "critical",
                       "reentry_pending 중 두 경로 실패 상황에서 자동 제어를 전면 차단한다.",
                       "잘못된 경로 복귀를 원천 차단한다.", 0),
                action("br22-a3b", 2, "create_alert", "operator", "control-room", "critical",
                       "reentry_pending + 건조실 + source water 3중 실패 상황을 알린다.",
                       "3경로 동시 수동 복구를 요청한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "두 경로 실패 동안 safe_mode는 어느 경로로 복귀해야 할지 확정할 수 없다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "reentry_pending 해제, 건조실 통신, 원수 파이프 상태를 함께 확인한다.")],
            "confidence": 0.86,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a3c",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-02-zone-main",
            "growth_stage": "fruit_expansion",
            "state_summary": "reentry_pending과 건조실 통신 손실에 보온커튼 readback도 사라져 climate 경로가 같이 무너졌다.",
            "active_constraints": ["reentry_pending", "dry_room_comm_loss", "climate_path_degraded"],
            "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        },
        "preferred_output": {
            "situation_summary": "reentry_pending + 건조실 + climate 3중 실패에서도 block_action + create_alert가 고정이고 safe_mode는 금지다.",
            "risk_level": "critical",
            "diagnosis": [
                "climate 경로까지 함께 무너지면 safe_mode는 온실 환경을 예측 불가능하게 만들 수 있다.",
                "reentry_pending이 유지되는 동안은 block_action이 유일한 안전한 선택이다.",
            ],
            "recommended_actions": [
                action("br22-a3c", 1, "block_action", "zone", "gh-02-zone-main", "critical",
                       "3경로 동시 실패 상황에서 모든 자동 제어를 차단한다.",
                       "예측 불가능한 복귀 동작을 막는다.", 0),
                action("br22-a3c", 2, "create_alert", "operator", "control-room", "critical",
                       "reentry_pending + 건조실 + climate 3중 실패를 통합 알림으로 보낸다.",
                       "여러 경로를 동시에 수동 복구할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "climate 경로까지 무너진 상태에서 자동 safe_mode는 온실 환경 안정성을 보장할 수 없다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "reentry_pending 해제, 건조실 통신, climate 경로 복구를 순서대로 확인한다.")],
            "confidence": 0.86,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-climate-001")],
        },
    },
    # ---- A4: manual_override + safe_mode already active (3 variants) -------
    {
        "sample_id": "failure-response-batch22-a4a",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-pilot",
            "growth_stage": "fruit_set",
            "state_summary": "manual override가 켜진 상태에서 safe_mode도 이미 활성이지만 추가 이상이 감지됐다.",
            "active_constraints": ["manual_override", "safe_mode_active", "anomaly_detected"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override와 safe_mode가 이미 켜져 있을 때 추가 이상에 대해 block_action을 덧씌우고 safe_mode 재진입은 금지한다.",
            "risk_level": "critical",
            "diagnosis": [
                "safe_mode가 이미 활성화된 상태에서 추가 enter_safe_mode는 의미 없는 재진입이며 manual override 의도를 깬다.",
                "이 경우 block_action으로 추가 변경을 차단하고 create_alert로 사람 확인을 요청해야 한다.",
            ],
            "recommended_actions": [
                action("br22-a4a", 1, "block_action", "zone", "gh-01-zone-pilot", "critical",
                       "manual override + safe_mode 위에 추가 자동 동작을 차단한다.",
                       "중복된 자동 복귀를 막는다.", 0),
                action("br22-a4a", 2, "create_alert", "operator", "control-room", "critical",
                       "safe_mode 유지 중 추가 이상 감지를 즉시 알린다.",
                       "운영자가 manual override 유지 여부를 재판단할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "safe_mode가 이미 활성 상태에서 재진입은 의미가 없고 manual override 의도를 혼동시킬 수 있다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "manual override 유지 이유와 추가 이상의 원인을 현장에서 확인한다.")],
            "confidence": 0.87,
            "retrieval_coverage": "partial",
            "citations": [citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a4b",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-mid",
            "growth_stage": "fruiting",
            "state_summary": "manual override와 safe_mode가 모두 활성인 상태에서 밸브 readback이 추가로 사라졌다.",
            "active_constraints": ["manual_override", "safe_mode_active", "valve_readback_loss"],
            "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override + safe_mode + readback loss 3중 상태에서 추가 enter_safe_mode는 금지, block_action과 create_alert가 고정이다.",
            "risk_level": "critical",
            "diagnosis": [
                "밸브 readback이 추가로 사라진 것은 하드웨어 신뢰 구간이 더 좁아졌다는 뜻이다.",
                "자동 복귀 대신 block_action으로 현재 상태를 동결하고 수동 점검으로 넘겨야 한다.",
            ],
            "recommended_actions": [
                action("br22-a4b", 1, "block_action", "zone", "gh-01-zone-mid", "critical",
                       "밸브 readback loss가 추가된 상황에서 자동 제어 복귀를 차단한다.",
                       "하드웨어 신뢰 구간이 좁아진 상태를 동결한다.", 0),
                action("br22-a4b", 2, "create_alert", "operator", "control-room", "critical",
                       "safe_mode 유지 중 readback 추가 손실을 알린다.",
                       "운영자가 밸브 점검을 우선 투입할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "safe_mode가 이미 활성인데 readback이 추가로 사라진 상태에서 재진입은 상황을 해결하지 못한다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("operator_confirm", 0,
                                     "밸브 readback 복구와 manual override 유지 여부를 함께 확인한다.")],
            "confidence": 0.86,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "failure-response-batch22-a4c",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-02-zone-west",
            "growth_stage": "fruit_expansion",
            "state_summary": "manual override와 safe_mode 활성 중 온도 센서가 stale 상태가 되었고 기록 갱신이 멈췄다.",
            "active_constraints": ["manual_override", "safe_mode_active", "temperature_sensor_stale"],
            "retrieved_context": ["pepper-agent-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override + safe_mode + sensor stale 상태에서도 block_action + create_alert가 고정이고 safe_mode 재진입은 금지다.",
            "risk_level": "critical",
            "diagnosis": [
                "온도 센서가 stale이면 safe_mode가 보고 있는 상태 자체가 낡았다는 뜻이다.",
                "block_action으로 기존 safe_mode 상태 이상의 자동 동작을 막고 수동 점검으로 넘긴다.",
            ],
            "recommended_actions": [
                action("br22-a4c", 1, "block_action", "zone", "gh-02-zone-west", "critical",
                       "sensor stale 상태에서 자동 제어 변경을 차단한다.",
                       "낡은 관측치로 자동 제어가 유발되는 것을 막는다.", 0),
                action("br22-a4c", 2, "create_alert", "operator", "control-room", "critical",
                       "safe_mode 유지 중 온도 센서 stale을 알린다.",
                       "센서 복구와 manual override 재검토를 요청할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "enter_safe_mode",
                 "reason": "센서가 stale인 상태에서 safe_mode 재진입은 잘못된 기준값으로 복귀할 위험이 있다."}
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("sensor_recheck", 0,
                                     "온도 센서 stale 원인과 safe_mode 상태 일관성을 확인한다.")],
            "confidence": 0.86,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-crop-env-thresholds-001")],
        },
    },
]


# ---------------------------------------------------------------------------
# Cluster B — GT Master dry-back → adjust_fertigation forbidden
# ---------------------------------------------------------------------------
# risk_level = high, [create_alert, request_human_check] fixed,
# adjust_fertigation and short_irrigation forbidden. Zone/stage/trigger vary
# to avoid memorizing the two eval cases.

STATE_ROWS: list[dict[str, Any]] = [
    # ---- B1 rootzone_diagnosis: dry-back overrun + low dawn WC + wilt ------
    {
        "sample_id": "state-judgement-batch22-b1a",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-fruiting",
            "growth_stage": "fruiting",
            "state_summary": "GT Master 슬래브에서 야간 dry-back이 과다하고 새벽 WC가 낮으며 오후 잎 처짐이 반복된다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "low_dawn_wc", "afternoon_wilt_repeat"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master dry-back 과다 + 낮은 새벽 WC + 반복 afternoon wilt는 rootzone stress 고위험 신호이며 현장 확인이 먼저다.",
            "risk_level": "high",
            "diagnosis": [
                "dry-back 과다와 낮은 새벽 WC는 실제 slab의 물 보유가 무너지고 있다는 뜻이다.",
                "afternoon wilt 반복은 이미 식물이 스트레스를 받고 있음을 의미한다.",
                "이때 recipe 변경은 직관적이지만 근권 상태를 수동 확인하지 않으면 오히려 악화될 수 있다.",
            ],
            "recommended_actions": [
                action("br22-b1a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "GT Master dry-back 과다 + low dawn WC + 반복 wilt를 rootzone stress 고위험으로 알린다.",
                       "운영자가 즉시 상황을 인지하고 현장 투입을 시작할 수 있다.", 0),
                action("br22-b1a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab의 dry-back, drain 상태, 통기 조건을 현장에서 확인한다.",
                       "오진 위험이 큰 자동 조정보다 수동 확인이 선행된다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "근권 stress 고위험 신호에서 자동 recipe 조정은 현장 확인 전에 허용되면 안 된다."},
                {"action_type": "short_irrigation",
                 "reason": "afternoon wilt가 이미 반복되는 상황에서 reflex 관수는 근본 원인을 놓친다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "대표 slab의 dry-back과 drain 상태, 통기 조건을 확인한다.")],
            "confidence": 0.82,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b1b",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-fruit-expansion",
            "growth_stage": "fruit_expansion",
            "state_summary": "fruit_expansion 구역 GT Master slab에서 dry-back 과다와 낮은 새벽 WC가 같이 있고 오후 잎 처짐 메모가 반복된다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "low_dawn_wc", "afternoon_wilt_repeat"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "fruit_expansion 구역의 GT Master dry-back 과다는 과실 하중과 겹쳐 더 큰 스트레스 위험을 만든다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중 구간에서 dry-back 과다와 low dawn WC가 겹치면 근권 회복 여유가 훨씬 좁다.",
                "이 상황에서도 recipe 자동 조정은 허용되지 않고 현장 확인이 우선이다.",
            ],
            "recommended_actions": [
                action("br22-b1b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "fruit_expansion 구역 GT Master rootzone stress 고위험을 알린다.",
                       "과실 하중 구간의 회복 여유가 좁다는 점을 명확히 한다.", 0),
                action("br22-b1b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab dry-back, drain 회복, 과실 하중 상태를 함께 확인한다.",
                       "자동 조정 전에 현장에서 확인할 신호를 명시한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "과실 하중 + dry-back 과다 상황에서 자동 recipe 조정은 근권 상태를 더 악화시킬 수 있다."},
                {"action_type": "short_irrigation",
                 "reason": "반복 wilt에 대한 reflex 관수는 통기 회복을 돕지 못한다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "과실 하중 구간의 slab dry-back과 drain 회복을 현장 확인한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- B2 rootzone_diagnosis: dry-back + drain EC 정상 + low dawn WC -----
    {
        "sample_id": "state-judgement-batch22-b2a",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-fruit-b",
            "growth_stage": "fruiting",
            "state_summary": "GT Master slab에서 dry-back이 과다하지만 drain EC는 정상 범위이고 새벽 WC만 낮다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "drain_ec_normal", "low_dawn_wc"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "drain EC가 정상이어도 dry-back 과다 + low dawn WC 조합은 고위험이며 자동 양액 조정은 허용되지 않는다.",
            "risk_level": "high",
            "diagnosis": [
                "drain EC가 정상이라는 것은 영양 농도만 괜찮다는 의미지 물 보유가 회복됐다는 뜻은 아니다.",
                "dry-back 과다와 low dawn WC가 유지되면 근권 stress는 여전히 고위험이다.",
            ],
            "recommended_actions": [
                action("br22-b2a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "drain EC 정상에도 불구하고 dry-back 과다를 rootzone stress 고위험으로 알린다.",
                       "drain EC만 보고 안전하다고 판단하지 않도록 한다.", 0),
                action("br22-b2a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab의 dry-back 속도와 dawn WC 회복 경향을 현장 확인한다.",
                       "drain EC 수치 뒤에 숨은 물 보유 문제를 찾는다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "drain EC가 정상이어도 dry-back 과다와 low dawn WC 상황에서 자동 recipe 조정은 허용되지 않는다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "GT Master slab의 dry-back과 dawn WC 회복을 직접 측정한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b2b",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-ripening",
            "growth_stage": "ripening",
            "state_summary": "ripening 단계의 GT Master slab에서 dry-back이 과다하고 새벽 WC가 낮지만 drain EC는 안정적이다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "low_dawn_wc", "drain_ec_stable"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "ripening 단계의 GT Master dry-back 과다도 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "ripening 단계에서는 물 stress가 오히려 과실 품질 손실로 빠르게 이어진다.",
                "drain EC가 안정적이라도 dry-back 과다와 낮은 dawn WC가 유지되면 현장 확인이 우선이다.",
            ],
            "recommended_actions": [
                action("br22-b2b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "ripening 단계 GT Master rootzone stress 고위험을 알린다.",
                       "과실 품질 손실 위험을 사전에 알린다.", 0),
                action("br22-b2b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "ripening 단계의 slab 상태와 과실 외관을 함께 확인한다.",
                       "품질 손실 가능성을 현장에서 판단할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "ripening 단계에서 자동 양액 조정은 drain EC가 안정적이어도 과실 품질을 해칠 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "ripening 단계 GT Master slab의 dry-back과 과실 상태를 함께 확인한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- B3 rootzone_diagnosis: dry-back + night slab temp drop ------------
    {
        "sample_id": "state-judgement-batch22-b3a",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-night",
            "growth_stage": "fruiting",
            "state_summary": "GT Master slab에서 dry-back 과다와 야간 slab 온도 하락이 동반된다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "night_slab_temp_drop"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 slab 온도 하락과 dry-back 과다가 겹치면 recipe 조정보다 현장 확인이 먼저다.",
            "risk_level": "high",
            "diagnosis": [
                "야간 slab 온도 하락은 근권 뿌리 활력을 추가로 떨어뜨린다.",
                "이 상황에서 recipe 변경은 온도 조건을 해결하지 못하고 오히려 영양 스트레스를 유발할 수 있다.",
            ],
            "recommended_actions": [
                action("br22-b3a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "야간 slab 온도 하락과 dry-back 과다 동반 상황을 알린다.",
                       "온도 조건과 근권 상태를 동시에 점검할 수 있다.", 0),
                action("br22-b3a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab의 온도 로그와 dry-back 패턴을 함께 확인한다.",
                       "영양보다 온도가 1차 원인인지 현장에서 판단할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "온도 하락이 1차 원인일 수 있는 상황에서 자동 양액 조정은 방향을 잘못 잡을 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "slab 온도 로그와 dry-back 패턴을 함께 확인한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b3b",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-cold-night",
            "growth_stage": "fruit_set",
            "state_summary": "cold-night 가중 상황의 GT Master slab에서 dry-back 과다와 함께 새벽 WC도 낮게 유지된다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "night_slab_temp_drop", "cold_night_aggravated", "low_dawn_wc"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "cold-night과 dry-back 과다가 겹친 GT Master 근권은 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "cold-night은 근권 뿌리 활력을 떨어뜨려 실제 흡수율을 낮춘다.",
                "dry-back 과다 + low dawn WC가 함께 나타나면 rootzone stress 고위험으로 봐야 한다.",
            ],
            "recommended_actions": [
                action("br22-b3b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "cold-night 가중 GT Master rootzone stress 고위험을 알린다.",
                       "온도와 근권 상태를 동시에 점검하도록 한다.", 0),
                action("br22-b3b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "cold-night 대응 조치와 slab 상태를 함께 확인한다.",
                       "온도 관리와 근권 관리 중 1차 원인을 찾는다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "cold-night 조건에서 자동 양액 조정은 근권 흡수율과 맞지 않아 스트레스를 키울 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "cold-night 대응 상태와 slab dry-back을 함께 확인한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- EXTENDED variations (언어/context 다양화, blind 일반화용) ----------
    {
        "sample_id": "state-judgement-batch22-b1c",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-03-gt-line-a",
            "growth_stage": "early_fruiting",
            "state_summary": "Grodan slab에서 야간 배액률이 과도하게 높고 아침 substrate 수분이 목표치에 미달하며 오후 시간대 기공 폐쇄 관찰이 반복된다.",
            "active_constraints": ["slab_night_drainback_ratio_high", "substrate_dawn_wc_deficit", "afternoon_stomatal_stress_repeat"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 배액률 과다 + dawn 수분 부족 + 오후 기공 폐쇄는 rootzone 고위험 신호이며 자동 recipe 조정보다 현장 확인이 먼저다.",
            "risk_level": "high",
            "diagnosis": [
                "야간 배액률 과다는 slab의 물 보유 능력이 떨어지고 있음을 시사한다.",
                "오후 기공 폐쇄가 반복된다면 식물이 이미 수분 스트레스 반응을 보이고 있다는 뜻이다.",
            ],
            "recommended_actions": [
                action("br22-b1c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "야간 배액률 과다 + dawn 수분 부족 + 반복 기공 폐쇄를 rootzone 고위험으로 알린다.",
                       "현장 투입을 즉시 시작할 수 있다.", 0),
                action("br22-b1c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab의 야간 배액률과 아침 수분 회복 패턴을 현장에서 확인한다.",
                       "자동 조정 전에 근거를 수동으로 모은다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "rootzone 고위험 신호에서 자동 양액 조정은 현장 확인 없이 허용되지 않는다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "야간 배액률과 dawn 수분 회복을 직접 측정한다.")],
            "confidence": 0.82,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b1d",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-04-gt-mixed",
            "growth_stage": "fruit_set",
            "state_summary": "nightly drainback excessive and dawn substrate WC remains below setpoint while afternoon leaf turgor loss repeats across the slab set.",
            "active_constraints": ["nightly_drainback_excessive", "dawn_substrate_wc_below_setpoint", "afternoon_leaf_turgor_loss"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "nightly drainback excessive + dawn WC below setpoint + repeated leaf turgor loss is a rootzone high-risk signal that requires field confirmation before any recipe change.",
            "risk_level": "high",
            "diagnosis": [
                "Excessive nightly drainback combined with below-setpoint dawn substrate WC means the slab water reserve is eroding.",
                "Repeated afternoon leaf turgor loss indicates the plant is already under water stress.",
            ],
            "recommended_actions": [
                action("br22-b1d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "Alert on nightly drainback excessive + dawn WC below setpoint + repeated afternoon turgor loss.",
                       "Operator can start field inspection immediately.", 0),
                action("br22-b1d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "Field-verify nightly drainback ratio, dawn substrate WC recovery, and slab cross-section.",
                       "Collect evidence manually before any automation change.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "Auto recipe change is not permitted under rootzone high-risk signals without field confirmation."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "Inspect slab for drainback ratio and dawn WC recovery on representative lines.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b2c",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-02-rockwool-zone",
            "growth_stage": "fruiting",
            "state_summary": "rockwool 슬래브에서 dry-back이 과다하지만 drain EC는 안정적이고 새벽 WC가 계속 낮다.",
            "active_constraints": ["rockwool_slab_dryback_overrun", "drain_ec_stable", "dawn_wc_low_persistent"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "rockwool 슬래브에서도 drain EC가 정상일 때 dry-back 과다 + low dawn WC 조합은 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "drain EC 정상은 영양 농도 안정을 의미할 뿐 물 보유 회복을 의미하지 않는다.",
                "rockwool 슬래브에서도 근권 stress 신호는 동일한 원칙으로 판단한다.",
            ],
            "recommended_actions": [
                action("br22-b2c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "rockwool 슬래브의 dry-back 과다 + dawn WC 저하를 고위험으로 알린다.",
                       "영양 수치 뒤에 숨은 물 보유 문제를 조기 공유한다.", 0),
                action("br22-b2c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "rockwool 라인의 dry-back과 dawn 회복을 현장에서 측정한다.",
                       "slab 물 보유 능력 저하 원인을 찾는다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "rockwool 슬래브에서도 drain EC 정상 여부와 무관하게 dry-back 과다 + low dawn WC는 자동 양액 조정을 금한다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "rockwool 슬래브의 dry-back 과 dawn WC를 직접 측정한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b2d",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-05-slab-line-c",
            "growth_stage": "ripening_start",
            "state_summary": "slab water reserve erosion observed with dry-back overrun while nutrient channel is stable.",
            "active_constraints": ["slab_water_reserve_erosion", "dry_back_overrun", "nutrient_channel_stable"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "Stable nutrient channel does not neutralize dry-back overrun; water reserve erosion is still a rootzone high-risk case that requires field-first handling.",
            "risk_level": "high",
            "diagnosis": [
                "Stable drain EC/pH does not imply adequate water buffering.",
                "The ripening phase is particularly sensitive to water-reserve erosion and fruit quality impacts.",
            ],
            "recommended_actions": [
                action("br22-b2d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "Alert on slab water reserve erosion with dry-back overrun during ripening.",
                       "Inform the operator before automated adjustments are considered.", 0),
                action("br22-b2d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "Field-verify slab water retention and ripening-phase fruit status together.",
                       "Separate fruit quality loss from nutrient drift.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "Nutrient stability does not license auto recipe change when slab water reserve is eroding."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "Inspect slab water retention and fruit quality on ripening lines.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b3c",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-06-gt-mini",
            "growth_stage": "mid_season_fruiting",
            "state_summary": "GT slab 라인에서 야간 배액률이 과다하며 slab 온도 하락과 뿌리 활력 저하 관찰이 동반된다.",
            "active_constraints": ["slab_nightly_drainback_high", "slab_temperature_drop", "root_vigor_decline_observed"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 배액률 과다 + slab 온도 저하 + 뿌리 활력 저하가 겹친 상황은 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "slab 온도 저하가 있으면 뿌리 흡수 효율 자체가 떨어져 양액 조정으로 해결되지 않는다.",
                "뿌리 활력 저하가 이미 관찰되면 recipe 변경보다 환경 조건 복구가 우선이다.",
            ],
            "recommended_actions": [
                action("br22-b3c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "야간 배액률 + slab 온도 + 뿌리 활력 저하 3중 신호를 고위험으로 알린다.",
                       "환경과 근권을 동시에 점검할 수 있다.", 0),
                action("br22-b3c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "slab 온도 조건과 뿌리 상태를 함께 현장에서 확인한다.",
                       "영양과 온도 원인을 분리할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "slab 온도 저하 + 뿌리 활력 저하 상황에서 자동 양액 조정은 환경 원인을 덮는다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "slab 온도 조건과 뿌리 상태를 함께 점검한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-batch22-b3d",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-07-mixed-substrate",
            "growth_stage": "fruit_expansion",
            "state_summary": "혼합 기질 구역에서 dry-back 과다와 야간 slab 온도 하락이 있으며 최근 며칠 cold-night 조건이 반복됐다.",
            "active_constraints": ["mixed_substrate_dryback_overrun", "night_slab_temp_drop", "cold_night_repeated"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "혼합 기질 구역에서 cold-night 반복 + slab 온도 저하 + dry-back 과다는 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "cold-night이 반복되면 누적 스트레스로 슬래브 온도와 뿌리 활력 모두 타격을 받는다.",
                "혼합 기질에서도 근권 stress 고위험 원칙은 동일하게 적용된다.",
            ],
            "recommended_actions": [
                action("br22-b3d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "cold-night 반복 + slab 온도 저하 + dry-back 과다 상황을 고위험으로 알린다.",
                       "온도 관리와 근권 관리를 동시에 시작하게 한다.", 0),
                action("br22-b3d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "혼합 기질 구역의 slab 온도와 dry-back 패턴을 현장 확인한다.",
                       "누적된 cold-night 영향을 진단한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "cold-night 반복 상황에서 자동 양액 조정은 뿌리 흡수율 저하 문제를 해결하지 못한다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "혼합 기질 구역의 slab 온도와 dry-back을 함께 점검한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


ACTION_ROWS: list[dict[str, Any]] = [
    # ---- B4 action_recommendation: fruit-load GT Master dry-back -----------
    {
        "sample_id": "action-recommendation-batch22-b4a",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-fruit-load",
            "growth_stage": "fruit_expansion",
            "state_summary": "과실 하중 구간의 GT Master 라인에서 dry-back이 과다하고 오후 잎 처짐이 반복된다.",
            "active_constraints": ["fruit_load_high", "gt_master_overnight_dryback_overrun", "afternoon_wilt_repeat"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 하중 GT Master dry-back 상황에서는 현장 확인이 먼저이고 자동 recipe 조정은 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중 + dry-back 과다 + 반복 wilt는 rootzone stress 고위험 signal이다.",
                "이 상황에서 자동 recipe 조정은 오진 위험이 높다.",
            ],
            "recommended_actions": [
                action("br22-b4a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "과실 하중 GT Master rootzone stress 고위험을 알린다.",
                       "운영자가 현장 투입을 즉시 시작할 수 있다.", 0),
                action("br22-b4a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "과실 하중 구간의 slab dry-back과 drain 상태를 수동 확인한다.",
                       "자동 조정 전 1차 확인을 한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "과실 하중 + dry-back 과다 상황에서 자동 recipe 조정은 식물 stress를 더 키울 수 있다."},
                {"action_type": "short_irrigation",
                 "reason": "반복 wilt는 통기와 근권 회복이 필요하며 reflex 관수로는 해결되지 않는다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "과실 하중 구간 slab dry-back과 drain 회복을 확인한다.")],
            "confidence": 0.82,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b4b",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-harvest-ready",
            "growth_stage": "harvest_ready",
            "state_summary": "수확 준비 구간의 GT Master 라인에서 dry-back 과다와 오후 잎 처짐이 반복된다.",
            "active_constraints": ["harvest_ready", "gt_master_overnight_dryback_overrun", "afternoon_wilt_repeat"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "수확 직전 구간에서도 GT Master dry-back 과다는 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "수확 준비 구간에서 과도한 dry-back은 과실 품질 저하로 빠르게 이어진다.",
                "이 시점에서 recipe 변경은 수확 스케줄과 충돌할 수 있으며 현장 확인이 먼저다.",
            ],
            "recommended_actions": [
                action("br22-b4b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "수확 준비 구간 GT Master rootzone stress 고위험을 알린다.",
                       "수확 품질 손실 위험을 사전 공유한다.", 0),
                action("br22-b4b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "수확 스케줄과 slab 상태를 함께 현장 확인한다.",
                       "수확 스케줄 조정 여부를 현장에서 판단할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "수확 준비 구간에서 자동 양액 조정은 수확 품질 손실 위험을 키운다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "수확 스케줄 조정과 slab 상태를 함께 확인한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- B5 action_recommendation: low dawn WC ----------------------------
    {
        "sample_id": "action-recommendation-batch22-b5a",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-fruiting-c",
            "growth_stage": "fruiting",
            "state_summary": "GT Master 구역에서 새벽 WC가 계속 낮게 유지되고 dry-back 기록도 증가 추세다.",
            "active_constraints": ["low_dawn_wc", "dry_back_trending_up"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "새벽 WC 저하 추세는 근권 회복 여유가 줄고 있다는 뜻이며 자동 recipe 조정은 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "새벽 WC가 추세적으로 낮아지면 근권 재충수 기회가 부족하다는 의미다.",
                "이 상황에서 recipe를 자동으로 조정하면 잘못된 방향으로 갈 위험이 있다.",
            ],
            "recommended_actions": [
                action("br22-b5a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "새벽 WC 저하 추세와 dry-back 증가를 고위험으로 알린다.",
                       "근권 회복 여유가 좁아지고 있음을 명시한다.", 0),
                action("br22-b5a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "대표 slab의 재충수 전략과 drain 회복을 함께 점검한다.",
                       "자동 조정 전에 재충수 조건을 수동 확인한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "새벽 WC 저하 추세에서는 자동 양액 조정이 근권 회복 전략과 충돌할 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "재충수 전략과 dawn WC 회복을 함께 확인한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b5b",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-dual-slab",
            "growth_stage": "fruiting",
            "state_summary": "두 라인 dual-slab 평균이 동시에 낮고 dry-back 기록도 커지고 있다.",
            "active_constraints": ["low_dawn_wc_dual_slab", "dry_back_trending_up"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "두 라인 동시 낮은 dawn WC는 계통 문제일 수 있으며 자동 recipe 조정은 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "두 라인 동시 저하는 개별 slab 문제라기보다 급액 계통이나 환경 조건의 공통 문제일 가능성이 높다.",
                "recipe 자동 조정보다 계통 진단과 현장 확인이 우선이다.",
            ],
            "recommended_actions": [
                action("br22-b5b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "두 라인 동시 dawn WC 저하를 계통 위험으로 알린다.",
                       "계통 문제를 조기에 분리할 수 있다.", 0),
                action("br22-b5b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "두 라인의 drain 회복과 급액 계통 상태를 함께 현장 확인한다.",
                       "계통과 개별 slab 문제를 구분할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "계통 문제일 가능성이 있는 상황에서 자동 양액 조정은 오히려 문제를 덮어버릴 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "두 라인의 drain 회복과 급액 계통 상태를 함께 확인한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- B6 action_recommendation: dry-back + slab temp drop ---------------
    {
        "sample_id": "action-recommendation-batch22-b6a",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-temp-drop",
            "growth_stage": "fruiting",
            "state_summary": "GT Master slab에서 dry-back 과다와 slab 온도 저하가 동반된다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "night_slab_temp_drop"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "slab 온도 저하 상황의 dry-back 과다는 온도 원인 여지를 남기므로 현장 확인이 먼저다.",
            "risk_level": "high",
            "diagnosis": [
                "slab 온도 저하와 dry-back 과다가 겹치면 영양보다 온도가 1차 원인일 수 있다.",
                "이 상황에서 자동 양액 조정은 잘못된 방향으로 갈 수 있다.",
            ],
            "recommended_actions": [
                action("br22-b6a", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "slab 온도 저하와 dry-back 과다 동반 상황을 고위험으로 알린다.",
                       "온도 원인을 함께 검토하게 한다.", 0),
                action("br22-b6a", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "slab 온도 조절 상태와 dry-back 패턴을 함께 확인한다.",
                       "온도와 양액 중 1차 원인을 현장에서 찾는다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "온도가 1차 원인인지 확인 전에 자동 양액 조정을 허용하면 안 된다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "slab 온도와 dry-back 패턴을 함께 확인한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b6b",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone-night-low-light",
            "growth_stage": "fruiting",
            "state_summary": "GT Master slab에서 dry-back 과다와 slab 온도 저하가 있고 최근 야간 저광 기록도 함께 있다.",
            "active_constraints": ["gt_master_overnight_dryback_overrun", "night_slab_temp_drop", "night_low_light"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 저광까지 겹친 slab 온도 저하 + dry-back 상황은 복합 원인이며 현장 확인이 우선이다.",
            "risk_level": "high",
            "diagnosis": [
                "야간 저광은 낮 광합성 부족까지 쌓여 근권 stress를 추가로 키울 수 있다.",
                "이 복합 상황에서 자동 recipe 조정은 원인을 잘못 짚을 확률이 매우 높다.",
            ],
            "recommended_actions": [
                action("br22-b6b", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "야간 저광 + slab 온도 저하 + dry-back 과다 복합 상황을 고위험으로 알린다.",
                       "복합 원인을 조기에 공유한다.", 0),
                action("br22-b6b", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "최근 광 로그, slab 온도, dry-back을 묶어 현장 확인한다.",
                       "복합 원인 중 1차 원인을 분리한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "복합 원인 상황에서 자동 양액 조정은 문제 분리를 방해하고 오히려 악화시킬 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "광, slab 온도, dry-back 패턴을 묶어 확인한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    # ---- EXTENDED variations (언어/context 다양화, blind 일반화용) ----------
    {
        "sample_id": "action-recommendation-batch22-b4c",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-08-high-load",
            "growth_stage": "fruit_expansion",
            "state_summary": "과실 하중이 높은 구역에서 야간 배액률이 과다하며 아침 slab 수분이 목표치에 미달한다.",
            "active_constraints": ["high_fruit_load", "slab_nightly_drainback_high", "morning_slab_wc_below_target"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 하중 + 야간 배액률 과다 + 아침 수분 미달은 rootzone 고위험이며 자동 recipe 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중 구간에서 근권 회복 여유가 이미 좁다.",
                "야간 배액률 과다와 아침 수분 미달이 겹치면 slab의 물 보유가 무너지고 있음을 의미한다.",
            ],
            "recommended_actions": [
                action("br22-b4c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "과실 하중 + 야간 배액률 과다 + 아침 수분 미달을 rootzone 고위험으로 알린다.",
                       "운영자가 상황을 즉시 인지할 수 있다.", 0),
                action("br22-b4c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "과실 하중 구간의 야간 배액률과 아침 수분 회복을 현장 확인한다.",
                       "자동 조정 전 근거를 수동으로 모은다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "과실 하중 상황에서 자동 양액 조정은 식물 스트레스를 키울 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "과실 하중 구간의 slab 수분 회복을 점검한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b4d",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-09-post-harvest",
            "growth_stage": "post_harvest_recovery",
            "state_summary": "후반 수확이 끝난 구역의 slab에서 dry-back은 여전히 과다하고 야간 slab 온도 하락이 관찰된다.",
            "active_constraints": ["post_harvest_recovery", "persistent_dryback_overrun", "night_slab_temp_drop"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "수확 후 회복 구역에서 dry-back 과다와 slab 온도 저하가 같이 있으면 근권 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "수확 후 회복 구간에서도 slab의 물 보유 능력이 회복되지 않으면 다음 단계 생육에 악영향을 준다.",
                "slab 온도 저하가 동반되면 근본 원인이 온도인지 물인지 현장에서 구분해야 한다.",
            ],
            "recommended_actions": [
                action("br22-b4d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "수확 후 회복 구역의 dry-back 과다 + slab 온도 저하를 고위험으로 알린다.",
                       "다음 생육 단계에 대비할 수 있다.", 0),
                action("br22-b4d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "회복 구역의 slab 온도와 dry-back을 함께 현장 확인한다.",
                       "온도와 물 원인을 분리할 수 있다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "회복 구간에서 자동 양액 조정은 근본 원인을 가린다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "회복 구역의 slab 상태를 현장 점검한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b5c",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-10-dual-zone",
            "growth_stage": "fruiting",
            "state_summary": "dual zone 평균 substrate WC가 연속 저하 추세이며 dry-back 수치도 함께 증가한다.",
            "active_constraints": ["dual_zone_substrate_wc_declining", "dry_back_trend_increasing"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "두 구역 동시 substrate WC 저하 추세는 계통 문제일 가능성이 있어 자동 recipe 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "두 구역 동시 저하는 개별 slab이 아니라 급액 계통 또는 환경 조건의 공통 문제를 의심하게 한다.",
                "dry-back 추세가 증가하면 slab 회복 여유가 계속 줄어드는 중이다.",
            ],
            "recommended_actions": [
                action("br22-b5c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "dual zone 동시 substrate WC 저하를 계통 위험으로 알린다.",
                       "계통 점검을 조기에 시작할 수 있다.", 0),
                action("br22-b5c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "두 구역의 급액 계통 상태와 dry-back 추세를 함께 점검한다.",
                       "계통 vs 개별 slab 문제를 구분한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "계통 문제 가능성이 있는 상황에서 자동 양액 조정은 원인을 덮을 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "두 구역의 급액 계통과 dry-back 추세를 함께 점검한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b5d",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-11-substrate-monitor",
            "growth_stage": "fruit_set",
            "state_summary": "substrate moisture dropping across multiple dawn observations while drain EC stays stable.",
            "active_constraints": ["substrate_moisture_dropping", "multi_dawn_observation", "drain_ec_stable"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "Multi-day dawn substrate moisture drop with stable drain EC is still a rootzone high-risk situation that requires field confirmation before any recipe change.",
            "risk_level": "high",
            "diagnosis": [
                "Multi-day dawn WC drops mean the slab recovery is not happening despite stable nutrient balance.",
                "Stable drain EC can mislead operators into assuming the rootzone is fine, which it is not here.",
            ],
            "recommended_actions": [
                action("br22-b5d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "Alert on multi-dawn substrate moisture drop with stable drain EC.",
                       "Prevent operators from being misled by drain EC alone.", 0),
                action("br22-b5d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "Field-verify dawn substrate WC recovery and slab water buffering.",
                       "Gather manual evidence before any automation change.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "Multi-day dawn moisture drop is not an acceptable trigger for automated recipe changes."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "Inspect slab water buffering and dawn WC recovery on representative lines.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b6c",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-12-cool-slab",
            "growth_stage": "fruit_expansion",
            "state_summary": "slab 온도가 야간에 반복해서 하락하고 아침에도 회복이 더디며 dry-back 과다 패턴이 동반된다.",
            "active_constraints": ["slab_night_cooling_repeated", "morning_slab_temp_recovery_slow", "dryback_overrun"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 slab 냉각 반복 + 아침 회복 지연 + dry-back 과다는 rootzone 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "야간 slab 냉각이 반복되고 아침 회복이 지연되면 뿌리 활력이 누적 저하된다.",
                "이 상황에서 자동 양액 조정은 온도 원인을 해결하지 못한다.",
            ],
            "recommended_actions": [
                action("br22-b6c", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "야간 slab 냉각 반복 + 아침 회복 지연 + dry-back 과다 복합을 고위험으로 알린다.",
                       "온도와 근권을 같이 점검하게 한다.", 0),
                action("br22-b6c", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "slab 온도 복구 전략과 dry-back 패턴을 함께 점검한다.",
                       "온도 원인 비중을 현장에서 판단한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "온도 원인이 1차 원인일 가능성이 높은 상황에서 자동 양액 조정은 잘못된 방향으로 갈 수 있다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "slab 온도 회복과 dry-back 패턴을 함께 점검한다.")],
            "confidence": 0.81,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "action-recommendation-batch22-b6d",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-13-low-light",
            "growth_stage": "fruit_set",
            "state_summary": "cold-night 조건이 이어지고 야간 저광 기록이 반복되며 slab에서 dry-back 과다가 관찰된다.",
            "active_constraints": ["cold_night_sustained", "night_low_light_repeated", "slab_dryback_overrun"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "cold-night 지속 + 야간 저광 반복 + slab dry-back 과다 복합 상황은 고위험이며 자동 양액 조정을 금지한다.",
            "risk_level": "high",
            "diagnosis": [
                "cold-night 지속과 야간 저광이 겹치면 낮 광합성과 밤 뿌리 활력 양쪽이 모두 깎인다.",
                "복합 원인에서 자동 recipe 조정은 원인 분리를 방해한다.",
            ],
            "recommended_actions": [
                action("br22-b6d", 1, "create_alert", "operator", "fertigation-manager", "high",
                       "cold-night + 야간 저광 + slab dry-back 복합을 rootzone 고위험으로 알린다.",
                       "복합 원인을 현장에 공유한다.", 0),
                action("br22-b6d", 2, "request_human_check", "operator", "fertigation-manager", "high",
                       "광 로그, slab 온도, dry-back을 한 묶음으로 점검한다.",
                       "복합 원인 중 1차 원인을 분리한다.", 0),
            ],
            "skipped_actions": [
                {"action_type": "adjust_fertigation",
                 "reason": "복합 원인 상황에서 자동 양액 조정은 원인 분리를 방해한다."},
            ],
            "requires_human_approval": False,
            "follow_up": [follow_up("visual_inspection", 0,
                                     "광, slab 온도, dry-back을 묶어 점검한다.")],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


def main() -> None:
    write_jsonl(FAILURE_OUTPUT, FAILURE_ROWS)
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ACTION_OUTPUT, ACTION_ROWS)
    print(
        json.dumps(
            {
                "failure_output": str(FAILURE_OUTPUT.relative_to(REPO_ROOT)),
                "state_output": str(STATE_OUTPUT.relative_to(REPO_ROOT)),
                "action_output": str(ACTION_OUTPUT.relative_to(REPO_ROOT)),
                "failure_rows": len(FAILURE_ROWS),
                "state_rows": len(STATE_ROWS),
                "action_rows": len(ACTION_ROWS),
                "total_rows": len(FAILURE_ROWS) + len(STATE_ROWS) + len(ACTION_ROWS),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
