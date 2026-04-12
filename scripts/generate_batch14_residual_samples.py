#!/usr/bin/env python3
"""Generate targeted batch14 samples for the remaining blind50 residual failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ACTION_OUTPUT = ROOT / "data" / "examples" / "action_recommendation_samples_batch10.jsonl"
STATE_OUTPUT = ROOT / "data" / "examples" / "state_judgement_samples_batch14.jsonl"
ROBOT_OUTPUT = ROOT / "data" / "examples" / "robot_task_samples_batch5.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-harvest-001": "RAG-SRC-001",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-pest-001": "RAG-SRC-001",
    "pepper-rootzone-001": "RAG-SRC-004",
}


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
    task_type: str,
    candidate_id: str,
    target_type: str,
    target_id: str,
    priority: str,
    reason: str,
    *,
    approval_required: bool = True,
) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "candidate_id": candidate_id,
        "target": {"target_type": target_type, "target_id": target_id},
        "priority": priority,
        "approval_required": approval_required,
        "reason": reason,
    }


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


def action_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_id": "action-rec-028",
            "task_type": "action_recommendation",
            "input": {
                "farm_id": "demo-farm",
                "zone_id": "gh-01-zone-b",
                "growth_stage": "fruit_expansion",
                "state_summary": "GT Master 슬래브의 야간 dry-back이 13%를 넘고 새벽 WC가 49%까지 내려간 날마다 오후 잎 처짐 메모가 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "GT Master 슬래브의 과도한 dry-back과 낮은 새벽 WC, 반복 잎 처짐은 근권 스트레스 고위험 신호다.",
                "risk_level": "high",
                "diagnosis": [
                    "과도한 야간 dry-back과 낮은 새벽 WC가 반복되면 낮 시간 회복 지연과 잎 처짐으로 이어질 수 있다.",
                    "이 상황에서는 short irrigation을 바로 넣기보다 현장 확인과 경고를 먼저 걸어야 원인 오판을 줄일 수 있다.",
                ],
                "recommended_actions": [
                    action(
                        "action10-028",
                        1,
                        "create_alert",
                        "zone",
                        "gh-01-zone-b",
                        "high",
                        "반복 잎 처짐과 GT Master 근권 건조 스트레스 고위험 상황을 즉시 공유한다.",
                        "운영자가 근권 건조 스트레스 대응을 우선순위로 올릴 수 있다.",
                        10,
                    ),
                    action(
                        "action10-028",
                        2,
                        "request_human_check",
                        "operator",
                        "rootzone-manager",
                        "medium",
                        "대표 slab의 새벽 WC, 배액 반응, dripper 균일도, 오후 잎 처짐 시점을 현장에서 다시 확인한다.",
                        "근권 건조와 관수 균일도 문제를 구분할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "short_irrigation",
                        "reason": "현재는 자동 보정 전에 원인 확인이 먼저라 추가 펄스를 바로 넣으면 안 된다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("visual_inspection", 20, "대표 slab와 인접 라인의 새벽 WC, 배액률, 오후 잎 처짐 시점을 다시 확인한다.")
                ],
                "confidence": 0.82,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
            },
        },
        {
            "sample_id": "action-rec-029",
            "task_type": "action_recommendation",
            "input": {
                "farm_id": "demo-farm",
                "zone_id": "nursery-zone-a",
                "growth_stage": "nursery",
                "state_summary": "해진 뒤 Delta 6.5 육묘 블록에서 높은 습도와 긴 잎 젖음 시간이 다시 관찰되고 보온은 유지 중이다.",
                "active_constraints": ["nursery_cold_humid_watch", "leaf_wetness_watch"],
                "retrieved_context": ["pepper-climate-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "Delta 6.5 육묘 블록의 야간 고습과 긴 잎 젖음 재발은 활착 지연과 병해 위험이 높은 상태다.",
                "risk_level": "high",
                "diagnosis": [
                    "육묘기 냉습과 긴 잎 젖음은 초기 병해와 활착 지연 위험을 빠르게 키운다.",
                    "이때 환기를 바로 여는 것보다 보온을 유지하면서 현장 확인과 경고를 먼저 거는 편이 안전하다.",
                ],
                "recommended_actions": [
                    action(
                        "action10-029",
                        1,
                        "create_alert",
                        "zone",
                        "nursery-zone-a",
                        "high",
                        "육묘 냉습과 잎 젖음 재발을 즉시 경고한다.",
                        "운영자가 병해와 활착 지연 위험을 놓치지 않고 대응할 수 있다.",
                        10,
                    ),
                    action(
                        "action10-029",
                        2,
                        "request_human_check",
                        "operator",
                        "nursery-manager",
                        "medium",
                        "실제 잎 젖음 범위, 블록 표면 상태, 보온 유지 조건을 현장에서 확인한다.",
                        "냉습과 환기 오판을 줄이고 현장 대응을 조정할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_vent",
                        "reason": "해진 뒤 냉기 유입을 키우는 환기 개방은 육묘 활착을 더 악화시킬 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("visual_inspection", 15, "육묘 블록 표면 수분, 잎 젖음 범위, 병반 의심 개체를 다시 확인한다.")
                ],
                "confidence": 0.81,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-climate-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "action-rec-030",
            "task_type": "action_recommendation",
            "input": {
                "farm_id": "demo-farm",
                "zone_id": "gh-01-fertigation-room",
                "growth_stage": "fruit_expansion",
                "state_summary": "배액 pH와 drain volume 기록이 비어 있는데 recipe 조정 권고가 동시에 올라왔다.",
                "active_constraints": ["fertigation_evidence_incomplete", "recipe_change_pending"],
                "retrieved_context": ["pepper-hydroponic-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "배액 pH와 drain volume 근거가 비어 있으면 recipe 조정을 자동으로 진행하면 안 된다.",
                "risk_level": "unknown",
                "diagnosis": [
                    "배액 근거가 비어 있는 상태에서는 현재 양액 리스크를 high나 normal로 확정할 수 없다.",
                    "근거 복구 없이 adjust_fertigation을 실행하면 오판된 recipe 조정이 누적될 수 있다.",
                ],
                "recommended_actions": [
                    action(
                        "action10-030",
                        1,
                        "pause_automation",
                        "system",
                        "gh-01-fertigation-control",
                        "high",
                        "배액 근거가 복구될 때까지 자동 recipe 조정을 일시 정지한다.",
                        "근거 없는 recipe 전환을 막을 수 있다.",
                        0,
                    ),
                    action(
                        "action10-030",
                        2,
                        "request_human_check",
                        "operator",
                        "fertigation-manager",
                        "medium",
                        "배액 pH, drain volume, 최근 배액률 로그를 수동으로 다시 확인한다.",
                        "근거 복구 후에만 recipe 전환 여부를 판단할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "drain evidence가 비어 있어 현재는 자동 recipe 조정을 걸면 안 된다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("sensor_recheck", 5, "배액 pH와 drain volume 로그 복구 여부를 확인한 뒤 recipe 전환을 재평가한다.")
                ],
                "confidence": 0.65,
                "retrieval_coverage": "partial",
                "citations": [citation("pepper-hydroponic-001"), citation("pepper-agent-001")],
            },
        },
    ]


def state_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_id": "state-judgement-108",
            "task_type": "climate_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "nursery",
                "zone_id": "nursery-zone-a",
                "state_summary": "Grodan Delta 6.5 육묘 블록 구간에서 해진 뒤 보온은 유지되지만 습도가 높고 잎 젖음 시간이 늘고 있다.",
                "active_constraints": ["nursery_cold_humid_watch", "leaf_wetness_watch"],
                "retrieved_context": ["pepper-climate-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "육묘기 Delta 6.5 구간의 야간 고습과 잎 젖음 증가는 활착 지연과 병해 위험이 높은 상태다.",
                "risk_level": "high",
                "diagnosis": [
                    "육묘기 냉습과 잎 젖음 증가는 활착 지연과 초기 병해 확산을 빠르게 키운다.",
                    "보온 유지 상태에서는 무리한 환기보다 현장 확인과 경고를 우선해야 한다.",
                ],
                "recommended_actions": [
                    action(
                        "state14-108",
                        1,
                        "create_alert",
                        "zone",
                        "nursery-zone-a",
                        "high",
                        "야간 고습과 잎 젖음 재발을 즉시 경고한다.",
                        "육묘 냉습 대응 우선순위를 빠르게 높일 수 있다.",
                        10,
                    ),
                    action(
                        "state14-108",
                        2,
                        "request_human_check",
                        "operator",
                        "nursery-manager",
                        "medium",
                        "실제 잎 젖음 범위와 보온 유지 상태를 현장에서 확인한다.",
                        "냉습 원인과 병해 위험 구간을 바로 확인할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_vent",
                        "reason": "해진 뒤 환기 개방은 육묘 활착과 온도 유지에 불리할 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("visual_inspection", 15, "잎 젖음 범위, 블록 표면 수분, 의심 병반을 다시 확인한다.")
                ],
                "confidence": 0.82,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-climate-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "state-judgement-109",
            "task_type": "nutrient_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruit_expansion",
                "zone_id": "gh-01-zone-c",
                "state_summary": "GT Master 슬래브에서 급액 EC 2.6 대비 배액 EC 5.3이 반복되고 배액률도 14%로 낮다.",
                "active_constraints": ["salt_accumulation_watch", "low_drain_fraction_watch"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "급액 대비 배액 EC 차이가 크게 벌어지고 배액률까지 낮아 염류 집적과 근권 스트레스 위험이 높다.",
                "risk_level": "high",
                "diagnosis": [
                    "급액 EC 2.6 대비 배액 EC 5.3이 반복되면 slab 내 염류 집적 가능성이 높다.",
                    "낮은 배액률까지 겹치면 근권 스트레스가 빠르게 커질 수 있어 경고와 현장 점검이 우선이다.",
                ],
                "recommended_actions": [
                    action(
                        "state14-109",
                        1,
                        "create_alert",
                        "zone",
                        "gh-01-zone-c",
                        "high",
                        "염류 집적과 낮은 배액률이 겹친 고위험 상황을 즉시 공유한다.",
                        "근권 스트레스 대응 우선순위를 높일 수 있다.",
                        10,
                    ),
                    action(
                        "state14-109",
                        2,
                        "request_human_check",
                        "operator",
                        "fertigation-manager",
                        "medium",
                        "대표 slab 배액 반응과 실제 배지 상태를 현장에서 다시 확인한다.",
                        "염류 집적과 line 편차를 구분할 수 있다.",
                        0,
                    ),
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("trend_review", 20, "대표 slab의 배액 EC, 배액률, 급액량 추세를 다시 확인한다.")
                ],
                "confidence": 0.83,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
            },
        },
        {
            "sample_id": "state-judgement-110",
            "task_type": "climate_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "nursery",
                "zone_id": "nursery-zone-b",
                "state_summary": "Delta 6.5 육묘 블록에서 해진 뒤 고습과 잎 젖음 증가가 다시 반복되고 보온은 유지 중이다.",
                "active_constraints": ["nursery_cold_humid_watch", "leaf_wetness_watch"],
                "retrieved_context": ["pepper-climate-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "육묘 블록의 해진 뒤 고습과 잎 젖음 재발은 활착 지연과 병해 위험이 높은 상태다.",
                "risk_level": "high",
                "diagnosis": [
                    "야간 고습과 잎 젖음 재발은 다음날 활착 회복 지연과 병해 위험을 키운다.",
                    "환기 개방보다 경고와 수동 점검을 먼저 걸어 실제 잎 젖음 범위를 확인해야 한다.",
                ],
                "recommended_actions": [
                    action(
                        "state14-110",
                        1,
                        "create_alert",
                        "zone",
                        "nursery-zone-b",
                        "high",
                        "육묘 냉습 재발 위험을 즉시 경고한다.",
                        "육묘 구간 점검 우선순위를 높일 수 있다.",
                        10,
                    ),
                    action(
                        "state14-110",
                        2,
                        "request_human_check",
                        "operator",
                        "nursery-manager",
                        "medium",
                        "실제 잎 젖음 범위와 블록 표면 상태를 현장에서 다시 확인한다.",
                        "냉습 재발과 병해 확산 징후를 빠르게 구분할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_vent",
                        "reason": "해진 뒤 냉기 유입을 늘리는 환기 개방은 육묘 활착에 불리할 수 있다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("visual_inspection", 15, "육묘 블록 표면 수분과 잎 젖음 재발 구간을 다시 확인한다.")
                ],
                "confidence": 0.81,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-climate-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "state-judgement-111",
            "task_type": "rootzone_diagnosis",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruit_expansion",
                "zone_id": "gh-01-zone-b",
                "state_summary": "GT Master 슬래브의 새벽 WC가 낮고 야간 dry-back이 과도한 날마다 오후 잎 처짐 메모가 반복된다.",
                "active_constraints": ["gt_master_dryback_watch", "rootzone_stress_field_check"],
                "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
            },
            "preferred_output": {
                "situation_summary": "GT Master 슬래브의 낮은 새벽 WC와 과도한 dry-back, 반복 잎 처짐은 근권 스트레스 고위험 신호다.",
                "risk_level": "high",
                "diagnosis": [
                    "낮은 새벽 WC와 과도한 dry-back이 반복되면 낮 시간 회복 지연과 잎 처짐으로 이어질 수 있다.",
                    "recipe 조정보다 현장 점검과 경고를 먼저 걸어 실제 rootzone stress 여부를 확인해야 한다.",
                ],
                "recommended_actions": [
                    action(
                        "state14-111",
                        1,
                        "create_alert",
                        "zone",
                        "gh-01-zone-b",
                        "high",
                        "GT Master 근권 스트레스 위험을 즉시 알린다.",
                        "반복 잎 처짐 구간 대응을 빠르게 시작할 수 있다.",
                        10,
                    ),
                    action(
                        "state14-111",
                        2,
                        "request_human_check",
                        "operator",
                        "rootzone-manager",
                        "medium",
                        "대표 slab의 새벽 WC, 배액 반응, dripper 균일도를 현장에서 다시 확인한다.",
                        "실제 근권 스트레스와 line 편차를 구분할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "현재는 recipe 조정보다 rootzone evidence 확인이 먼저라 자동 recipe 변경을 걸면 안 된다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("visual_inspection", 20, "대표 slab의 새벽 WC, 배액 반응, 오후 잎 처짐 시점을 다시 확인한다.")
                ],
                "confidence": 0.82,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-rootzone-001"), citation("pepper-hydroponic-001")],
            },
        },
        {
            "sample_id": "state-judgement-112",
            "task_type": "nutrient_risk",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruit_expansion",
                "zone_id": "gh-01-zone-a",
                "state_summary": "GT Master 구역에서 recipe 전환 직전 drain EC와 drain volume 기록이 동시에 비어 있다.",
                "active_constraints": ["fertigation_evidence_incomplete", "recipe_change_pending"],
                "retrieved_context": ["pepper-hydroponic-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "drain EC와 drain volume 근거가 동시에 비어 있어 현재 nutrient risk는 unknown으로 두고 자동 recipe 전환을 멈춰야 한다.",
                "risk_level": "unknown",
                "diagnosis": [
                    "배액 근거가 비어 있으면 현재 양액 리스크를 정확히 high 또는 medium으로 고정할 수 없다.",
                    "근거 복구 전까지는 자동 recipe 전환보다 pause와 수동 확인이 먼저다.",
                ],
                "recommended_actions": [
                    action(
                        "state14-112",
                        1,
                        "pause_automation",
                        "system",
                        "gh-01-fertigation-control",
                        "high",
                        "배액 근거가 복구될 때까지 자동 recipe 전환을 일시 정지한다.",
                        "근거 없는 nutrient adjustment를 막을 수 있다.",
                        0,
                    ),
                    action(
                        "state14-112",
                        2,
                        "request_human_check",
                        "operator",
                        "fertigation-manager",
                        "medium",
                        "drain EC, drain volume, 최근 배액률 로그를 수동으로 다시 확인한다.",
                        "근거 복구 후에만 recipe 전환 여부를 다시 판단할 수 있다.",
                        0,
                    ),
                ],
                "skipped_actions": [
                    {
                        "action_type": "adjust_fertigation",
                        "reason": "drain evidence가 비어 있는 상태에서는 자동 recipe 조정을 진행하면 안 된다.",
                    }
                ],
                "requires_human_approval": False,
                "approval_reason": None,
                "follow_up": [
                    follow_up("sensor_recheck", 5, "drain EC와 drain volume 로그 복구 여부를 확인한다.")
                ],
                "confidence": 0.64,
                "retrieval_coverage": "partial",
                "citations": [citation("pepper-hydroponic-001"), citation("pepper-agent-001")],
            },
        },
    ]


def robot_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_id": "robot-task-045",
            "task_type": "robot_task_prioritization",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruiting",
                "zone_id": "gh-01-zone-b",
                "state_summary": "과실기 canopy 안쪽에 국소 병반 의심 hotspot이 표시돼 영상 재확인이 필요하다.",
                "candidates": [{"candidate_id": "hotspot-21", "disease_score": 0.73, "reachable": True}],
                "safety_context": {"worker_present": False, "robot_zone_clear": True},
                "retrieved_context": ["pepper-pest-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "병반 의심 hotspot은 inspect_crop 작업으로 재확인이 우선이다.",
                "risk_level": "medium",
                "robot_tasks": [
                    robot_task(
                        "inspect_crop",
                        "hotspot-21",
                        "zone",
                        "gh-01-zone-b-hotspot-21",
                        "high",
                        "국소 병반 의심 hotspot을 먼저 재촬영하고 현장 영상을 확인해야 한다.",
                    )
                ],
                "skipped_candidates": [],
                "requires_human_approval": True,
                "follow_up": [follow_up("visual_inspection", 15, "hotspot-21의 실제 병반 여부와 확산 범위를 확인한다.")],
                "confidence": 0.8,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-pest-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "robot-task-046",
            "task_type": "robot_task_prioritization",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "harvest",
                "zone_id": "gh-01-zone-c",
                "state_summary": "수확 후보 두 개 중 하나는 pallet block으로 바로 접근할 수 없어 우회가 먼저 필요하다.",
                "candidates": [
                    {"candidate_id": "cand-87", "ripeness_score": 0.95, "reachable": False, "blocked_by": "pallet-block"},
                    {"candidate_id": "cand-88", "ripeness_score": 0.93, "reachable": True},
                ],
                "safety_context": {"worker_present": False, "robot_zone_clear": True},
                "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "blocked candidate는 harvest review보다 skip_area를 먼저 생성해야 한다.",
                "risk_level": "high",
                "robot_tasks": [
                    robot_task(
                        "skip_area",
                        "cand-87",
                        "zone",
                        "gh-01-zone-c-pallet-block",
                        "high",
                        "pallet block으로 접근이 막혀 있어 우회 지시가 먼저 필요하다.",
                    )
                ],
                "skipped_candidates": [
                    {"candidate_id": "cand-88", "reason": "현재 문제는 blocked candidate 처리라 접근 가능 후보 검토보다 우회 지시가 우선이다."}
                ],
                "requires_human_approval": True,
                "follow_up": [follow_up("operator_confirm", 0, "pallet block 해제 시점과 우회 동선 가능 여부를 확인한다.")],
                "confidence": 0.84,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "robot-task-047",
            "task_type": "robot_task_prioritization",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "fruiting",
                "zone_id": "gh-01-zone-a",
                "state_summary": "과실 hotspot은 보이지만 성숙도 confidence가 낮아 재촬영이 먼저 필요하다.",
                "candidates": [{"candidate_id": "hotspot-22", "ripeness_score": 0.58, "reachable": True, "vision_confidence": 0.39}],
                "safety_context": {"worker_present": False, "robot_zone_clear": True},
                "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "낮은 confidence hotspot은 harvest review보다 inspect_crop이 먼저다.",
                "risk_level": "medium",
                "robot_tasks": [
                    robot_task(
                        "inspect_crop",
                        "hotspot-22",
                        "candidate",
                        "hotspot-22",
                        "high",
                        "성숙도 confidence가 낮아 재촬영과 근접 확인이 먼저 필요하다.",
                    )
                ],
                "skipped_candidates": [],
                "requires_human_approval": True,
                "follow_up": [follow_up("visual_inspection", 15, "hotspot-22의 실제 성숙도와 병반 여부를 다시 확인한다.")],
                "confidence": 0.77,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
            },
        },
        {
            "sample_id": "robot-task-048",
            "task_type": "robot_task_prioritization",
            "input": {
                "farm_id": "demo-farm",
                "growth_stage": "harvest",
                "zone_id": "gh-01-zone-b",
                "state_summary": "성숙도와 병반 여부가 모두 애매한 후보라 수동 검토가 먼저 필요하다.",
                "candidates": [{"candidate_id": "cand-89", "ripeness_score": 0.71, "disease_score": 0.41, "reachable": True, "vision_confidence": 0.44}],
                "safety_context": {"worker_present": False, "robot_zone_clear": True},
                "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
            },
            "preferred_output": {
                "situation_summary": "성숙도와 병반 여부가 모두 애매하면 manual_review가 먼저다.",
                "risk_level": "medium",
                "robot_tasks": [
                    robot_task(
                        "manual_review",
                        "cand-89",
                        "candidate",
                        "cand-89",
                        "high",
                        "성숙도와 병반 여부가 동시에 불확실해 수동 검토가 먼저 필요하다.",
                    )
                ],
                "skipped_candidates": [],
                "requires_human_approval": True,
                "follow_up": [follow_up("visual_inspection", 15, "cand-89의 실제 숙도와 병반 여부를 현장에서 확인한다.")],
                "confidence": 0.76,
                "retrieval_coverage": "sufficient",
                "citations": [citation("pepper-harvest-001"), citation("pepper-agent-001")],
            },
        },
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def main() -> None:
    action = action_rows()
    state = state_rows()
    robot = robot_rows()
    write_jsonl(ACTION_OUTPUT, action)
    write_jsonl(STATE_OUTPUT, state)
    write_jsonl(ROBOT_OUTPUT, robot)
    print(
        json.dumps(
            {
                "action_output": str(ACTION_OUTPUT.relative_to(ROOT)),
                "action_rows": len(action),
                "state_output": str(STATE_OUTPUT.relative_to(ROOT)),
                "state_rows": len(state),
                "robot_output": str(ROBOT_OUTPUT.relative_to(ROOT)),
                "robot_rows": len(robot),
                "total_rows": len(action) + len(state) + len(robot),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
