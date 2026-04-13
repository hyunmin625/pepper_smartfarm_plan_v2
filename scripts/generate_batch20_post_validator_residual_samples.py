#!/usr/bin/env python3
"""Generate batch20 corrective samples from ds_v14 blind50 post-validator residuals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch20_post_validator_residual.jsonl"
STATE_OUTPUT = REPO_ROOT / "data/examples/state_judgement_samples_batch20_post_validator_residual.jsonl"
ROBOT_OUTPUT = REPO_ROOT / "data/examples/robot_task_samples_batch20_post_validator_residual.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-hydroponic-001": "RAG-SRC-003",
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


ACTION_ROWS = [
    {
        "sample_id": "action-recommendation-701",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gt-master-zone",
            "growth_stage": "fruit_set",
            "state_summary": "흐리고 서늘한 날 GT Master 구역에서 CO2가 낮고 보온커튼이 부분 폐쇄된 채 환기는 최소로 유지되고 있다.",
            "active_constraints": ["low_light_cool_day", "co2_under_target", "shade_partially_closed"],
            "retrieved_context": ["pepper-climate-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "저광·저온 조건에서 CO2 부족이 있어도 환기를 먼저 열기보다 사람 확인을 포함한 보수적 대응이 우선이다.",
            "risk_level": "medium",
            "diagnosis": [
                "흐리고 서늘한 조건에서는 환기를 늘리면 보온이 깨질 수 있어 request_human_check 없이 장치 제어만 바로 내면 안 된다.",
                "CO2 보충은 허용될 수 있지만 현장 상태와 커튼·환기 상태를 함께 확인해야 한다."
            ],
            "recommended_actions": [
                action(
                    "action20-701",
                    1,
                    "request_human_check",
                    "operator",
                    "climate-manager",
                    "medium",
                    "CO2 최근값, 보온커튼 상태, 환기 run 상태를 함께 확인한다.",
                    "저광·저온 조건에서 잘못된 환기/가온 판단을 줄일 수 있다.",
                    0,
                ),
                action(
                    "action20-701",
                    2,
                    "adjust_co2",
                    "zone",
                    "gt-master-zone",
                    "medium",
                    "저광 조건에서도 CO2 부족이 지속되면 제한적 보충을 검토한다.",
                    "광합성 저하를 일부 완화하되 현장 확인 후에만 적용할 수 있다.",
                    20,
                    approval_required=True,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_vent",
                    "reason": "저광·저온 구간에서 환기를 reflex처럼 여는 것은 보온 손실을 키울 수 있다.",
                }
            ],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("operator_confirm", 10, "CO2 센서, 보온커튼, 최소 환기 상태를 다시 확인한다.")
            ],
            "confidence": 0.72,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-climate-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "action-recommendation-702",
        "task_type": "action_recommendation",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruit_expansion",
            "state_summary": "배액 pH와 drain volume 기록이 비어 있는데 recipe 조정 권고가 올라왔다.",
            "active_constraints": ["drain_ph_missing", "drain_volume_missing", "recipe_change_pending"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "배액 근거가 비어 있는 상태에서는 recipe 조정을 자동으로 진행하지 말고 근거 복구를 먼저 해야 한다.",
            "risk_level": "unknown",
            "diagnosis": [
                "drain pH와 drain volume 기록이 동시에 비면 현재 양액 상태를 정상 위험도로 단정할 수 없다.",
                "이 경우 risk_level은 high가 아니라 unknown으로 올리고 pause_automation과 request_human_check를 우선해야 한다."
            ],
            "recommended_actions": [
                action(
                    "action20-702",
                    1,
                    "pause_automation",
                    "system",
                    "gh-01-zone-fruit-fertigation-auto-control",
                    "unknown",
                    "배액 근거가 복구될 때까지 자동 recipe 조정을 보류한다.",
                    "근거 없는 양액 조정이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    "action20-702",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "unknown",
                    "배액 pH와 drain volume 수동 측정값을 확인하고 기록 누락 원인을 점검한다.",
                    "근거 복구 후에만 recipe 조정을 다시 검토할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "배액 근거가 비어 있으면 자동 recipe 조정은 허용하면 안 된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("sensor_recheck", 10, "배액 pH와 drain volume 수동 측정값, 기록 누락 원인을 확인한다.")
            ],
            "confidence": 0.7,
            "retrieval_coverage": "partial",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-agent-001")],
        },
    },
]


STATE_ROWS = [
    {
        "sample_id": "state-judgement-701",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruit_set",
            "state_summary": "Grodan GT Master 슬래브에서 야간 dry-back이 3%에 그쳤고 새벽 WC가 77%로 높게 남아 하부 통기 저하가 우려된다.",
            "active_constraints": ["gt_master_overnight_dryback_too_small", "high_dawn_wc"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "야간 dry-back 부족과 높은 새벽 WC는 과습/통기 저하 방향의 medium 위험 신호다.",
            "risk_level": "medium",
            "diagnosis": [
                "GT Master에서 야간 dry-back이 너무 작고 dawn WC가 높게 남는다면 통기 저하와 과습 가능성을 먼저 확인해야 한다.",
                "이 slice는 high로 과승격하기보다 medium으로 두고 request_human_check를 우선하는 편이 제품 기준과 맞는다."
            ],
            "recommended_actions": [
                action(
                    "state20-701",
                    1,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 slab의 배액 회복, dawn WC, 실제 통기 상태를 현장에서 확인한다.",
                    "과습/통기 저하 여부를 수동 측정으로 교차 검증할 수 있다.",
                    0,
                )
            ],
            "skipped_actions": [
                {
                    "action_type": "short_irrigation",
                    "reason": "과습 방향 신호가 있는 상황에서 추가 관수를 reflex처럼 넣으면 안 된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 slab의 배액 회복과 통기 상태를 다시 확인한다.")
            ],
            "confidence": 0.74,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-702",
        "task_type": "rootzone_diagnosis",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-b",
            "growth_stage": "fruit_set",
            "state_summary": "Grodan GT Master 2번 라인에서 야간 dry-back이 4%에 머물고 dawn WC가 76%로 높게 남아 배액 회복이 늦다.",
            "active_constraints": ["gt_master_overnight_dryback_too_small", "high_dawn_wc"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        },
        "preferred_output": {
            "situation_summary": "배액 회복이 늦고 dawn WC가 높은 GT Master 라인은 medium 위험으로 보고 현장 확인을 우선한다.",
            "risk_level": "medium",
            "diagnosis": [
                "근권 과습/통기 저하 방향 신호이지만 즉시 장치 제어를 바꾸기보다 실제 line 편차를 먼저 확인해야 한다.",
                "이 케이스도 high/create_alert reflex보다 medium/request_human_check가 더 적절하다."
            ],
            "recommended_actions": [
                action(
                    "state20-702",
                    1,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "medium",
                    "대표 line의 배액 회복, 산소 부족 징후, 실제 dawn WC를 다시 확인한다.",
                    "line 편차와 실제 통기 저하 여부를 구분할 수 있다.",
                    0,
                )
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "과습/통기 저하 여부가 확정되기 전에는 recipe 변경을 자동으로 걸면 안 된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("visual_inspection", 20, "대표 line의 배액 회복과 dawn WC를 다시 측정한다.")
            ],
            "confidence": 0.73,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
        },
    },
    {
        "sample_id": "state-judgement-703",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit",
            "growth_stage": "fruiting",
            "state_summary": "GT Master 구역에서 recipe 전환 직전 drain EC와 drain volume 기록이 동시에 비어 있다.",
            "active_constraints": ["drain_ec_missing", "drain_volume_missing", "recipe_shift_pending"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "recipe 전환 직전 drain 근거가 비어 있으면 nutrient risk를 unknown으로 올리고 자동 조정을 멈춰야 한다.",
            "risk_level": "unknown",
            "diagnosis": [
                "recipe 전환 직전 drain EC와 drain volume이 동시에 비면 현재 nutrient 상태를 신뢰할 수 없다.",
                "이 slice는 high/create_alert만 내는 대신 pause_automation과 request_human_check를 같이 내야 한다."
            ],
            "recommended_actions": [
                action(
                    "state20-703",
                    1,
                    "pause_automation",
                    "system",
                    "gh-01-zone-fruit-fertigation-auto-control",
                    "unknown",
                    "drain 근거가 복구될 때까지 자동 recipe 전환을 보류한다.",
                    "근거 없는 nutrient 조정이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    "state20-703",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "unknown",
                    "대표 slab의 drain EC와 drain volume을 수동 측정하고 기록 상태를 복구한다.",
                    "recipe 전환 전 nutrient 상태를 다시 확인할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "drain 근거가 비어 있으면 recipe 전환 전 자동 양액 조정은 허용하면 안 된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("lab_test", 20, "대표 slab의 drain EC와 drain volume을 수동 측정한다.")
            ],
            "confidence": 0.71,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "state-judgement-704",
        "task_type": "nutrient_risk",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-fruit-c",
            "growth_stage": "fruiting",
            "state_summary": "Grodan GT Master 3번 라인에서 recipe shift 직전 drain volume 기록이 비고 drain EC도 stale 상태다.",
            "active_constraints": ["drain_ec_stale", "drain_volume_missing", "recipe_shift_pending"],
            "retrieved_context": ["pepper-hydroponic-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "drain EC stale와 drain volume 공백이 겹치면 nutrient risk를 unknown으로 올리고 근거 복구를 먼저 해야 한다.",
            "risk_level": "unknown",
            "diagnosis": [
                "drain 근거가 비어 있거나 stale이면 recipe shift를 자동으로 진행할 수 없다.",
                "이 경우 create_alert만으로 끝내지 말고 pause_automation과 request_human_check를 같이 묶어야 한다."
            ],
            "recommended_actions": [
                action(
                    "state20-704",
                    1,
                    "pause_automation",
                    "system",
                    "gh-01-zone-fruit-c-fertigation-auto-control",
                    "unknown",
                    "drain 근거가 복구될 때까지 자동 recipe shift를 보류한다.",
                    "stale/missing 근거로 잘못된 양액 조정이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    "state20-704",
                    2,
                    "request_human_check",
                    "operator",
                    "fertigation-manager",
                    "unknown",
                    "drain EC 재측정과 drain volume 기록 복구를 현장에서 확인한다.",
                    "recipe shift 전 nutrient 근거를 다시 확보할 수 있다.",
                    0,
                ),
            ],
            "skipped_actions": [
                {
                    "action_type": "adjust_fertigation",
                    "reason": "drain EC stale와 drain volume 공백이 동시에 있으면 자동 양액 조정은 금지해야 한다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                follow_up("lab_test", 20, "drain EC 재측정과 drain volume 기록 복구 여부를 확인한다.")
            ],
            "confidence": 0.72,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-hydroponic-001"), citation("pepper-agent-001")],
        },
    },
]


ROBOT_ROWS = [
    {
        "sample_id": "robot-task-701",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-harvest-a",
            "growth_stage": "harvest",
            "state_summary": "aisle 바닥 젖음이 확인돼 수확 후보가 있어도 우회 지시가 먼저 필요하다.",
            "candidate_ids": ["candidate-001", "candidate-002"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "aisle 바닥 젖음이 남아 있으면 수확 후보가 있어도 skip_area가 먼저다.",
            "risk_level": "high",
            "robot_tasks": [
                robot_task(
                    "robot20-701",
                    1,
                    "skip_area",
                    "zone",
                    "gh-01-zone-harvest-a",
                    "high",
                    "젖은 통로는 미끄럼 위험이 있어 수확 후보보다 우회 지시가 먼저다.",
                    candidate_id="candidate-001",
                )
            ],
            "skipped_candidates": [
                {
                    "candidate_id": "candidate-002",
                    "reason": "통로 젖음이 해소되기 전에는 접근 우선순위를 올리면 안 된다.",
                }
            ],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("operator_confirm", 0, "통로 건조 여부와 접근 가능성을 확인한다.")
            ],
            "confidence": 0.7,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001")],
        },
    },
    {
        "sample_id": "robot-task-702",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-harvest-b",
            "growth_stage": "harvest",
            "state_summary": "harvest candidate는 있지만 aisle condensation으로 바닥이 젖어 우회 지시가 먼저 필요하다.",
            "candidate_ids": ["candidate-101"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "aisle condensation과 바닥 젖음이 있으면 harvest candidate보다 skip_area가 먼저다.",
            "risk_level": "high",
            "robot_tasks": [
                robot_task(
                    "robot20-702",
                    1,
                    "skip_area",
                    "zone",
                    "gh-01-zone-harvest-b",
                    "high",
                    "condensation으로 통로가 젖어 있어 우회 지시를 먼저 내려야 한다.",
                    candidate_id="candidate-101",
                )
            ],
            "requires_human_approval": True,
            "follow_up": [
                follow_up("operator_confirm", 0, "통로 미끄럼 위험 해소와 접근 가능 여부를 확인한다.")
            ],
            "confidence": 0.69,
            "retrieval_coverage": "sufficient",
            "citations": [citation("pepper-agent-001")],
        },
    },
]


def main() -> None:
    write_jsonl(ACTION_OUTPUT, ACTION_ROWS)
    write_jsonl(STATE_OUTPUT, STATE_ROWS)
    write_jsonl(ROBOT_OUTPUT, ROBOT_ROWS)
    print(
        json.dumps(
            {
                "action_output": str(ACTION_OUTPUT.relative_to(REPO_ROOT)),
                "state_output": str(STATE_OUTPUT.relative_to(REPO_ROOT)),
                "robot_output": str(ROBOT_OUTPUT.relative_to(REPO_ROOT)),
                "action_rows": len(ACTION_ROWS),
                "state_rows": len(STATE_ROWS),
                "robot_rows": len(ROBOT_ROWS),
                "total_rows": len(ACTION_ROWS) + len(STATE_ROWS) + len(ROBOT_ROWS),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
