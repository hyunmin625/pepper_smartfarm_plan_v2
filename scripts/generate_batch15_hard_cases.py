#!/usr/bin/env python3
"""Generate next-only hard-case training samples for safety/failure/robot slices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STATE = REPO_ROOT / "data/examples/state_judgement_samples_batch15_hard_cases.jsonl"
OUTPUT_FAILURE = REPO_ROOT / "data/examples/failure_response_samples_batch15_hard_cases.jsonl"
OUTPUT_ROBOT = REPO_ROOT / "data/examples/robot_task_samples_batch6_hard_cases.jsonl"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


STATE_ROWS: list[dict[str, Any]] = [
    {
        "sample_id": "state-judgement-201",
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-a",
            "growth_stage": "fruiting",
            "state_summary": "작업자 출입 이벤트가 active인데 circulation fan과 shade 자동 명령 큐가 동시에 남아 있다.",
            "active_constraints": ["worker_present", "robot_zone_not_clear"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "작업자 출입이 active인 동안에는 모든 동력 장치 자동 명령을 차단하고 경고를 남겨야 한다.",
            "risk_level": "critical",
            "diagnosis": [
                "작업자 존재는 자동 장치 제어보다 안전 인터락이 우선인 상태다.",
                "이 구간에서 환기나 차광 자동 명령을 그대로 보내면 충돌과 오작동 위험이 커진다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "state15-201-act-001",
                    "action_type": "block_action",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-a-action-gate"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "작업자 출입이 active인 동안에는 동력 장치 자동 명령을 차단한다.",
                    "expected_effect": "작업자-장치 충돌과 예기치 않은 자동 작동을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "state15-201-act-002",
                    "action_type": "create_alert",
                    "target": {"target_type": "zone", "target_id": "gh-01-zone-a"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "작업자 존재로 자동 제어를 차단한 상태를 운영자에게 즉시 알린다.",
                    "expected_effect": "현장 안전 해제 조건을 빠르게 확인할 수 있다.",
                    "cooldown_minutes": 5,
                },
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "operator_confirm",
                    "due_in_minutes": 0,
                    "description": "작업자 퇴장과 zone clear 상태를 확인한다.",
                }
            ],
            "confidence": 0.93,
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"}],
        },
    },
    {
        "sample_id": "state-judgement-202",
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-b",
            "growth_stage": "fruiting",
            "state_summary": "manual override가 active인데 irrigation manifold 재시작 명령이 대기 중이다.",
            "active_constraints": ["manual_override_active", "line_pressure_fault_watch"],
            "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        },
        "preferred_output": {
            "situation_summary": "manual override가 active이면 자동 급수 재시작보다 차단과 경고가 먼저다.",
            "risk_level": "critical",
            "diagnosis": [
                "수동 개입 중인 구간에서 자동 급수 재시작은 현장 조치와 충돌할 수 있다.",
                "line pressure 확인 전 자동 재기동을 허용하면 수동 복구를 방해한다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "state15-202-act-001",
                    "action_type": "block_action",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-b-action-gate"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "manual override가 active인 동안에는 급수 자동 재시작을 차단한다.",
                    "expected_effect": "수동 개입과 자동 명령이 충돌하는 것을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "state15-202-act-002",
                    "action_type": "create_alert",
                    "target": {"target_type": "zone", "target_id": "gh-01-zone-b"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "manual override active 상태와 급수 재시작 차단을 운영자에게 알린다.",
                    "expected_effect": "복구 순서를 수동 확인 기준으로 유지할 수 있다.",
                    "cooldown_minutes": 5,
                },
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "operator_confirm",
                    "due_in_minutes": 0,
                    "description": "manual override 해제와 line pressure 정상 여부를 확인한다.",
                }
            ],
            "confidence": 0.92,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
            ],
        },
    },
    {
        "sample_id": "state-judgement-203",
        "task_type": "sensor_fault",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-c",
            "growth_stage": "flowering",
            "state_summary": "온도 센서는 jump를 반복하고 습도 센서는 flatline이라 VPD 계산을 신뢰할 수 없다.",
            "active_constraints": ["core_sensor_fault", "climate_control_guard"],
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "핵심 기후 센서가 noisy/flatline 상태라 현재 기후 해석을 자동 위험도로 단정할 수 없다.",
            "risk_level": "unknown",
            "diagnosis": [
                "온도 jump와 습도 flatline이 함께 발생하면 VPD 계산과 고온 판단이 모두 흔들린다.",
                "이때는 기후 제어를 보수적으로 멈추고 수동 확인으로 전환해야 한다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "state15-203-act-001",
                    "action_type": "pause_automation",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-c-auto-control"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "핵심 기후 센서 품질이 회복될 때까지 자동 기후 제어를 멈춘다.",
                    "expected_effect": "오판된 센서값에 따라 환기·차광 명령이 누적되는 것을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "state15-203-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "climate-manager"},
                    "risk_level": "medium",
                    "approval_required": False,
                    "reason": "온도/습도 센서 상태와 현장 체감 환경을 함께 점검한다.",
                    "expected_effect": "센서 fault와 실제 환경 문제를 구분할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "sensor_recheck",
                    "due_in_minutes": 5,
                    "description": "온도와 습도 센서 최신값, jump/flatline 여부, 대체 측정값을 확인한다.",
                }
            ],
            "confidence": 0.57,
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"}],
        },
    },
    {
        "sample_id": "state-judgement-204",
        "task_type": "sensor_fault",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-a",
            "growth_stage": "fruit_expansion",
            "state_summary": "slab WC는 flatline이고 drain sensor는 missing이라 근권 증거가 비어 있다.",
            "active_constraints": ["rootzone_evidence_incomplete", "fertigation_hold"],
            "retrieved_context": ["pepper-rootzone-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "근권 핵심 센서 증거가 비어 있어 현재 근권 상태를 high/medium으로 확정할 수 없다.",
            "risk_level": "unknown",
            "diagnosis": [
                "slab WC flatline과 drain missing이 겹치면 근권 상태의 핵심 증거가 무너진다.",
                "이 구간에서는 자동 급수나 양액 조정보다 증거 복구와 수동 점검이 먼저다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "state15-204-act-001",
                    "action_type": "pause_automation",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-a-fertigation-control"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "근권 증거가 회복될 때까지 자동 급수·양액 제어를 멈춘다.",
                    "expected_effect": "불완전한 근거로 급액 레시피가 바뀌는 것을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "state15-204-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "fertigation-manager"},
                    "risk_level": "medium",
                    "approval_required": False,
                    "reason": "슬래브 함수율, 배액 상태, 수동 EC/pH를 현장에서 다시 확인한다.",
                    "expected_effect": "근권 상태를 수동 측정으로 다시 확보할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "sensor_recheck",
                    "due_in_minutes": 10,
                    "description": "slab WC와 drain sensor 정상화, 수동 측정값, 실제 배액 상태를 확인한다.",
                }
            ],
            "confidence": 0.55,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
            ],
        },
    },
]

FAILURE_ROWS: list[dict[str, Any]] = [
    {
        "sample_id": "failure-response-101",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-a",
            "growth_stage": "fruit_set",
            "failure_type": "irrigation_pump_communication_loss",
            "state_summary": "야간 관수 직전 irrigation pump 통신이 끊겨 마지막 명령 실행 여부를 확인할 수 없다.",
            "active_faults": ["irrigation_pump_comm_loss", "night_irrigation_window"],
            "last_action": "short_irrigation",
            "retrieved_context": ["pepper-rootzone-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "핵심 급수 경로 통신 손실이라 야간 급수 상태를 신뢰할 수 없어 즉시 안전 모드가 필요하다.",
            "risk_level": "critical",
            "diagnosis": [
                "야간 급수 직전 pump communication loss는 실제 급수 실행 여부를 불명확하게 만든다.",
                "이 상태에서 자동 급수를 계속 시도하면 과소/과다 급수 모두 생길 수 있다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "fail15-101-act-001",
                    "action_type": "enter_safe_mode",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-a-irrigation-control"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "핵심 급수 경로를 신뢰할 수 없어 자동 제어를 안전 모드로 전환한다.",
                    "expected_effect": "불명확한 급수 상태에서 자동 명령 누적을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "fail15-101-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "irrigation-manager"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "현장에서 전원, 통신, 실제 급수 상태를 확인한다.",
                    "expected_effect": "수동 복구 전 실제 급수 상태를 빠르게 확인할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": "pump 전원과 실제 급수 이력, 라인 압력을 확인한다.",
                }
            ],
            "confidence": 0.92,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"},
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
            ],
        },
    },
    {
        "sample_id": "failure-response-102",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-water-room",
            "growth_stage": "fruit_expansion",
            "failure_type": "source_water_low_pressure_lock",
            "state_summary": "source water low-pressure lock이 반복되고 main valve readback도 늦어 급수 경로가 불안정하다.",
            "active_faults": ["low_pressure_lock", "source_water_valve_readback_slow"],
            "last_action": "pause_automation",
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "원수 압력 lock과 readback 지연이 겹쳐 급수 경로를 신뢰할 수 없어 안전 모드가 먼저다.",
            "risk_level": "critical",
            "diagnosis": [
                "원수 저압 lock 반복은 급수 누락과 불완전 공급 위험을 만든다.",
                "main valve readback도 늦으면 공급 경로 정상 여부를 원격으로 확정할 수 없다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "fail15-102-act-001",
                    "action_type": "enter_safe_mode",
                    "target": {"target_type": "system", "target_id": "source-water-control"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "원수 경로 상태가 불명확해 자동 공급 제어를 안전 모드로 전환한다.",
                    "expected_effect": "불안정한 원수 상태에서 자동 명령 누적을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "fail15-102-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "facility-manager"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "원수 압력과 메인 밸브 실제 상태를 현장에서 확인한다.",
                    "expected_effect": "수동 복구 전에 공급 안정성을 다시 확인할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": "원수 압력, 밸브 실제 개폐 상태, 예비 공급 가능 여부를 확인한다.",
                }
            ],
            "confidence": 0.92,
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"}],
        },
    },
    {
        "sample_id": "failure-response-103",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-dry-room",
            "growth_stage": "harvest",
            "failure_type": "dry_room_readback_loss",
            "state_summary": "dehumidifier와 circulation fan readback이 동시에 사라져 현재 건조 상태를 확인할 수 없다.",
            "active_faults": ["dry_room_readback_loss", "device_status_unknown"],
            "last_action": "adjust_fan",
            "retrieved_context": ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "건조실 핵심 장치 readback loss라 현재 건조 lot 상태를 신뢰할 수 없어 안전 모드가 필요하다.",
            "risk_level": "critical",
            "diagnosis": [
                "건조실 장치 상태를 읽을 수 없으면 재흡습과 품질 편차를 즉시 놓치게 된다.",
                "readback loss 상태에서는 자동 건조 명령보다 현장 확인이 우선이다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "fail15-103-act-001",
                    "action_type": "enter_safe_mode",
                    "target": {"target_type": "system", "target_id": "gh-01-dry-room-control"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "건조실 핵심 장치 상태를 읽을 수 없어 자동 제어를 안전 모드로 전환한다.",
                    "expected_effect": "품질 손상으로 이어질 수 있는 자동 제어 누적을 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "fail15-103-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "storage-manager"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "lot 상태와 장치 전원, 통신, 실제 건조 상태를 현장에서 확인한다.",
                    "expected_effect": "수동 복구 전에 lot 품질 위험을 빠르게 확인할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": "건조실 장치 전원과 lot 상태, RH 추세를 현장에서 확인한다.",
                }
            ],
            "confidence": 0.93,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-house-drying-hygiene-001", "document_id": "RAG-SRC-001"},
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
            ],
        },
    },
    {
        "sample_id": "failure-response-104",
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": "gh-01-zone-b",
            "growth_stage": "fruiting",
            "failure_type": "reboot_recovery_unknown_state",
            "state_summary": "정전 복구 직후 controller uptime은 짧고 heater/fan 마지막 상태 동기화가 아직 끝나지 않았다.",
            "active_faults": ["power_recovery", "device_state_sync_unknown"],
            "last_action": "adjust_heating",
            "retrieved_context": ["pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "재부팅 직후 장치 상태 동기화가 끝나지 않아 자동 복귀보다 안전 모드와 수동 확인이 먼저다.",
            "risk_level": "critical",
            "diagnosis": [
                "reboot recovery 구간에서는 마지막 명령 상태와 실제 장치 상태가 어긋날 수 있다.",
                "state sync가 끝나기 전 자동 복귀를 허용하면 잘못된 장치 상태를 증폭시킬 수 있다.",
            ],
            "recommended_actions": [
                {
                    "action_id": "fail15-104-act-001",
                    "action_type": "enter_safe_mode",
                    "target": {"target_type": "system", "target_id": "gh-01-zone-b-safe-control"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "재부팅 직후 장치 상태가 불명확해 자동 제어를 안전 모드로 유지한다.",
                    "expected_effect": "state sync 완료 전 잘못된 자동 복귀를 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": "fail15-104-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "climate-manager"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "heater/fan 실제 상태와 controller sync 완료 여부를 확인한다.",
                    "expected_effect": "수동 복귀 절차를 안전하게 시작할 수 있다.",
                    "cooldown_minutes": 0,
                },
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": "heater/fan 실제 상태, sync 완료 여부, 재부팅 원인을 확인한다.",
                }
            ],
            "confidence": 0.9,
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"}],
        },
    },
]

ROBOT_ROWS: list[dict[str, Any]] = [
    {
        "sample_id": "robot-task-101",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "harvest",
            "zone_id": "gh-01-zone-a",
            "state_summary": "수확 후보는 있으나 작업자 정리 작업과 pallet 이동이 동시에 진행 중이라 robot zone이 clear하지 않다.",
            "candidates": [{"candidate_id": "cand-101", "ripeness_score": 0.96, "reachable": True}],
            "safety_context": {"worker_present": True, "robot_zone_clear": False},
            "retrieved_context": ["pepper-harvest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "작업자와 pallet 이동이 끝나기 전에는 harvest robot task를 만들면 안 된다.",
            "risk_level": "critical",
            "robot_tasks": [],
            "skipped_candidates": [
                {
                    "candidate_id": "cand-101",
                    "reason": "worker present와 zone unclear가 동시에 active라 robot task 생성이 금지된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "operator_confirm",
                    "due_in_minutes": 0,
                    "description": "작업자 퇴장과 aisle clear 완료 여부를 확인한다.",
                }
            ],
            "confidence": 0.92,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-harvest-001", "document_id": "RAG-SRC-001"},
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
            ],
        },
    },
    {
        "sample_id": "robot-task-102",
        "task_type": "robot_task_prioritization",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": "fruiting",
            "zone_id": "gh-01-zone-c",
            "state_summary": "inspect hotspot은 존재하지만 estop reset이 끝나지 않아 robot subsystem을 아직 재가동하면 안 된다.",
            "candidates": [{"candidate_id": "hotspot-101", "disease_score": 0.76, "reachable": True}],
            "safety_context": {"worker_present": False, "robot_zone_clear": False, "estop_active": True},
            "retrieved_context": ["pepper-pest-001", "pepper-agent-001"],
        },
        "preferred_output": {
            "situation_summary": "estop이 active인 동안에는 inspect robot task보다 수동 확인이 먼저다.",
            "risk_level": "critical",
            "robot_tasks": [],
            "skipped_candidates": [
                {
                    "candidate_id": "hotspot-101",
                    "reason": "estop active와 zone unclear 상태에서 robot subsystem 재가동은 금지된다.",
                }
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "operator_confirm",
                    "due_in_minutes": 0,
                    "description": "estop reset 완료와 zone clear 상태를 확인한 뒤 수동 점검 여부를 판단한다.",
                }
            ],
            "confidence": 0.91,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-pest-001", "document_id": "RAG-SRC-001"},
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
            ],
        },
    },
]


def main() -> None:
    write_jsonl(OUTPUT_STATE, STATE_ROWS)
    write_jsonl(OUTPUT_FAILURE, FAILURE_ROWS)
    write_jsonl(OUTPUT_ROBOT, ROBOT_ROWS)
    print(f"state_rows: {len(STATE_ROWS)}")
    print(f"failure_rows: {len(FAILURE_ROWS)}")
    print(f"robot_rows: {len(ROBOT_ROWS)}")
    print(f"total_rows: {len(STATE_ROWS) + len(FAILURE_ROWS) + len(ROBOT_ROWS)}")


if __name__ == "__main__":
    main()
