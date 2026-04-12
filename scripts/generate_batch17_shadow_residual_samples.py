#!/usr/bin/env python3
"""Generate batch17 samples for the remaining offline shadow residual drifts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch11_shadow_residual.jsonl"
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch17_shadow_residual.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data/examples/robot_task_samples_batch6_shadow_residual.jsonl"

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
        "sample_id": "action-rec-031",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-a",
            "growth_stage": "fruit_set",
            "state_summary": "과실 하중이 올라간 GT Master 라인에서 새벽 WC가 48%까지 내려가고 dry-back이 커진 다음 낮 시간 잎 처짐 메모가 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "과실 하중 구간 GT Master 라인의 낮은 새벽 WC와 과도한 dry-back, 반복 잎 처짐은 현장 점검이 먼저 필요한 high rootzone stress 신호다.",
            "risk_level": "high",
            "diagnosis": [
                "과실 하중이 큰 시기에는 새벽 회복 부족과 과도한 dry-back이 반복되면 낮 시간 잎 처짐으로 바로 이어질 수 있다.",
                "이 상태에서는 recipe 변경보다 경고와 현장 확인이 먼저라 adjust_fertigation을 reflex처럼 내면 안 된다.",
            ],
            "recommended_actions": [
                action(
                    "action11-031",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-a",
                    "high",
                    "GT Master 근권 스트레스 고위험과 반복 잎 처짐 사실을 즉시 공유한다.",
                    "운영자가 rootzone stress 대응을 우선순위로 올릴 수 있다.",
                    10,
                ),
                action(
                    "action11-031",
                    2,
                    "request_human_check",
                    "operator",
                    "rootzone-manager",
                    "medium",
                    "대표 slab의 새벽 WC, 배액 반응, dripper 균일도와 오후 잎 처짐 시점을 현장에서 다시 확인한다.",
                    "recipe 조정 전 실제 rootzone stress 여부를 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "새벽 WC 저하와 dry-back만으로는 recipe 변경이 정답인지 확정할 수 없어 현장 확인 전 자동 급액 조정은 금지한다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab와 인접 라인의 새벽 WC, 배액률, 잎 처짐 시점을 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-crop-env-thresholds-001")],
        },
    },
    {
        "sample_id": "action-rec-032",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-b",
            "growth_stage": "fruit_expansion",
            "state_summary": "GT Master 과실 라인에서 고온일 다음날 새벽 WC가 낮고 night dry-back이 과도했던 구간만 오전 말부터 잎 처짐이 다시 보인다.",
            "active_constraints": ["gt_master_dryback_watch", "line_variability_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "GT Master line-specific dry-back 과다와 낮은 새벽 WC 재발은 high rootzone stress로 보고 경고와 현장 확인을 먼저 해야 한다.",
            "risk_level": "high",
            "diagnosis": [
                "고온일 다음날 새벽 회복 부족이 line별로 반복되면 관수 recipe 자체보다 line 편차와 배액 반응을 먼저 봐야 한다.",
                "이때 adjust_fertigation을 먼저 내면 원인 확인 전에 recipe만 흔들 수 있다.",
            ],
            "recommended_actions": [
                action(
                    "action11-032",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-b",
                    "high",
                    "line-specific rootzone stress 재발과 잎 처짐 위험을 경고한다.",
                    "운영자가 현장 확인을 우선 시작할 수 있다.",
                    10,
                ),
                action(
                    "action11-032",
                    2,
                    "request_human_check",
                    "operator",
                    "crop-manager",
                    "medium",
                    "대표 line의 새벽 WC, drain fraction, dripper 편차를 현장에서 다시 확인한다.",
                    "line 편차와 실제 rootzone stress를 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "line 편차와 배액 반응 확인 전 recipe 조정을 먼저 걸면 고위험 구간을 더 흔들 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 line의 새벽 WC와 잎 처짐 재발 시점을 다시 확인한다.")
            ],
            "confidence": 0.83,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
]


STATE_ROWS = [
    {
        "sample_id": "state-judgement-321",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-a",
            "state_summary": "GT Master 슬래브에서 급액 EC 2.7 대비 배액 EC 5.4가 반복되고 배액률은 13%로 낮다.",
            "active_constraints": ["salt_accumulation_watch", "low_drain_fraction_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "급액 대비 배액 EC 차이가 크게 벌어지고 배액률이 낮아 염류 집적과 근권 스트레스 위험이 높다.",
            "risk_level": "high",
            "diagnosis": [
                "배액 EC가 급액보다 크게 높고 낮은 배액률이 반복되면 GT Master slab 내 염류 집적 가능성이 높다.",
                "이 시점에서는 adjust_fertigation을 먼저 확정하기보다 경고와 현장 점검으로 원인을 다시 확인해야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state17-321",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-a",
                    "high",
                    "염류 집적과 낮은 배액률이 겹친 고위험 nutrient risk를 즉시 알린다.",
                    "운영자가 flush 필요성과 현장 점검을 우선순위로 올릴 수 있다.",
                    10,
                ),
                action(
                    "state17-321",
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
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "현장 점검 전 recipe를 바로 바꾸면 line 편차와 mixing 문제를 놓칠 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "대표 slab의 급액 EC, 배액 EC, 배액률 추세를 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-322",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-b",
            "state_summary": "GT Master 구역에서 drain EC 5.1이 누적되고 flush window는 지났지만 배액률은 12%에 머문다.",
            "active_constraints": ["salt_accumulation_watch", "flush_window_missed"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "flush 시점을 놓친 상태에서 drain EC 누적과 낮은 배액률이 겹쳐 nutrient risk가 high다.",
            "risk_level": "high",
            "diagnosis": [
                "flush window를 놓친 뒤 drain EC가 누적되고 배액률이 낮으면 rootzone salt stress가 빠르게 커질 수 있다.",
                "이 경우에도 recipe 변경을 reflex로 확정하기보다 먼저 경고와 현장 확인으로 실제 line 상태를 다시 봐야 한다.",
            ],
            "recommended_actions": [
                action(
                    "state17-322",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-b",
                    "high",
                    "flush window miss와 drain EC 누적 사실을 즉시 경고한다.",
                    "운영자가 nutrient risk 대응을 늦추지 않게 한다.",
                    10,
                ),
                action(
                    "state17-322",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 slab 배액 상태와 mixing 로그를 다시 확인한다.",
                    "line별 편차와 실제 flush 필요성을 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "flush 누락과 line 편차를 먼저 확인하지 않으면 recipe 변경이 과교정으로 이어질 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("trend_review", 20, "flush 직전·직후 배액 EC와 배액률 추세를 다시 본다.")
            ],
            "confidence": 0.83,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-rootzone-001")],
        },
    },
    {
        "sample_id": "state-judgement-323",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_expansion",
            "zone_id": "gh-01-zone-fruit-a",
            "state_summary": "GT Master 슬래브의 새벽 WC가 47%로 낮고 야간 dry-back이 과도한 날마다 오후 잎 처짐 메모가 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "낮은 새벽 WC와 과도한 dry-back, 반복 잎 처짐은 GT Master rootzone stress high 신호다.",
            "risk_level": "high",
            "diagnosis": [
                "새벽 WC 저하와 반복 dry-back 과다는 낮 시간 회복 지연과 잎 처짐으로 연결되는 대표적인 rootzone stress 패턴이다.",
                "이때는 recipe 조정보다 경고와 현장 확인을 먼저 두어야 하며 adjust_fertigation을 바로 걸면 안 된다.",
            ],
            "recommended_actions": [
                action(
                    "state17-323",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-a",
                    "high",
                    "반복되는 GT Master rootzone stress 신호를 즉시 공유한다.",
                    "운영자가 slab 점검과 대응을 우선 시작할 수 있다.",
                    10,
                ),
                action(
                    "state17-323",
                    2,
                    "request_human_check",
                    "operator",
                    "rootzone-manager",
                    "medium",
                    "대표 slab의 dawn WC, drain response, dripper 균일도와 잎 처짐 시점을 다시 확인한다.",
                    "실제 rootzone stress와 line 편차를 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "현장 evidence를 확인하기 전 recipe를 바꾸면 stress 원인을 더 흐릴 수 있다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab의 새벽 WC와 오후 잎 처짐 재발 시점을 다시 확인한다.")
            ],
            "confidence": 0.84,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-324",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruit_set",
            "zone_id": "gh-01-zone-fruit-c",
            "state_summary": "GT Master line에서 dawn WC 저하와 큰 night dry-back이 이어진 뒤 오후 잎 처짐이 며칠째 같은 구간에서만 반복된다.",
            "active_constraints": ["gt_master_dryback_watch", "line_variability_watch"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
        },
        "preferred_output": {
            "situation_summary": "같은 GT Master line에서만 반복되는 dawn WC 저하와 잎 처짐은 high rootzone stress로 보고 현장 점검을 먼저 해야 한다.",
            "risk_level": "high",
            "diagnosis": [
                "동일 line에서만 dawn WC 저하와 잎 처짐이 반복되면 recipe 전체보다 line 상태와 배액 반응을 먼저 봐야 한다.",
                "이 상황에서 adjust_fertigation을 먼저 내면 국소 문제를 전체 recipe 문제로 오판할 수 있다.",
            ],
            "recommended_actions": [
                action(
                    "state17-324",
                    1,
                    "create_alert",
                    "zone",
                    "gh-01-zone-fruit-c",
                    "high",
                    "line-specific rootzone stress 반복 사실을 즉시 경고한다.",
                    "운영자가 line 점검을 우선 실행할 수 있다.",
                    10,
                ),
                action(
                    "state17-324",
                    2,
                    "request_human_check",
                    "operator",
                    "rootzone-manager",
                    "medium",
                    "대표 line의 drain 반응과 dripper 편차를 현장에서 다시 확인한다.",
                    "국소 stress와 배관 편차를 구분할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "국소 line 문제를 recipe 전체 문제로 잘못 읽지 않도록 현장 확인이 먼저다.",
                }
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [
                follow_up("visual_inspection", 20, "문제 line의 새벽 WC, 배액률, 잎 처짐 위치를 다시 확인한다.")
            ],
            "confidence": 0.82,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-crop-env-thresholds-001")],
        },
    },
]


ROBOT_ROWS = [
    {
        "sample_id": "robot-task-103",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-a",
            "state_summary": "과실 hotspot은 보이지만 성숙도 confidence가 낮아 근접 재촬영이 먼저 필요하다.",
            "candidates": [{"candidate_id": "hotspot-31", "ripeness_score": 0.61, "reachable": True, "vision_confidence": 0.42}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "낮은 confidence hotspot은 generic task가 아니라 inspect_crop으로 다시 확인해야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                {
                    "task_type": "inspect_crop",
                    "candidate_id": "hotspot-31",
                    "target": {"target_type": "candidate", "target_id": "hotspot-31"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "성숙도 confidence가 낮아 재촬영과 근접 확인이 먼저 필요하다.",
                }
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [follow_up("visual_inspection", 15, "hotspot-31의 실제 성숙도와 병반 여부를 다시 확인한다.")],
            "confidence": 0.78,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "robot-task-104",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-harvest-b",
            "state_summary": "수확 후보 hotspot이 감지됐지만 시야 가림이 있어 maturity confidence가 낮고 재촬영이 먼저 필요하다.",
            "candidates": [{"candidate_id": "hotspot-32", "ripeness_score": 0.57, "reachable": True, "vision_confidence": 0.37}],
            "safety_context": {"worker_present": False, "robot_zone_clear": True},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "시야 가림으로 confidence가 낮은 수확 후보는 inspect_crop으로 보내야 한다.",
            "risk_level": "medium",
            "robot_tasks": [
                {
                    "task_type": "inspect_crop",
                    "candidate_id": "hotspot-32",
                    "target": {"target_type": "candidate", "target_id": "hotspot-32"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "가림 때문에 maturity confidence가 낮아 재촬영과 근접 확인이 우선이다.",
                }
            ],
            "skipped_candidates": [],
            "requires_human_approval": True,
            "follow_up": [follow_up("visual_inspection", 15, "hotspot-32의 실제 성숙도와 가림 원인을 다시 확인한다.")],
            "confidence": 0.77,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
        },
    },
]


def main() -> None:
    write_jsonl(ACTION_OUTPUT, ACTION_ROWS)
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ROBOT_OUTPUT, ROBOT_ROWS)
    print(f"action_rows={len(ACTION_ROWS)} output={ACTION_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"state_rows={len(STATE_ROWS)} output={STATE_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"robot_rows={len(ROBOT_ROWS)} output={ROBOT_OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
