#!/usr/bin/env python3
"""Generate batch18 samples for synthetic shadow day0 residual disagreements."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch12_shadow_day0.jsonl"
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch18_shadow_day0.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data/examples/robot_task_samples_batch7_shadow_day0.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-harvest-001": "RAG-SRC-001",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-crop-env-thresholds-001": "RAG-SRC-001",
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


ACTION_ROWS = [
    {
        "sample_id": "action-rec-033",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-c",
            "growth_stage": "fruit_set",
            "state_summary": "GT Master 과실 라인에서 dawn WC가 낮고 dry-back이 커진 다음 낮 시간 잎 처짐 메모가 다시 누적된다.",
            "active_constraints": ["gt_master_dryback_watch", "leaf_wilt_repeat_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master 과실 라인의 낮은 dawn WC와 반복 잎 처짐은 고위험 rootzone stress라 경고와 현장 확인이 먼저다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중 구간에서 dawn WC 회복 부족과 dry-back 과다는 낮 시간 잎 처짐으로 바로 이어질 수 있다.",
                "이 구간은 adjust_fertigation보다 create_alert + request_human_check를 먼저 내는 패턴을 유지해야 한다.",
            ],
            "recommended_actions": [
                action(
                    "action12-033",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-c",
                    "high",
                    "GT Master line의 rootzone stress 재발과 잎 처짐 위험을 즉시 공유한다.",
                    "운영자가 현장 점검과 응급 대응 우선순위를 바로 올릴 수 있다.",
                    10,
                ),
                action(
                    "action12-033",
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
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab의 dawn WC, dry-back, 잎 처짐 발생 시점을 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-crop-env-thresholds-001")],
        },
    },
    {
        "sample_id": "action-rec-034",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-d",
            "growth_stage": "fruit_expansion",
            "state_summary": "GT Master line에서 고온일 이후 dawn WC 저하와 과도한 night dry-back이 반복되고 오후 잎 처짐이 다시 관찰된다.",
            "active_constraints": ["gt_master_dryback_watch", "line_variability_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "고온일 이후 반복되는 dawn WC 저하와 line-specific dry-back은 high rootzone stress로 보고 경고와 현장 확인을 먼저 해야 한다.",
            "risk_level": "high",
            "diagnosis": [
                "고온일 뒤 회복 부족이 line별로 반복되면 line 편차와 배액 반응을 먼저 확인해야 한다.",
                "이때 adjust_fertigation reflex를 끊고 create_alert + request_human_check를 우선 고정해야 한다.",
            ],
            "recommended_actions": [
                action(
                    "action12-034",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-d",
                    "high",
                    "line-specific rootzone stress와 반복 잎 처짐 위험을 경고한다.",
                    "운영자가 현장 확인과 기록을 우선 시작할 수 있다.",
                    10,
                ),
                action(
                    "action12-034",
                    2,
                    "request_human_check",
                    "operator",
                    "rootzone-manager",
                    "medium",
                    "대표 line의 dawn WC, drain fraction, dripper 편차를 현장에서 다시 확인한다.",
                    "line 편차와 실제 stress 원인을 다시 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "line 편차와 배액 반응 확인 전 recipe 조정을 먼저 걸면 고위험 line을 더 흔들 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 line의 dawn WC와 오후 잎 처짐 재발 시점을 다시 확인한다.")
            ],
            "confidence": 0.83,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


STATE_ROWS = [
    {
        "sample_id": "state-judgement-325",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-c",
            "state_summary": "GT Master slab에서 feed EC 2.6 대비 drain EC 5.2가 반복되고 drain fraction은 12%로 낮다.",
            "active_constraints": ["salt_accumulation_watch", "low_drain_fraction_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "drain EC 누적과 낮은 drain fraction이 함께 반복돼 nutrient risk가 high다.",
            "risk_level": "high",
            "diagnosis": [
                "feed 대비 drain EC가 크게 높고 배액률이 낮으면 slab 내 염류 집적 가능성이 높다.",
                "이 시점에서는 adjust_fertigation보다 create_alert + request_human_check를 먼저 내야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state18-325",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-c",
                    "high",
                    "염류 집적과 낮은 drain fraction이 겹친 nutrient risk를 즉시 알린다.",
                    "운영자가 flush 필요성과 line 점검을 우선순위로 올릴 수 있다.",
                    10,
                ),
                action(
                    "state18-325",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 slab의 drain EC, drain fraction, mixing 상태를 다시 확인한다.",
                    "실제 염류 집적과 line 편차를 다시 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "현장 점검 전 recipe를 바로 바꾸면 mixing 문제와 line 편차를 놓칠 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "대표 slab의 feed EC, drain EC, drain fraction 추세를 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-326",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-d",
            "state_summary": "GT Master 구역에서 drain EC 5.0이 누적되고 flush window를 놓친 뒤에도 drain fraction은 13%에 머문다.",
            "active_constraints": ["salt_accumulation_watch", "flush_window_missed"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "flush 시점을 놓친 상태에서 drain EC 누적과 낮은 drain fraction이 겹쳐 nutrient risk가 high다.",
            "risk_level": "high",
            "diagnosis": [
                "flush window를 놓친 뒤 drain EC가 계속 높고 drain fraction이 낮으면 염류 집적 위험이 더 커진다.",
                "이 구간에서는 recipe 조정보다 create_alert와 현장 점검이 먼저다.",
            ],
            "recommended_actions": [
                action(
                    "state18-326",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-d",
                    "high",
                    "flush missed + high drain EC 패턴을 고위험 nutrient risk로 즉시 공유한다.",
                    "운영자가 배액과 mixing 상태를 즉시 점검할 수 있다.",
                    10,
                ),
                action(
                    "state18-326",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "flush window 이후 대표 slab의 drain fraction과 mixing 상태를 현장에서 다시 확인한다.",
                    "자동 recipe 변경 전 실제 염류 집적 여부를 다시 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "flush와 drain 상태 확인 전 recipe 조정은 nutrient risk 원인을 가릴 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "flush missed 이후 drain EC와 drain fraction 추세를 다시 확인한다.")
            ],
            "confidence": 0.83,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "state-judgement-327",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-c",
            "state_summary": "GT Master slab의 dawn WC가 낮고 야간 dry-back이 과도했던 날마다 오후 잎 처짐 메모가 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "leaf_wilt_repeat_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master slab의 낮은 dawn WC, 과도한 dry-back, 반복 잎 처짐은 high rootzone stress 패턴이다.",
            "risk_level": "high",
            "diagnosis": [
                "낮은 dawn WC와 과도한 dry-back이 반복되면 오후 잎 처짐과 근권 수분 불균형으로 이어질 수 있다.",
                "이 패턴은 adjust_fertigation보다 create_alert + request_human_check를 먼저 내는 게 맞다.",
            ],
            "recommended_actions": [
                action(
                    "state18-327",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-c",
                    "high",
                    "반복 dry-back과 잎 처짐 패턴을 rootzone stress 고위험으로 즉시 공유한다.",
                    "운영자가 rootzone line 점검을 먼저 시작할 수 있다.",
                    10,
                ),
                action(
                    "state18-327",
                    2,
                    "request_human_check",
                    "operator",
                    "rootzone-manager",
                    "medium",
                    "대표 slab의 dawn WC, dry-back, 잎 처짐 시점을 현장에서 다시 확인한다.",
                    "recipe 조정 전 실제 rootzone stress 여부를 다시 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "반복 잎 처짐과 dawn WC 저하만으로는 recipe 변경이 정답인지 확정할 수 없어 자동 급액 조정은 보류한다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "대표 slab의 dawn WC, dry-back, 잎 처짐 추세를 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-crop-env-thresholds-001")],
        },
    },
    {
        "sample_id": "state-judgement-328",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_set",
            "zone_id": "gh-01-zone-fruit-d",
            "state_summary": "과실 하중이 올라간 GT Master line에서 dawn WC 저하와 과도한 night dry-back 뒤 오후 잎 처짐 메모가 다시 붙는다.",
            "active_constraints": ["gt_master_dryback_watch", "line_variability_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 하중 구간 GT Master line의 dawn WC 저하와 반복 잎 처짐은 high rootzone stress로 본다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중이 올라간 구간에서 dawn WC 저하와 night dry-back 재발은 rootzone 불균형 가능성이 높다.",
                "이때는 create_alert와 현장 확인이 recipe 조정보다 앞선다.",
            ],
            "recommended_actions": [
                action(
                    "state18-328",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-d",
                    "high",
                    "과실 하중 구간의 rootzone stress 재발과 잎 처짐 위험을 즉시 공유한다.",
                    "운영자가 현장 확인과 기록을 우선 시작할 수 있다.",
                    10,
                ),
                action(
                    "state18-328",
                    2,
                    "request_human_check",
                    "operator",
                    "crop-manager",
                    "medium",
                    "대표 line의 dawn WC, dry-back, 잎 처짐 메모를 다시 확인한다.",
                    "자동 급액 조정 전 실제 stress 원인을 다시 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "line 편차와 rootzone stress 확인 전 recipe 조정은 오판을 키울 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 line의 dawn WC와 잎 처짐 재발 시점을 다시 확인한다.")
            ],
            "confidence": 0.83,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


ROBOT_ROWS = [
    {
        "sample_id": "robot-task-105",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-d",
            "state_summary": "수확 hotspot은 보이지만 maturity confidence가 낮아 재촬영과 근접 확인이 먼저 필요하다.",
            "candidates": [{"candidate_id": "hotspot-41", "ripeness_score": 0.58, "reachable": True, "vision_confidence": 0.39}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "낮은 confidence hotspot은 generic manual_review가 아니라 inspect_crop으로 다시 확인해야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                {
                    "task_type": "inspect_crop",
                    "candidate_id": "hotspot-41",
                    "target": {"target_type": "candidate", "target_id": "hotspot-41"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "maturity confidence가 낮아 재촬영과 근접 확인이 먼저 필요하다.",
                }
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("visual_inspection", 15, "hotspot-41의 실제 성숙도와 병반 여부를 다시 확인한다.")
            ],
            "confidence": 0.79,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "robot-task-106",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-e",
            "state_summary": "fruit hotspot은 탐지됐지만 confidence가 낮고 시야 가림이 있어 근접 inspect가 먼저 필요하다.",
            "candidates": [{"candidate_id": "hotspot-42", "ripeness_score": 0.6, "reachable": True, "vision_confidence": 0.35}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "시야 가림으로 confidence가 낮은 hotspot은 inspect_crop으로 보내고 수확 판단은 보류해야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                {
                    "task_type": "inspect_crop",
                    "candidate_id": "hotspot-42",
                    "target": {"target_type": "candidate", "target_id": "hotspot-42"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "시야 가림 때문에 maturity confidence가 낮아 근접 inspect가 먼저다.",
                }
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("visual_inspection", 15, "hotspot-42의 실제 성숙도와 가림 원인을 다시 확인한다.")
            ],
            "confidence": 0.78,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
]


def main() -> None:
    write_jsonl(ACTION_OUTPUT, ACTION_ROWS)
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ROBOT_OUTPUT, ROBOT_ROWS)
    print(f"action_rows: {len(ACTION_ROWS)}")
    print(f"state_rows: {len(STATE_ROWS)}")
    print(f"robot_rows: {len(ROBOT_ROWS)}")
    print(f"total_rows: {len(ACTION_ROWS) + len(STATE_ROWS) + len(ROBOT_ROWS)}")


if __name__ == "__main__":
    main()
