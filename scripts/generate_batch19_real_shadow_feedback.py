#!/usr/bin/env python3
"""Generate batch19 samples from real-shadow rollback feedback and blind50 residuals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch19_real_shadow_feedback.jsonl"
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch19_real_shadow_feedback.jsonl"
FAILURE_OUTPUT = REPO_ROOT / "data/examples/failure_response_samples_batch19_real_shadow_feedback.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data/examples/robot_task_samples_batch19_real_shadow_feedback.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-house-safety-001": "RAG-SRC-002",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-crop-env-thresholds-001": "RAG-SRC-001",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-plantfactory-healing-001": "RAG-SRC-001",
    "pepper-harvest-001": "RAG-SRC-001",
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


STATE_ROWS = [
    {
        "sample_id": "state-judgement-401",
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-irrigation-zone",
            "growth_stage": "harvest",
            "state_summary": "작업자가 관수 레인 안에 있고 manual override가 active인데 irrigation manifold 자동 재시작 큐가 남아 있다.",
            "active_constraints": ["worker_present", "manual_override_active", "irrigation_restart_queued"],
            "retrieved_context": ["pepper-agent-001", "pepper-house-safety-001"],
        },
        "preferred_output": {
            "situation_summary": "작업자 진입과 manual override가 동시에 active인 동안에는 자동 제어보다 차단과 경고가 먼저다.",
            "risk_level": "critical",
            "diagnosis": [
                "real shadow rollback 원인처럼 작업자 존재와 manual override는 자동 급수 재시작보다 안전 인터락이 우선인 상태다.",
                "이 구간에서는 request_human_check만으로는 부족하고 block_action과 create_alert를 즉시 내야 한다."
            ],
            "recommended_actions": [
                action(
                    "state19-401",
                    1,
                    "block_action",
                    "system",
                    "gh-01-irrigation-zone-action-gate",
                    "critical",
                    "작업자 진입과 manual override가 active인 동안 irrigation manifold 자동 재시작을 즉시 차단한다.",
                    "작업자-장치 충돌과 수동 복구 중 자동 재기동을 막는다.",
                    0,
                ),
                action(
                    "state19-401",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-irrigation-zone",
                    "critical",
                    "자동 재시작 차단과 안전 인터락 유지 상태를 운영자에게 즉시 알린다.",
                    "현장 해제 조건과 복구 순서를 수동 확인 기준으로 유지할 수 있다.",
                    5,
                ),
            ],
            "robot_tasks": [],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("operator_confirm", 0, "작업자 퇴장, manual override 해제, manifold 실제 상태를 확인한다.")
            ],
            "confidence": 0.96,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-house-safety-001")],
        },
    },
    {
        "sample_id": "state-judgement-402",
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-pack",
            "growth_stage": "harvest",
            "state_summary": "estop latch가 active인데 pallet conveyor 자동 복귀 큐가 남아 있다.",
            "active_constraints": ["estop_latched", "worker_present"],
            "retrieved_context": ["pepper-agent-001", "pepper-house-safety-001"],
        },
        "preferred_output": {
            "situation_summary": "estop latch가 active인 동안에는 conveyor 자동 복귀보다 차단과 경고가 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "estop latch는 안전 해제 전 자동 복귀를 허용하면 안 되는 hard safety 상태다.",
                "이때 pause_automation이나 단순 확인 요청만 내면 인터락 위반을 막지 못한다."
            ],
            "recommended_actions": [
                action(
                    "state19-402",
                    1,
                    "block_action",
                    "system",
                    "gh-01-zone-pack-action-gate",
                    "critical",
                    "estop latch가 active인 동안 conveyor 자동 복귀를 즉시 차단한다.",
                    "안전 해제 전 장치가 다시 기동되는 것을 막는다.",
                    0,
                ),
                action(
                    "state19-402",
                    2,
                    "create_alert",
                    "zone",
                    "gh-01-zone-pack",
                    "critical",
                    "estop latch 유지와 자동 복귀 차단 상태를 즉시 알린다.",
                    "현장 해제 절차를 누락 없이 유지할 수 있다.",
                    5,
                ),
            ],
            "robot_tasks": [],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("operator_confirm", 0, "estop 해제 승인과 conveyor 실제 정지 상태를 확인한다.")
            ],
            "confidence": 0.96,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001"), citation("pepper-house-safety-001")],
        },
    },
    {
        "sample_id": "state-judgement-403",
        "task_type": "climate_risk",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-nursery",
            "growth_stage": "nursery",
            "state_summary": "Grodan Delta 6.5 육묘 블록 구간에서 해진 뒤 보온은 유지되지만 습도가 높고 잎 젖음 시간이 늘고 있다.",
            "active_constraints": ["delta65_nursery_leaf_wet_watch", "night_heat_retention_mode"],
            "retrieved_context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "Delta 6.5 육묘 구간의 해진 뒤 냉습 조건과 잎 젖음 시간 증가는 활착 지연과 병해 위험을 동시에 높인다.",
            "risk_level": "high",
            "diagnosis": [
                "육묘기 냉습 조건은 활착 전 병해와 생육 지연 위험을 동시에 키우므로 risk_level을 medium으로 낮추면 안 된다.",
                "이 경우 adjust_vent를 reflex처럼 열기보다 경고와 현장 확인이 먼저다."
            ],
            "recommended_actions": [
                action(
                    "state19-403",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-nursery",
                    "high",
                    "육묘 냉습·잎 젖음 복합 위험을 즉시 기록한다.",
                    "육묘 활착 지연과 병해 리스크를 빠르게 인지할 수 있다.",
                    10,
                ),
                action(
                    "state19-403",
                    2,
                    "request_human_check",
                    "operator",
                    "nursery-manager",
                    "medium",
                    "실제 잎 젖음 시간, 육묘 활착 상태, 난방·보온 커튼 상태를 현장에서 확인한다.",
                    "냉습 리스크와 야간 보온 상태를 현장 기준으로 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_vent",
                    "reason": "해진 뒤 육묘 구간에서 환기를 바로 열면 보온 유지가 무너져 활착 지연이 더 커질 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 블록의 잎 젖음 시간과 난방·보온 커튼 상태를 다시 확인한다.")
            ],
            "confidence": 0.82,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-plantfactory-healing-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-404",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruit_expansion",
            "state_summary": "GT Master 슬래브에서 급액 EC 2.6 대비 배액 EC 5.3이 반복되고 배액률도 14%로 낮다.",
            "active_constraints": ["salt_accumulation_watch", "low_drain_fraction_watch"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "급액 대비 배액 EC 차이가 크게 벌어지고 배액률이 낮아 염류 집적과 근권 스트레스 위험이 높다.",
            "risk_level": "high",
            "diagnosis": [
                "급액 대비 배액 EC 차이가 2.5를 넘고 배액률이 낮으면 GT Master slab 내 염류 집적 가능성이 높다.",
                "이 경우 observe_only나 즉시 recipe 변경보다 create_alert와 request_human_check가 먼저다."
            ],
            "recommended_actions": [
                action(
                    "state19-404",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit",
                    "high",
                    "염류 집적과 낮은 배액률이 겹친 고위험 nutrient risk를 즉시 알린다.",
                    "운영자가 flush 필요성과 현장 점검을 우선순위로 올릴 수 있다.",
                    10,
                ),
                action(
                    "state19-404",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 slab의 drain EC, drain fraction, mixing 상태를 현장에서 다시 확인한다.",
                    "실제 염류 집적과 line 편차를 구분할 수 있다.",
                    0,
                ),
            ],
            "follow_up": [
                follow_up("trend_review", 20, "대표 slab의 급액 EC, 배액 EC, 배액률 추세를 다시 확인한다.")
            ],
            "requires_human_approval": False,
            "confidence": 0.85,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "state-judgement-405",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruit_expansion",
            "state_summary": "GT Master 슬래브의 새벽 WC가 낮고 야간 dry-back이 과도한 날마다 오후 잎 처짐 메모가 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "field_rootzone_recheck"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master dry-back 과다와 낮은 새벽 WC, 반복 잎 처짐은 rootzone stress 고위험 신호다.",
            "risk_level": "high",
            "diagnosis": [
                "GT Master dry-back 과다와 낮은 새벽 WC, 반복 잎 처짐은 rootzone stress high slice로 고정해야 한다.",
                "이 구간에서는 adjust_fertigation reflex를 금지하고 create_alert와 request_human_check를 먼저 낸다."
            ],
            "recommended_actions": [
                action(
                    "state19-405",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit",
                    "high",
                    "GT Master line의 rootzone stress 고위험을 즉시 공유한다.",
                    "운영자가 현장 점검과 응급 대응 우선순위를 바로 올릴 수 있다.",
                    10,
                ),
                action(
                    "state19-405",
                    2,
                    "request_human_check",
                    "operator",
                    "crop-manager",
                    "medium",
                    "대표 slab의 dawn WC, dry-back, 잎 처짐 시점을 현장에서 다시 확인한다.",
                    "recipe 변경 전 실제 rootzone stress 여부를 다시 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "반복 잎 처짐과 낮은 dawn WC만으로는 recipe 변경이 정답인지 확정할 수 없어 자동 급액 조정은 보류한다.",
                }
            ],
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab의 dawn WC, dry-back, 잎 처짐 발생 시점을 다시 확인한다.")
            ],
            "requires_human_approval": False,
            "confidence": 0.85,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


ACTION_ROWS = [
    {
        "sample_id": "action-rec-401",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruit_set",
            "state_summary": "과실 하중 구간 GT Master 라인에서 새벽 WC가 낮고 dry-back이 커진 뒤 낮 시간 잎 처짐이 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "field_rootzone_recheck"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 하중 구간 GT Master dry-back 과다는 현장 확인이 먼저인 high rootzone stress 신호다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중 구간의 GT Master dry-back 과다는 근권 스트레스와 잎 처짐 재발로 이어질 수 있다.",
                "이 상황에서는 adjust_fertigation보다 create_alert와 request_human_check가 먼저다."
            ],
            "recommended_actions": [
                action(
                    "action19-401",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit",
                    "high",
                    "GT Master line의 rootzone stress 고위험과 반복 잎 처짐 사실을 즉시 공유한다.",
                    "운영자가 현장 점검과 응급 대응 우선순위를 바로 올릴 수 있다.",
                    10,
                ),
                action(
                    "action19-401",
                    2,
                    "request_human_check",
                    "operator",
                    "crop-manager",
                    "medium",
                    "대표 slab의 dawn WC, dry-back, 잎 처짐 시점과 dripper 편차를 현장에서 다시 확인한다.",
                    "recipe 변경 전 실제 rootzone stress 여부를 다시 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "과실 하중 구간의 dry-back 과다는 현장 확인 전 자동 급액 조정으로 바로 대응하면 원인 분리를 놓칠 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab의 dawn WC, dry-back, 잎 처짐 재발 여부를 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-crop-env-thresholds-001")],
        },
    }
]


FAILURE_ROWS = [
    {
        "sample_id": "failure-response-401",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-water-room",
            "growth_stage": "fruit_set",
            "failure_type": "source_water_valve_communication_loss",
            "state_summary": "원수 메인 밸브 통신이 끊겨 현재 개폐 상태와 마지막 명령 반영 여부를 신뢰할 수 없다.",
            "active_faults": ["source_water_path_degraded", "execution_state_unknown"],
            "last_action": "short_irrigation",
            "retrieved_context": ["pepper-rootzone-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "핵심 수계 경로 통신 손실이라 원수 상태를 신뢰할 수 없어 즉시 safe mode 전환이 필요하다.",
            "risk_level": "critical",
            "diagnosis": [
                "핵심 water-delivery path의 communication/readback loss는 실제 급수 상태를 확인할 수 없는 critical failure다.",
                "이 구간에서는 pause_automation만으로는 부족하고 enter_safe_mode와 request_human_check가 우선이다."
            ],
            "recommended_actions": [
                action(
                    "fail19-401",
                    1,
                    "enter_safe_mode",
                    "system",
                    "gh-01-water-room-control",
                    "critical",
                    "핵심 수계 경로를 신뢰할 수 없어 자동 제어를 안전 모드로 전환한다.",
                    "불명확한 급수 상태에서 자동 명령 누적을 막는다.",
                    0,
                ),
                action(
                    "fail19-401",
                    2,
                    "request_human_check",
                    "operator",
                    "irrigation-manager",
                    "high",
                    "현장에서 전원, 통신, 실제 개폐 상태를 확인한다.",
                    "수동 복구 전 실제 water path 상태를 빠르게 확인할 수 있다.",
                    0,
                ),
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                follow_up("device_readback", 5, "원수 메인 밸브 전원, 통신, 실제 개폐 상태를 확인한다.")
            ],
            "confidence": 0.94,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-agent-001")],
        },
    }
]


ROBOT_ROWS = [
    {
        "sample_id": "robot-task-401",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-c",
            "state_summary": "수확 후보 두 개 중 하나는 pallet block으로 바로 접근할 수 없어 우회가 먼저 필요하다.",
            "candidates": [
                {"candidate_id": "harvest-41", "ripeness_score": 0.81, "reachable": False, "vision_confidence": 0.79},
                {"candidate_id": "harvest-42", "ripeness_score": 0.77, "reachable": True, "vision_confidence": 0.72},
            ],
            "safety_context": {"worker_present": False, "robot_zone_clear": False},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "blocked candidate는 generic review가 아니라 skip_area가 먼저다.",
            "risk_level": "high",
            "robot_tasks": [
                {
                    "task_type": "skip_area",
                    "candidate_id": "harvest-41",
                    "target": {"target_type": "candidate", "target_id": "harvest-41"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "pallet block 때문에 바로 접근할 수 없어 우회 지시가 먼저 필요하다.",
                }
            ],
            "skipped_candidates": [
                {
                    "candidate_id": "harvest-42",
                    "reason": "blocked candidate 우회 지시가 먼저라 이번 사이클에서는 뒤 순위로 둔다."
                }
            ],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("operator_confirm", 10, "pallet block 해제 여부와 우회 가능 aisle을 확인한다.")
            ],
            "confidence": 0.8,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    }
]


def main() -> None:
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ACTION_OUTPUT, ACTION_ROWS)
    write_jsonl(FAILURE_OUTPUT, FAILURE_ROWS)
    write_jsonl(ROBOT_OUTPUT, ROBOT_ROWS)
    total = len(STATE_ROWS) + len(ACTION_ROWS) + len(FAILURE_ROWS) + len(ROBOT_ROWS)
    print(f"state_rows: {len(STATE_ROWS)}")
    print(f"action_rows: {len(ACTION_ROWS)}")
    print(f"failure_rows: {len(FAILURE_ROWS)}")
    print(f"robot_rows: {len(ROBOT_ROWS)}")
    print(f"total_rows: {total}")
    print(f"state_output: {STATE_OUTPUT.as_posix()}")
    print(f"action_output: {ACTION_OUTPUT.as_posix()}")
    print(f"failure_output: {FAILURE_OUTPUT.as_posix()}")
    print(f"robot_output: {ROBOT_OUTPUT.as_posix()}")


if __name__ == "__main__":
    main()
