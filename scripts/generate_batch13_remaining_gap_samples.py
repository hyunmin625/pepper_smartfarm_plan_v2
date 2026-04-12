#!/usr/bin/env python3
"""Generate targeted samples for the final two blind holdout semantic gaps."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def action_recommendation_rows() -> list[dict]:
    return [
        {
            "sample_id": "action-rec-026",
            "task_type": "action_recommendation",
            "input": {
                "farm_id": "demo-farm",
                "zone_id": "gh-01-zone-b",
                "growth_stage": "fruit_expansion",
                "state_summary": "Grodan GT Master 슬래브에서 야간 dry-back이 12.8%까지 커졌고 새벽 WC가 49%까지 내려간 뒤 오후 잎 처짐 메모가 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "GT Master 슬래브의 과도한 야간 dry-back과 낮은 새벽 WC, 반복 잎 처짐은 실제 근권 스트레스 가능성이 높아 현장 확인을 우선해야 한다.",
                "risk_level": "high",
                "diagnosis": [
                    "과도한 야간 dry-back과 낮은 새벽 WC가 함께 나타나면 낮 시간 회복 지연과 반복 잎 처짐으로 이어질 수 있다.",
                    "이 단계에서는 배액, dripper, 뿌리 상태 확인 없이 자동 급액이나 레시피 조정을 바로 걸면 원인을 오판할 수 있다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "act-052",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-b"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "GT Master 근권 건조 스트레스 가능성을 즉시 기록해 운영자가 대응을 시작하게 한다.",
                        "expected_effect": "반복 잎 처짐과 근권 건조 위험을 놓치지 않고 현장 점검을 시작할 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "act-053",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "rootzone-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "새벽 WC, dripper 균일도, 배액 반응, 실제 잎 처짐 시간을 현장에서 함께 확인한다.",
                        "expected_effect": "건조 스트레스와 단순 급액 세팅 문제를 구분할 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "skipped_actions": [
                    {
                        "action_type": "short_irrigation",
                        "reason": "현장 확인 없이 추가 관수 펄스를 바로 실행하면 dripper 편차와 근권 통기 저하를 함께 놓칠 수 있다.",
                    },
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "근권 건조 원인이 배액/관수 균일도인지 recipe 문제인지 확인되기 전에는 자동 recipe 조정을 바로 걸면 안 된다.",
                    },
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 20,
                        "description": "대표 slab의 새벽 WC, 배액 반응, 오후 잎 처짐 시점을 다시 확인한다.",
                    }
                ],
                "confidence": 0.8,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                    {"chunk_id": "pepper-hydroponic-001", "document_id": "RAG-SRC-003"},
                ],
            },
        },
        {
            "sample_id": "action-rec-027",
            "task_type": "action_recommendation",
            "input": {
                "farm_id": "demo-farm",
                "zone_id": "gh-01-zone-c",
                "growth_stage": "fruit_expansion",
                "state_summary": "GT Master 대표 라인에서 새벽 WC가 48%까지 떨어지고 dry-back이 13%를 넘은 날마다 오후 과실 하중 구간 잎 처짐 메모가 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "fruit_load_rootzone_watch"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "과실 하중이 있는 GT Master 라인에서 dry-back 과다와 낮은 새벽 WC가 반복되면 근권 스트레스 위험이 높아 경고와 현장 확인이 먼저다.",
                "risk_level": "high",
                "diagnosis": [
                    "과실 하중 구간의 낮은 새벽 WC는 낮 시간 수분 회복 지연과 잎 처짐을 키울 수 있다.",
                    "근권 상태와 관수 균일도를 보지 않고 급액 조건을 먼저 바꾸면 원인 분리가 더 어려워진다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "act-054",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-c"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "과실 하중 구간의 근권 건조 스트레스 위험을 운영자에게 즉시 알린다.",
                        "expected_effect": "반복되는 잎 처짐 패턴을 빠르게 공유하고 대응 우선순위를 올릴 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "act-055",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "duty-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "대표 slab 수동 측정, dripper 막힘 여부, 배액 회복을 현장에서 함께 확인한다.",
                        "expected_effect": "실제 건조 스트레스와 급액 균일도 문제를 구분할 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "새벽 WC 저하만으로 recipe 변경을 자동 승인하면 근권·배액 문제를 잘못 덮을 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "trend_review",
                        "due_in_minutes": 30,
                        "description": "새벽 WC, dry-back, 오후 잎 처짐 메모가 같은 라인에서 반복되는지 다시 확인한다.",
                    }
                ],
                "confidence": 0.79,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                    {"chunk_id": "pepper-hydroponic-001", "document_id": "RAG-SRC-003"},
                ],
            },
        },
    ]


def state_rows() -> list[dict]:
    return [
        {
            "sample_id": "state-judgement-104",
            "task_type": "rootzone_diagnosis",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruit_expansion",
                "zone_id": "gh-01-zone-b",
                "state_summary": "Grodan GT Master 슬래브의 야간 dry-back이 13%까지 커졌고 새벽 WC가 49%로 내려간 뒤 오후 잎 처짐이 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "GT Master 슬래브에서 과도한 dry-back과 낮은 새벽 WC가 반복되면 실제 근권 스트레스 위험이 높다.",
                "risk_level": "high",
                "diagnosis": [
                    "과도한 야간 dry-back은 새벽 회복 지연과 오후 잎 처짐으로 이어질 수 있다.",
                    "지금은 추가 급액보다 slab별 편차와 뿌리 활력을 먼저 확인해야 한다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "state13-104-act-001",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-b"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "근권 건조 스트레스 고위험 상황을 즉시 기록한다.",
                        "expected_effect": "현장 점검 우선순위를 빠르게 높일 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "state13-104-act-002",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "rootzone-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "대표 slab 수동 측정, dripper 균일도, 배액 회복을 현장에서 확인한다.",
                        "expected_effect": "실제 근권 스트레스와 관수 균일도 문제를 구분할 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "skipped_actions": [
                    {
                        "action_type": "short_irrigation",
                        "reason": "원인 확인 없이 추가 관수 펄스를 걸면 line 편차와 배지 통기 저하를 함께 놓칠 수 있다.",
                    },
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "근권 스트레스 원인이 recipe가 아닐 수 있어 자동 recipe 변경을 먼저 걸면 안 된다.",
                    },
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 20,
                        "description": "대표 slab 수동 측정과 오후 잎 처짐 시간대를 다시 확인한다.",
                    }
                ],
                "confidence": 0.8,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                    {"chunk_id": "pepper-hydroponic-001", "document_id": "RAG-SRC-003"},
                ],
            },
        },
        {
            "sample_id": "state-judgement-105",
            "task_type": "rootzone_diagnosis",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruit_set",
                "zone_id": "gh-01-zone-c",
                "state_summary": "GT Master 과실 하중 라인에서 새벽 WC가 50% 아래로 유지되고 야간 dry-back이 커진 날마다 낮 시간 잎 처짐 메모가 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "fruit_load_rootzone_watch"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-crop-env-thresholds-001"],
            },
            "preferred_output": {
                "situation_summary": "과실 하중 라인의 과도한 dry-back과 낮은 새벽 WC 반복은 근권 스트레스 고위험 신호다.",
                "risk_level": "high",
                "diagnosis": [
                    "과실 하중 구간은 새벽 회복이 늦어지면 낮 시간 잎 처짐으로 바로 드러날 수 있다.",
                    "자동 관수나 recipe 변경보다 대표 라인의 배액 반응과 dripper 균일도 확인이 우선이다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "state13-105-act-001",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-c"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "과실 하중 라인의 근권 스트레스 위험을 즉시 알린다.",
                        "expected_effect": "반복 잎 처짐 패턴에 대한 대응 우선순위를 빠르게 높일 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "state13-105-act-002",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "duty-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "대표 라인의 실제 배지 상태, 배액 반응, 관수 균일도를 함께 확인한다.",
                        "expected_effect": "dry-back 과다와 line 편차를 구분할 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "trend_review",
                        "due_in_minutes": 30,
                        "description": "새벽 WC와 낮 시간 잎 처짐 메모가 같은 라인에서 반복되는지 다시 비교한다.",
                    }
                ],
                "confidence": 0.78,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                    {"chunk_id": "pepper-crop-env-thresholds-001", "document_id": "RAG-SRC-001"},
                ],
            },
        },
        {
            "sample_id": "state-judgement-106",
            "task_type": "climate_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "nursery",
                "zone_id": "gh-01-zone-nursery",
                "state_summary": "Grodan Delta 6.5 육묘 블록 구간에서 해진 뒤 보온은 유지되지만 상대습도가 높고 잎 젖음 시간이 늘고 있다.",
                "active_constraints": ["delta65_nursery_leaf_wet_watch", "night_heat_retention_mode"],
                "retrieved_context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "Delta 6.5 육묘 구간의 해진 뒤 냉습 조건과 잎 젖음 시간 증가는 활착 지연과 병해 위험을 동시에 높인다.",
                "risk_level": "high",
                "diagnosis": [
                    "육묘기에는 보온이 유지돼도 높은 습도와 긴 잎 젖음 시간이 병해와 활착 지연 위험을 키울 수 있다.",
                    "이 상황에서 야간 환기를 바로 열면 온도 유지가 무너질 수 있어 먼저 경고와 현장 확인이 필요하다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "state13-106-act-001",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-nursery"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "육묘 냉습·잎 젖음 복합 위험을 즉시 기록한다.",
                        "expected_effect": "육묘 활착 지연과 병해 리스크를 빠르게 인지할 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "state13-106-act-002",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "nursery-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "실제 잎 젖음 시간, 육묘 활착 상태, 난방·보온 커튼 상태를 현장에서 함께 확인한다.",
                        "expected_effect": "냉습 리스크와 야간 보온 상태를 현장 기준으로 구분할 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_vent",
                        "reason": "해진 뒤 육묘 구간에서 환기를 바로 열면 온도 유지가 무너져 활착 지연이 더 커질 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 20,
                        "description": "대표 블록의 잎 젖음 시간과 난방·보온 커튼 상태를 다시 확인한다.",
                    }
                ],
                "confidence": 0.79,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-plantfactory-healing-001", "document_id": "RAG-SRC-001"},
                    {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                ],
            },
        },
        {
            "sample_id": "state-judgement-107",
            "task_type": "climate_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "nursery",
                "zone_id": "gh-01-zone-nursery",
                "state_summary": "Grodan Delta 6.5 육묘 블록에서 해진 뒤 습도는 높고 미세한 결로 메모와 잎 젖음 지속 시간이 함께 늘고 있다.",
                "active_constraints": ["delta65_nursery_leaf_wet_watch", "night_condensation_watch"],
                "retrieved_context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "해진 뒤 육묘 블록의 고습·결로 징후와 긴 잎 젖음 시간은 활착과 병해에 모두 높은 부담이다.",
                "risk_level": "high",
                "diagnosis": [
                    "육묘기 냉습 조건이 길어지면 잎 젖음 시간이 길어져 병해와 활착 지연 위험이 동시에 커진다.",
                    "보온 유지가 필요한 시점이어서 자동 환기보다 현장 확인과 보수적 대응이 우선이다.",
                ],
                "recommended_actions": [
                    {
                        "action_id": "state13-107-act-001",
                        "action_type": "create_alert",
                        "target": {"target_type": "zone", "target_id": "gh-01-zone-nursery"},
                        "risk_level": "high",
                        "approval_required": False,
                        "reason": "육묘 냉습·결로 복합 위험을 즉시 알린다.",
                        "expected_effect": "야간 육묘 관리 우선순위를 빠르게 높일 수 있다.",
                        "cooldown_minutes": 10,
                    },
                    {
                        "action_id": "state13-107-act-002",
                        "action_type": "request_human_check",
                        "target": {"target_type": "operator", "target_id": "nursery-manager"},
                        "risk_level": "medium",
                        "approval_required": False,
                        "reason": "실제 결로, 잎 젖음 시간, block 활착 상태를 현장에서 함께 확인한다.",
                        "expected_effect": "야간 보온과 냉습 위험의 균형을 현장 기준으로 맞출 수 있다.",
                        "cooldown_minutes": 0,
                    },
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_vent",
                        "reason": "해진 뒤 육묘 구간에서 환기 우선 대응을 자동 실행하면 보온 밴드를 깨뜨릴 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 15,
                        "description": "결로 위치와 잎 젖음 지속 시간, 보온 커튼 상태를 다시 확인한다.",
                    }
                ],
                "confidence": 0.8,
                "retrieval_coverage": "sufficient",
                "citations": [
                    {"chunk_id": "pepper-plantfactory-healing-001", "document_id": "RAG-SRC-001"},
                    {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                ],
            },
        },
    ]


def forbidden_rows() -> list[dict]:
    return [
        {
            "sample_id": "forbidden-action-025",
            "task_type": "forbidden_action",
            "input": {
                "growth_stage": "fruit_expansion",
                "proposed_action": "adjust_fertigation",
                "state_summary": "Grodan GT Master 슬래브의 야간 dry-back이 과도하고 새벽 WC가 낮아 오후 잎 처짐이 반복되지만 dripper 균일도와 현장 상태 확인은 아직 없다.",
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "decision": "approval_required",
                "risk_level": "high",
                "blocked_action_type": "adjust_fertigation",
                "reason": "GT Master dry-back 과다와 잎 처짐만으로는 recipe 변경이 정답인지 확정할 수 없어 승인과 현장 확인이 먼저다.",
                "required_follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 20,
                        "description": "대표 slab 수동 측정, dripper 균일도, 배액 반응을 확인한 뒤 recipe 조정 필요성을 판단한다.",
                    }
                ],
                "citations": [
                    {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                    {"chunk_id": "pepper-hydroponic-001", "document_id": "RAG-SRC-003"},
                ],
            },
        },
        {
            "sample_id": "forbidden-action-026",
            "task_type": "forbidden_action",
            "input": {
                "growth_stage": "nursery",
                "proposed_action": "adjust_vent",
                "state_summary": "Grodan Delta 6.5 육묘 블록 구간에서 해진 뒤 습도와 잎 젖음 시간이 함께 높아졌지만 보온 유지가 필요한 시간대다.",
                "retrieved_context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "decision": "block",
                "risk_level": "high",
                "blocked_action_type": "adjust_vent",
                "reason": "해진 뒤 육묘 구간에서 자동 환기를 바로 열면 보온이 무너져 활착 지연을 키울 수 있어 경고와 현장 확인이 먼저다.",
                "required_follow_up": [
                    {
                        "check_type": "visual_inspection",
                        "due_in_minutes": 15,
                        "description": "잎 젖음 시간, 결로 위치, 난방·보온 커튼 상태를 확인한 뒤 수동 조정 여부를 판단한다.",
                    }
                ],
                "citations": [
                    {"chunk_id": "pepper-plantfactory-healing-001", "document_id": "RAG-SRC-001"},
                    {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                ],
            },
        },
    ]


def main() -> None:
    outputs = {
        ROOT / "data/examples/action_recommendation_samples_batch9.jsonl": action_recommendation_rows(),
        ROOT / "data/examples/state_judgement_samples_batch13.jsonl": state_rows(),
        ROOT / "data/examples/forbidden_action_samples_batch6.jsonl": forbidden_rows(),
    }

    total_rows = 0
    for path, rows in outputs.items():
        write_jsonl(path, rows)
        total_rows += len(rows)
        print(f"wrote {len(rows)} rows -> {path.relative_to(ROOT)}")
    print(f"total_rows: {total_rows}")


if __name__ == "__main__":
    main()
