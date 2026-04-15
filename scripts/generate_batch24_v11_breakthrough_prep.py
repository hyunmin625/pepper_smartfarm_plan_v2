#!/usr/bin/env python3
"""Generate batch24 corrective samples for v11 breakthrough preparation.

This batch does not assume retraining will beat ds_v11. It only strengthens
the two weakest preconditions identified in local reports:
1. edge-eval-021 style `reentry_pending + dry_room_comm_loss` hard-block pattern
2. low-count task families (`state_judgement`, `harvest_drying`)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FAILURE_OUTPUT = REPO_ROOT / "data/examples/failure_response_samples_batch24_reentry_block_priority.jsonl"
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch24_lowcount_rebalance.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data/examples/robot_task_samples_batch24_inspect_crop_contract.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-dry-storage-maintenance-001": "RAG-SRC-001",
    "pepper-harvest-001": "RAG-SRC-001",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-lifecycle-001": "RAG-SRC-001",
    "pepper-rootzone-001": "RAG-SRC-004",
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


def robot_task(
    prefix: str,
    index: int,
    task_type: str,
    target_type: str,
    target_id: str,
    priority: str,
    reason: str,
    *,
    approval_required: bool = True,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "task_id": f"{prefix}-task-{index:03d}",
        "task_type": task_type,
        "priority": priority,
        "approval_required": approval_required,
        "reason": reason,
        "target": {"target_type": target_type, "target_id": target_id},
    }
    if candidate_id:
        payload["candidate_id"] = candidate_id
    return payload


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


FAILURE_ROWS = [
    {
        "sample_id": "failure-response-801",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "dry-room-2",
            "growth_stage": "harvest",
            "state_summary": "건조실 통신 손실이 있고 reentry_pending 상태라 자동 제어를 바로 재개할 수 없으며, 이전 건조 cycle 승인도 아직 닫히지 않았다.",
            "active_constraints": ["dry_room_comm_loss", "reentry_pending", "restart_approval_open"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "reentry_pending이 남아 있는 건조실 통신 손실은 safe_mode 재진입보다 hard block과 운영자 경고가 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "reentry_pending은 자동 복귀 조건이 아직 닫히지 않았다는 뜻이라 comm loss와 겹치면 enter_safe_mode보다 block_action이 먼저다.",
                "이 slice는 품질 제어 장애가 아니라 안전 잠금 우선 시나리오라 create_alert가 반드시 같이 나와야 한다.",
            ],
            "recommended_actions": [
                action(
                    "failure24-801",
                    1,
                    "block_action",
                    "system",
                    "dry-room-2-action-gate",
                    "critical",
                    "reentry 승인 전에는 어떤 자동 복귀 경로도 열지 않는다.",
                    "건조실 장치가 승인 없이 재기동되는 것을 막는다.",
                    0,
                ),
                action(
                    "failure24-801",
                    2,
                    "create_alert",
                    "zone",
                    "dry-room-2",
                    "critical",
                    "통신 손실과 reentry_pending이 동시에 active인 hard-block 상태를 즉시 공유한다.",
                    "운영자가 승인 상태와 현장 복구 순서를 먼저 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "enter_safe_mode",
                    "reason": "reentry_pending이 남아 있는 동안 safe mode 재진입은 승인 우선 원칙을 깨므로 금지한다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("operator_confirm", 0, "reentry 승인 상태, 통신 복구 여부, 건조실 실제 정지 상태를 함께 확인한다.")
            ],
            "confidence": 0.95,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "failure-response-802",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "dry-room-3",
            "growth_stage": "harvest",
            "state_summary": "건조실 제습기 통신이 끊겼고 reentry_pending 상태에서 작업자 출입 로그도 아직 열려 있어 자동 복귀를 보류해야 한다.",
            "active_constraints": ["dry_room_comm_loss", "reentry_pending", "worker_entry_open"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "건조실 통신 손실과 reentry_pending, 작업자 출입 미종결이 겹치면 hard block이 safe mode보다 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "작업자 출입 로그가 열려 있으면 장치 상태를 모르는 채 safe mode로 복귀시키면 안 된다.",
                "이 케이스는 request_human_check만으로 부족하고 block_action과 create_alert가 같이 나와야 한다.",
            ],
            "recommended_actions": [
                action(
                    "failure24-802",
                    1,
                    "block_action",
                    "system",
                    "dry-room-3-action-gate",
                    "critical",
                    "작업자 출입 종료와 reentry 승인 확인 전까지 자동 건조 제어를 차단한다.",
                    "출입 중 장치 재기동과 승인 누락을 막는다.",
                    0,
                ),
                action(
                    "failure24-802",
                    2,
                    "create_alert",
                    "zone",
                    "dry-room-3",
                    "critical",
                    "통신 손실, reentry_pending, 작업자 출입 미종결이 겹친 안전 잠금 상태를 운영자에게 즉시 알린다.",
                    "현장 확인과 승인 절차를 먼저 실행하게 만든다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "enter_safe_mode",
                    "reason": "작업자 출입 로그가 열린 reentry_pending 구간에서는 safe mode보다 hard block이 우선이다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("operator_confirm", 0, "작업자 출입 종료, reentry 승인, 제습기 통신 복구를 순서대로 확인한다.")
            ],
            "confidence": 0.95,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "failure-response-803",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "dry-room-4",
            "growth_stage": "harvest",
            "state_summary": "건조실 환기 제어 통신이 사라졌고 reentry_pending 상태에서 lot 전환 배치가 아직 열려 있어 자동 제어를 바로 재개할 수 없다.",
            "active_constraints": ["dry_room_comm_loss", "reentry_pending", "lot_change_pending"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "lot 전환이 닫히지 않은 건조실 reentry_pending 구간에서는 block_action과 create_alert를 먼저 고정해야 한다.",
            "risk_level": "critical",
            "diagnosis": [
                "lot change pending은 품질 책임 구간이 아직 종료되지 않았다는 의미라 통신 손실과 겹치면 hard block이 우선이다.",
                "safe mode 재진입은 lot 전환 승인과 통신 복구를 가리지 못해 forbidden으로 두는 편이 맞다.",
            ],
            "recommended_actions": [
                action(
                    "failure24-803",
                    1,
                    "block_action",
                    "system",
                    "dry-room-4-action-gate",
                    "critical",
                    "lot 전환 종료와 통신 복구 확인 전에는 자동 건조 장치 제어를 재개하지 않는다.",
                    "품질 lot 경계와 장치 안전 경계를 동시에 지킬 수 있다.",
                    0,
                ),
                action(
                    "failure24-803",
                    2,
                    "create_alert",
                    "zone",
                    "dry-room-4",
                    "critical",
                    "lot 전환 미종결 상태에서 통신 손실이 발생한 건조실 hard-block 상태를 즉시 기록한다.",
                    "운영자가 lot 전환 종료와 복구 우선순위를 정할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "enter_safe_mode",
                    "reason": "lot 전환이 닫히지 않은 reentry_pending 구간에서는 enter_safe_mode보다 block_action이 우선이다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("operator_confirm", 0, "lot 전환 종료 여부, reentry 승인, 환기 제어 통신 복구를 함께 확인한다.")
            ],
            "confidence": 0.94,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "failure-response-804",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "dry-room-5",
            "growth_stage": "harvest",
            "state_summary": "건조실 통신 손실이 있고 reentry_pending 상태에서 원격 reset ack도 들어오지 않아 자동 복귀 근거가 더 약하다.",
            "active_constraints": ["dry_room_comm_loss", "reentry_pending", "remote_reset_ack_missing"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "reentry_pending에 원격 reset ack 누락까지 겹치면 safe mode보다 block_action + create_alert가 더 강한 기본 패턴이다.",
            "risk_level": "critical",
            "diagnosis": [
                "원격 reset ack까지 비어 있으면 자동 복귀 근거가 더 약해져 enter_safe_mode를 허용하면 안 된다.",
                "이 케이스는 hard block과 운영자 경고를 먼저 묶어야 다음 단계 수동 복구가 안전하다.",
            ],
            "recommended_actions": [
                action(
                    "failure24-804",
                    1,
                    "block_action",
                    "system",
                    "dry-room-5-action-gate",
                    "critical",
                    "원격 reset ack와 reentry 승인이 모두 확인되기 전까지 자동 복귀를 차단한다.",
                    "근거 없는 재기동과 재진입을 막는다.",
                    0,
                ),
                action(
                    "failure24-804",
                    2,
                    "create_alert",
                    "zone",
                    "dry-room-5",
                    "critical",
                    "통신 손실, reentry_pending, reset ack 누락이 겹친 hard-block 상태를 운영자에게 즉시 알린다.",
                    "현장 복구와 승인 경로를 수동으로 닫게 만든다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "enter_safe_mode",
                    "reason": "reset ack가 없는 reentry_pending 상태에서는 enter_safe_mode 재진입을 허용하면 안 된다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("operator_confirm", 0, "원격 reset ack, reentry 승인, 건조실 통신 복구 여부를 함께 확인한다.")
            ],
            "confidence": 0.95,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
]


STATE_ROWS = [
    {
        "sample_id": "state-judgement-801",
        "task_type": "state_judgement",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-balance-a",
            "growth_stage": "fruit_expansion",
            "state_summary": "온습도, VPD, 배지 함수율, drain EC가 모두 안정 범위에 있고 센서 품질도 양호하다.",
            "active_constraints": [],
            "retrieved_context": ["pepper-lifecycle-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 비대기 현재 상태는 전반적으로 안정적이라 과잉 제어보다 관찰 유지가 적절하다.",
            "risk_level": "low",
            "diagnosis": [
                "핵심 기후·근권 센서가 모두 안정적이면 현재 상태 판단 신뢰도가 높다.",
                "불필요한 장치 제어보다 추세 관찰을 유지하는 편이 더 안전하다.",
            ],
            "recommended_actions": [
                action(
                    "state24-801",
                    1,
                    "observe_only",
                    "zone",
                    "gh-01-zone-balance-a",
                    "low",
                    "명확한 스트레스 신호가 없어 현재 운전을 유지한다.",
                    "안정 구간에서 과잉 제어를 피할 수 있다.",
                    30,
                )
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 30, "온습도, VPD, 배지 함수율 추세가 계속 안정적인지 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-lifecycle-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-802",
        "task_type": "state_judgement",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-balance-b",
            "growth_stage": "transplanting",
            "state_summary": "정식 직후 야간 저온 경계는 있지만 낮에는 회복되고 배지 과습 신호도 심하지 않다.",
            "active_constraints": ["post_transplant_conservative_mode"],
            "retrieved_context": ["pepper-lifecycle-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "정식 초기라 보수적으로 봐야 하지만 현재는 즉시 high로 올리기보다 medium 경계 관리가 맞다.",
            "risk_level": "medium",
            "diagnosis": [
                "정식 초기 야간 저온 경계는 활착 지연 위험이 있지만 낮 회복이 유지되면 먼저 현장 확인으로 관리할 수 있다.",
                "이 구간은 자동 관수나 공격적 제어보다 사람 확인과 경고를 같이 두는 편이 맞다.",
            ],
            "recommended_actions": [
                action(
                    "state24-802",
                    1,
                    "request_human_check",
                    "operator",
                    "crop-manager",
                    "medium",
                    "야간 보온 상태와 활착 초기 과습 여부를 현장에서 다시 확인한다.",
                    "정식 초기 스트레스 신호를 실제 현장 기준으로 다시 볼 수 있다.",
                    0,
                ),
                action(
                    "state24-802",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-zone-balance-b",
                    "medium",
                    "정식 초기 저온 경계 상태를 운영 기록에 남긴다.",
                    "야간 보온 대응을 누락하지 않게 만든다.",
                    20,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 30, "활착 상태와 배지 수분 상태를 다시 확인한다.")
            ],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-lifecycle-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-803",
        "task_type": "harvest_drying",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-dry-room-a",
            "growth_stage": "drying",
            "state_summary": "건조실 평균 습도는 허용 범위지만 lot별 함수율 편차가 다시 벌어지고 일부 tray에서 표면 재흡습 메모가 들어왔다.",
            "active_constraints": ["lot_moisture_variance", "surface_rewet_watch"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-dry-storage-maintenance-001"],
        },
        "preferred_output": {
            "situation_summary": "건조실 평균 조건이 안정적이어도 lot별 함수율 편차와 재흡습 징후가 있으면 medium harvest_drying risk로 관리해야 한다.",
            "risk_level": "medium",
            "diagnosis": [
                "평균 습도만 안정적이라고 해서 lot별 함수율 편차와 표면 재흡습 위험이 사라지지 않는다.",
                "이 구간은 자동 송풍 변경보다 request_human_check와 create_alert를 먼저 묶는 편이 맞다.",
            ],
            "recommended_actions": [
                action(
                    "state24-803",
                    1,
                    "request_human_check",
                    "operator",
                    "drying-manager",
                    "medium",
                    "lot별 함수율 편차와 표면 재흡습 징후를 현장에서 다시 확인한다.",
                    "평균값에 가려진 lot 편차를 놓치지 않을 수 있다.",
                    0,
                ),
                action(
                    "state24-803",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-dry-room-a",
                    "medium",
                    "lot 편차와 재흡습 watch를 건조 품질 리스크로 기록한다.",
                    "후속 재건조나 lot 분리 판단을 빠르게 할 수 있다.",
                    20,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("lab_test", 30, "lot별 함수율을 다시 측정하고 재흡습 징후 tray를 구분한다.")
            ],
            "confidence": 0.79,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-dry-storage-maintenance-001")],
        },
    },
    {
        "sample_id": "state-judgement-804",
        "task_type": "harvest_drying",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-dry-room-b",
            "growth_stage": "harvest",
            "state_summary": "착색된 수확 후보는 늘었지만 건조실 적재 여력이 부족하고 대기 lot에 결로 메모가 남아 있다.",
            "active_constraints": ["dry_room_capacity_tight", "condensation_watch"],
            "retrieved_context": ["pepper-harvest-001", "pepper-house-drying-hygiene-001"],
        },
        "preferred_output": {
            "situation_summary": "수확 후보가 늘어도 건조실 적재 여력과 결로 watch를 같이 보면 medium harvest_drying risk로 보는 편이 맞다.",
            "risk_level": "medium",
            "diagnosis": [
                "수확 적기 판단만 보고 lot를 밀어 넣으면 결로 watch와 적재 과밀로 품질이 무너질 수 있다.",
                "이 경우 사람 확인으로 적재 여력과 lot 순서를 먼저 정해야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state24-804",
                    1,
                    "request_human_check",
                    "operator",
                    "harvest-manager",
                    "medium",
                    "수확 후보, 건조실 적재 여력, 결로 watch lot를 함께 다시 확인한다.",
                    "수확과 건조를 같은 리듬으로 묶을 수 있다.",
                    0,
                ),
                action(
                    "state24-804",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-dry-room-b",
                    "medium",
                    "적재 여력 부족과 결로 watch를 품질 리스크로 남긴다.",
                    "적재 과밀과 재흡습 위험을 빠르게 공유할 수 있다.",
                    20,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대기 lot 결로와 건조실 적재 여력을 다시 확인한다.")
            ],
            "confidence": 0.78,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-house-drying-hygiene-001")],
        },
    },
    {
        "sample_id": "state-judgement-805",
        "task_type": "harvest_drying",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-dry-room-c",
            "growth_stage": "drying",
            "state_summary": "건조 종료 직전 일부 lot 함수율은 목표치에 도달했지만 다른 lot는 아직 높고 출하 분리 태그가 미완료다.",
            "active_constraints": ["lot_split_pending", "final_moisture_variance"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-dry-storage-maintenance-001"],
        },
        "preferred_output": {
            "situation_summary": "건조 종료 직전 lot 분리 태그가 미완료이고 함수율 편차가 남아 있으면 medium risk로 두고 사람 확인이 먼저다.",
            "risk_level": "medium",
            "diagnosis": [
                "건조 종료 직전 lot별 함수율 차이가 남아 있으면 일괄 종료보다 lot 분리 판단이 먼저다.",
                "출하 분리 태그가 미완료면 품질 혼입 위험이 있어 사람 확인을 꼭 묶어야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state24-805",
                    1,
                    "request_human_check",
                    "operator",
                    "drying-manager",
                    "medium",
                    "lot별 함수율과 분리 태그 상태를 현장에서 다시 확인한다.",
                    "혼입과 미건조 lot를 분리할 수 있다.",
                    0,
                ),
                action(
                    "state24-805",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-dry-room-c",
                    "medium",
                    "건조 종료 직전 lot 편차와 분리 태그 미완료 상태를 기록한다.",
                    "출하 전 품질 판단 누락을 줄일 수 있다.",
                    15,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("lab_test", 20, "lot별 함수율 재측정과 분리 태그 완료 여부를 확인한다.")
            ],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-dry-storage-maintenance-001")],
        },
    },
    {
        "sample_id": "state-judgement-806",
        "task_type": "harvest_drying",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-harvest-line-a",
            "growth_stage": "harvest",
            "state_summary": "성숙 과실 비율은 높지만 일부 lot에서 표면 손상과 과숙 혼입이 보여 수확 후보 정리를 먼저 해야 한다.",
            "active_constraints": ["ripe_candidate_mix", "surface_damage_watch"],
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "성숙 후보가 많아도 표면 손상과 과숙 혼입이 보이면 medium harvest_drying risk로 보고 사람 확인을 먼저 둔다.",
            "risk_level": "medium",
            "diagnosis": [
                "수확량 확보보다 손상 과실과 과숙 혼입 분리가 먼저다.",
                "로봇 후보 검토를 쓰더라도 최종 후보 확정은 request_human_check가 먼저여야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state24-806",
                    1,
                    "request_human_check",
                    "operator",
                    "harvest-manager",
                    "medium",
                    "손상 과실, 과숙 혼입, 수확 후보 범위를 현장에서 다시 확인한다.",
                    "수확 후보 정렬과 후속 건조 lot 품질을 함께 맞출 수 있다.",
                    0,
                ),
                action(
                    "state24-806",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-harvest-line-a",
                    "medium",
                    "수확 후보 혼입과 표면 손상 watch를 품질 리스크로 기록한다.",
                    "성숙도만 보고 밀어붙이는 수확을 막을 수 있다.",
                    15,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 15, "수확 후보 중 손상 과실과 과숙 혼입 비율을 다시 확인한다.")
            ],
            "confidence": 0.77,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-807",
        "task_type": "sensor_fault",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-dry-room-sensor-a",
            "growth_stage": "drying",
            "state_summary": "건조실 습도 센서가 stale인데 일부 tray 표면 결로 메모가 함께 들어와 장치 제어 근거가 불완전하다.",
            "active_constraints": ["dry_room_humidity_stale", "surface_condensation_watch"],
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "건조실 습도 센서 stale 상태라 결로 watch를 자동 고위험으로 단정하기보다 unknown으로 두고 근거 복구가 먼저다.",
            "risk_level": "unknown",
            "diagnosis": [
                "결로 메모가 있어도 핵심 습도 센서가 stale이면 실제 재흡습 수준을 자동으로 확정할 수 없다.",
                "이 구간은 장치 제어보다 pause_automation과 request_human_check가 먼저다.",
            ],
            "recommended_actions": [
                action(
                    "state24-807",
                    1,
                    "pause_automation",
                    "system",
                    "gh-01-dry-room-sensor-a-auto-control",
                    "unknown",
                    "습도 센서 근거가 복구될 때까지 자동 건조 제어를 보류한다.",
                    "stale 센서로 잘못된 송풍·제습 명령이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    "state24-807",
                    2,
                    "request_human_check",
                    "operator",
                    "drying-manager",
                    "unknown",
                    "습도 센서 최신값, 결로 여부, tray 상태를 현장에서 다시 확인한다.",
                    "센서 fault와 실제 품질 리스크를 분리할 수 있다.",
                    0,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("sensor_recheck", 10, "습도 센서 최신값과 tray 표면 결로 여부를 함께 확인한다.")
            ],
            "confidence": 0.71,
            "retrieval_coverage": "partial",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-808",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-d",
            "growth_stage": "fruit_expansion",
            "state_summary": "GT Master 4번 라인에서 drain EC가 반복적으로 높고 drain fraction은 낮아 rootzone salt stress가 의심된다.",
            "active_constraints": ["gt_master_salt_accumulation_watch", "low_drain_fraction_watch"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master 라인의 높은 drain EC와 낮은 drain fraction 조합은 high nutrient risk로 보고 alert-first 패턴을 유지해야 한다.",
            "risk_level": "high",
            "diagnosis": [
                "배액 EC 누적과 낮은 배액률이 함께 반복되면 rootzone salt stress 가능성이 높다.",
                "이 구간은 adjust_fertigation reflex보다 create_alert와 request_human_check를 먼저 묶는 편이 맞다.",
            ],
            "recommended_actions": [
                action(
                    "state24-808",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-d",
                    "high",
                    "GT Master 라인의 염류 집적과 낮은 배액률 리스크를 즉시 알린다.",
                    "운영자가 flush 필요성과 line 점검을 우선순위로 올릴 수 있다.",
                    10,
                ),
                action(
                    "state24-808",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 slab의 drain EC, drain fraction, line 편차를 현장에서 다시 확인한다.",
                    "실제 염류 집적과 line 편차를 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "line 편차와 rootzone stress 원인을 확인하기 전 자동 recipe 조정은 과교정 위험이 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "대표 slab의 drain EC, drain fraction, flush window 상태를 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-rootzone-001")],
        },
    },
]


ROBOT_ROWS = [
    {
        "sample_id": "robot-task-801",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-f",
            "state_summary": "수확 hotspot이 보이지만 성숙도 confidence가 낮아 근접 재촬영과 점검이 먼저 필요하다.",
            "candidates": [{"candidate_id": "hotspot-81", "ripeness_score": 0.59, "reachable": True, "vision_confidence": 0.38}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "낮은 confidence 수확 hotspot은 generic task가 아니라 inspect_crop exact enum으로 다시 확인해야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                robot_task(
                    "robot24-801",
                    1,
                    "inspect_crop",
                    "candidate",
                    "hotspot-81",
                    "high",
                    "성숙도 confidence가 낮아 근접 재촬영과 시각 점검이 먼저 필요하다.",
                    candidate_id="hotspot-81",
                )
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("visual_inspection", 15, "hotspot-81의 실제 성숙도와 표면 이상 여부를 다시 확인한다.")
            ],
            "confidence": 0.79,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "robot-task-802",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "drying",
            "zone_id": "gh-01-dry-room-d",
            "state_summary": "건조 tray 일부에서 표면 색 편차와 재흡습 의심이 보여 근접 점검 후보를 먼저 태워야 한다.",
            "candidates": [{"candidate_id": "drylot-81", "ripeness_score": 0.0, "reachable": True, "vision_confidence": 0.44}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "건조 tray 표면 이상 후보는 manual_review 같은 generic 이름이 아니라 inspect_crop exact enum으로 보내야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                robot_task(
                    "robot24-802",
                    1,
                    "inspect_crop",
                    "candidate",
                    "drylot-81",
                    "high",
                    "표면 색 편차와 재흡습 의심 tray는 근접 시각 점검이 먼저 필요하다.",
                    candidate_id="drylot-81",
                )
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("visual_inspection", 15, "drylot-81 tray의 재흡습, 곰팡이, 표면 색 편차를 다시 확인한다.")
            ],
            "confidence": 0.78,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-house-drying-hygiene-001"), citation("pepper-agent-001")],
        },
    },
]


def main() -> None:
    write_jsonl(FAILURE_OUTPUT, FAILURE_ROWS)
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ROBOT_OUTPUT, ROBOT_ROWS)
    print(f"failure_rows: {len(FAILURE_ROWS)} -> {FAILURE_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"state_rows: {len(STATE_ROWS)} -> {STATE_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"robot_rows: {len(ROBOT_ROWS)} -> {ROBOT_OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
