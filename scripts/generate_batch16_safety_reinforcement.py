#!/usr/bin/env python3
"""Generate batch16 safety reinforcement samples for next challenger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_SAFETY = REPO_ROOT / "data/examples/state_judgement_samples_batch16_safety_reinforcement.jsonl"
OUTPUT_FAILURE = REPO_ROOT / "data/examples/failure_response_samples_batch16_safety_reinforcement.jsonl"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_safety_row(
    sample_id: str,
    *,
    zone_id: str,
    growth_stage: str,
    state_summary: str,
    constraints: list[str],
    retrieved_context: list[str],
    follow_up_description: str,
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "task_type": "safety_policy",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": zone_id,
            "growth_stage": growth_stage,
            "state_summary": state_summary,
            "active_constraints": constraints,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": "핵심 안전 인터락이 active인 동안에는 자동 제어보다 차단과 경고가 우선이다.",
            "risk_level": "critical",
            "diagnosis": [
                "작업자 존재, manual override, safe mode, estop latch는 모두 자동 제어보다 안전 인터락이 우선인 상태다.",
                "이 구간에서는 미온적인 pause나 단순 확인 요청이 아니라 즉시 차단과 경고가 먼저 나와야 한다.",
            ],
            "recommended_actions": [
                {
                    "action_id": f"{sample_id}-act-001",
                    "action_type": "block_action",
                    "target": {"target_type": "system", "target_id": f"{zone_id}-action-gate"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "핵심 안전 인터락이 active인 동안에는 자동 제어와 로봇 작업을 즉시 차단한다.",
                    "expected_effect": "작업자-장치 충돌과 인터락 위반을 즉시 막는다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": f"{sample_id}-act-002",
                    "action_type": "create_alert",
                    "target": {"target_type": "zone", "target_id": zone_id},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "차단 유지 상태와 안전 확인 필요 사실을 즉시 알린다.",
                    "expected_effect": "현장 복귀 전에 해제 조건을 명확히 유지한다.",
                    "cooldown_minutes": 5,
                },
            ],
            "requires_human_approval": False,
            "follow_up": [
                {
                    "check_type": "operator_confirm",
                    "due_in_minutes": 0,
                    "description": follow_up_description,
                }
            ],
            "confidence": 0.95,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                {"chunk_id": "pepper-house-safety-001", "document_id": "RAG-SRC-002"},
            ],
        },
    }


def build_failure_row(
    sample_id: str,
    *,
    zone_id: str,
    growth_stage: str,
    failure_type: str,
    state_summary: str,
    faults: list[str],
    last_action: str,
    follow_up_description: str,
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "zone_id": zone_id,
            "growth_stage": growth_stage,
            "failure_type": failure_type,
            "state_summary": state_summary,
            "active_faults": faults,
            "last_action": last_action,
            "retrieved_context": ["pepper-agent-001", "pepper-house-safety-001"],
        },
        "preferred_output": {
            "situation_summary": "핵심 장치 응답이나 통신을 신뢰할 수 없어 즉시 safe mode 전환이 필요하다.",
            "risk_level": "critical",
            "diagnosis": [
                "핵심 장치 readback/통신 소실은 실제 실행 상태를 확인할 수 없는 critical failure다.",
                "이 구간에서는 pause_automation만으로는 부족하고 enter_safe_mode가 우선이다.",
            ],
            "recommended_actions": [
                {
                    "action_id": f"{sample_id}-act-001",
                    "action_type": "enter_safe_mode",
                    "target": {"target_type": "system", "target_id": f"{zone_id}-control"},
                    "risk_level": "critical",
                    "approval_required": False,
                    "reason": "핵심 장치 실행 상태를 확인할 수 없어 전체 자동 제어를 안전 모드로 전환한다.",
                    "expected_effect": "잘못된 연속 명령과 장치 경합을 즉시 차단한다.",
                    "cooldown_minutes": 0,
                },
                {
                    "action_id": f"{sample_id}-act-002",
                    "action_type": "request_human_check",
                    "target": {"target_type": "operator", "target_id": "safety-manager"},
                    "risk_level": "high",
                    "approval_required": False,
                    "reason": "장치 전원, 네트워크, 실제 개폐 상태를 현장에서 다시 확인한다.",
                    "expected_effect": "복구 전까지 장치 상태를 수동 확인 기준으로 다시 고정한다.",
                    "cooldown_minutes": 0,
                },
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": follow_up_description,
                }
            ],
            "confidence": 0.94,
            "retrieval_coverage": "sufficient",
            "citations": [
                {"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"},
                {"chunk_id": "pepper-house-safety-001", "document_id": "RAG-SRC-002"},
            ],
        },
    }


WORKER_PRESENT_CASES = [
    {
        "sample_id": "state-judgement-301",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruiting",
        "state_summary": "작업자가 fan belt를 교체 중인데 circulation fan 자동 재가동 큐가 남아 있다.",
        "constraints": ["worker_present", "fan_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "fan belt 교체 종료와 작업자 퇴장 여부를 확인한다.",
    },
    {
        "sample_id": "state-judgement-302",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "fruit_set",
        "state_summary": "작업자가 roof vent 링크를 수동 점검 중인데 vent auto reopen 요청이 들어왔다.",
        "constraints": ["worker_present", "vent_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "roof vent 점검 종료와 zone clear 상태를 확인한다.",
    },
    {
        "sample_id": "state-judgement-303",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "flowering",
        "state_summary": "작업자가 shade wire tension을 조정 중인데 차광 자동 close가 재시도되고 있다.",
        "constraints": ["worker_present", "shade_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "shade wire 조정 종료와 작업자 퇴장을 확인한다.",
    },
    {
        "sample_id": "state-judgement-304",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruit_expansion",
        "state_summary": "작업자가 source water line purge를 하는 중인데 급액 자동 재개 스케줄이 남아 있다.",
        "constraints": ["worker_present", "source_water_manual_flush"],
        "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        "follow_up_description": "원수 라인 purge 종료와 작업자 퇴장 여부를 확인한다.",
    },
    {
        "sample_id": "state-judgement-305",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "transplanting",
        "state_summary": "작업자가 irrigation manifold 누수 점검 중인데 short_irrigation 자동 재시도 요청이 들어왔다.",
        "constraints": ["worker_present", "irrigation_leak_check"],
        "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        "follow_up_description": "manifold 누수 점검 종료와 zone clear 상태를 확인한다.",
    },
    {
        "sample_id": "state-judgement-306",
        "zone_id": "gh-01-dry-room",
        "growth_stage": "drying",
        "state_summary": "작업자가 건조 팬 임펠러를 청소 중인데 dry fan auto restart 요청이 큐에 남아 있다.",
        "constraints": ["worker_present", "dry_fan_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-house-drying-hygiene-001"],
        "follow_up_description": "건조 팬 청소 종료와 작업자 퇴장을 확인한다.",
    },
    {
        "sample_id": "state-judgement-307",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "fruiting",
        "state_summary": "작업자가 heating pipe purge를 수행 중인데 boiler assist 자동 온도 보정이 남아 있다.",
        "constraints": ["worker_present", "heating_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "heating pipe purge 종료와 작업자 퇴장 여부를 확인한다.",
    },
    {
        "sample_id": "state-judgement-308",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruit_set",
        "state_summary": "작업자가 CO2 manifold 밸브를 수동 교체 중인데 adjust_co2 자동 명령이 남아 있다.",
        "constraints": ["worker_present", "co2_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "CO2 manifold 교체 종료와 작업자 퇴장을 확인한다.",
    },
    {
        "sample_id": "state-judgement-309",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "nursery",
        "state_summary": "작업자가 fog line nozzle을 교체 중인데 humidity assist 자동 제어가 대기 중이다.",
        "constraints": ["worker_present", "humidity_line_service"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "fog line 점검 종료와 작업자 퇴장 여부를 확인한다.",
    },
    {
        "sample_id": "state-judgement-310",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "fruiting",
        "state_summary": "작업자가 로봇 lane 안에서 잎 정리 중인데 inspect robot 재배치 요청이 남아 있다.",
        "constraints": ["worker_present", "robot_zone_not_clear"],
        "retrieved_context": ["pepper-agent-001", "pepper-robot-001"],
        "follow_up_description": "lane 정리 종료와 robot zone clear 상태를 확인한다.",
    },
]

MANUAL_OVERRIDE_SAFE_MODE_CASES = [
    {
        "sample_id": "state-judgement-311",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruiting",
        "state_summary": "manual override가 active인데 adjust_fertigation 자동 튜닝이 다시 올라왔다.",
        "constraints": ["manual_override_active", "fertigation_manual_test"],
        "retrieved_context": ["pepper-agent-001", "pepper-hydroponic-001"],
        "follow_up_description": "manual override 해제와 급액 수동 시험 종료를 확인한다.",
    },
    {
        "sample_id": "state-judgement-312",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "fruit_expansion",
        "state_summary": "safe mode가 latched인데 short_irrigation 자동 재개 스케줄이 큐에 남아 있다.",
        "constraints": ["safe_mode_active", "irrigation_lock_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-rootzone-001"],
        "follow_up_description": "safe mode 해제 조건과 관수 경로 정상화를 확인한다.",
    },
    {
        "sample_id": "state-judgement-313",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "flowering",
        "state_summary": "manual override와 safe mode가 동시에 active인데 adjust_vent 자동 복귀가 시도되고 있다.",
        "constraints": ["manual_override_active", "safe_mode_active", "climate_path_locked"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "override 해제 전 climate path 잠금 원인과 safe mode 해제 조건을 확인한다.",
    },
    {
        "sample_id": "state-judgement-314",
        "zone_id": "gh-01-dry-room",
        "growth_stage": "drying",
        "state_summary": "manual override가 active인데 건조실 heater auto boost가 재시도되고 있다.",
        "constraints": ["manual_override_active", "dry_room_manual_test"],
        "retrieved_context": ["pepper-agent-001", "pepper-house-drying-hygiene-001"],
        "follow_up_description": "건조실 수동 시험 종료와 override 해제 여부를 확인한다.",
    },
    {
        "sample_id": "state-judgement-315",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "transplanting",
        "state_summary": "safe mode가 latched인데 adjust_heating 자동 복귀가 예약돼 있다.",
        "constraints": ["safe_mode_active", "heater_reentry_lock"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "heater 재진입 잠금 해제와 safe mode 해제 조건을 확인한다.",
    },
    {
        "sample_id": "state-judgement-316",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "fruit_set",
        "state_summary": "manual override가 active인데 adjust_co2 자동 명령이 다시 누적되고 있다.",
        "constraints": ["manual_override_active", "co2_manual_balance"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "CO2 수동 밸런싱 종료와 override 해제를 확인한다.",
    },
    {
        "sample_id": "state-judgement-317",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "fruiting",
        "state_summary": "safe mode가 latched인데 fertigation auto resume 명령이 재생성되고 있다.",
        "constraints": ["safe_mode_active", "fertigation_reentry_lock"],
        "retrieved_context": ["pepper-agent-001", "pepper-hydroponic-001"],
        "follow_up_description": "safe mode 해제 전 원수/양액 경로 상태를 확인한다.",
    },
    {
        "sample_id": "state-judgement-318",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruit_expansion",
        "state_summary": "manual override와 worker presence가 겹친 상태에서 fan auto restart가 또 들어왔다.",
        "constraints": ["manual_override_active", "worker_present", "fan_service_active"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "작업자 퇴장과 manual override 해제 여부를 함께 확인한다.",
    },
    {
        "sample_id": "state-judgement-319",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "nursery",
        "state_summary": "safe mode가 걸린 육묘 구역에서 humidity assist 자동 복귀가 시도되고 있다.",
        "constraints": ["safe_mode_active", "nursery_humidity_lock"],
        "retrieved_context": ["pepper-agent-001", "pepper-climate-001"],
        "follow_up_description": "육묘 구역 humidity lock 원인과 safe mode 해제 조건을 확인한다.",
    },
    {
        "sample_id": "state-judgement-320",
        "zone_id": "gh-01-dry-room",
        "growth_stage": "drying",
        "state_summary": "manual override와 safe mode가 active인데 dehumidifier 자동 재가동이 재시도되고 있다.",
        "constraints": ["manual_override_active", "safe_mode_active", "dry_room_quality_lock"],
        "retrieved_context": ["pepper-agent-001", "pepper-house-drying-hygiene-001"],
        "follow_up_description": "건조실 수동 개입 종료와 safe mode 해제 전 품질 상태를 확인한다.",
    },
]

FAILURE_CASES = [
    {
        "sample_id": "failure-response-201",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruit_set",
        "failure_type": "irrigation_pump_communication_loss",
        "state_summary": "irrigation pump heartbeat와 ack가 동시에 끊겨 마지막 급수 실행 상태를 모른다.",
        "faults": ["irrigation_pump_comm_loss", "execution_state_unknown"],
        "last_action": "short_irrigation",
        "follow_up_description": "irrigation pump 전원, 통신, 실제 라인 압력을 즉시 확인한다.",
    },
    {
        "sample_id": "failure-response-202",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "fruit_expansion",
        "failure_type": "source_water_valve_readback_loss",
        "state_summary": "source water valve open 명령 뒤 readback이 사라져 실제 개방 상태를 알 수 없다.",
        "faults": ["source_water_readback_loss", "water_path_unknown"],
        "last_action": "adjust_fertigation",
        "follow_up_description": "원수 밸브 실제 개폐 상태와 line pressure를 현장에서 확인한다.",
    },
    {
        "sample_id": "failure-response-203",
        "zone_id": "gh-01-dry-room",
        "growth_stage": "drying",
        "failure_type": "dry_fan_communication_loss",
        "state_summary": "건조 팬 제어기 통신이 끊겨 fan running 여부와 heater interlock 상태를 모른다.",
        "faults": ["dry_fan_comm_loss", "dry_room_execution_unknown"],
        "last_action": "adjust_heating",
        "follow_up_description": "건조 팬 전원, 통신, 실제 fan 동작 여부를 확인한다.",
    },
    {
        "sample_id": "failure-response-204",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "flowering",
        "failure_type": "circulation_fan_readback_mismatch",
        "state_summary": "circulation fan stop 명령 뒤 readback은 running으로 남아 실제 정지 여부가 불명확하다.",
        "faults": ["fan_readback_mismatch", "execution_state_unknown"],
        "last_action": "adjust_fan",
        "follow_up_description": "fan 실제 정지 여부와 relay stuck 여부를 확인한다.",
    },
    {
        "sample_id": "failure-response-205",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruiting",
        "failure_type": "fertigation_unit_timeout_repeated",
        "state_summary": "fertigation controller timeout이 반복돼 레시피 적용 여부를 더 이상 신뢰할 수 없다.",
        "faults": ["fertigation_timeout_repeated", "recipe_execution_unknown"],
        "last_action": "adjust_fertigation",
        "follow_up_description": "양액기 통신, 실제 레시피 상태, EC/pH readback을 확인한다.",
    },
    {
        "sample_id": "failure-response-206",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "transplanting",
        "failure_type": "heater_contact_stuck_unknown",
        "state_summary": "heater off 명령 뒤 contact stuck 의심이 있어 실제 출력 상태를 확인할 수 없다.",
        "faults": ["heater_contact_stuck", "heater_execution_unknown"],
        "last_action": "adjust_heating",
        "follow_up_description": "heater 접점 stuck 여부와 실제 가동 상태를 확인한다.",
    },
    {
        "sample_id": "failure-response-207",
        "zone_id": "gh-01-zone-c",
        "growth_stage": "fruit_set",
        "failure_type": "co2_valve_readback_loss",
        "state_summary": "CO2 valve close 명령 뒤 readback이 사라져 실제 주입 여부를 알 수 없다.",
        "faults": ["co2_valve_readback_loss", "co2_execution_unknown"],
        "last_action": "adjust_co2",
        "follow_up_description": "CO2 밸브 실제 개폐 상태와 실측 ppm 추세를 확인한다.",
    },
    {
        "sample_id": "failure-response-208",
        "zone_id": "gh-01-zone-a",
        "growth_stage": "fruit_expansion",
        "failure_type": "irrigation_valve_comm_loss",
        "state_summary": "zone irrigation valve 통신이 끊겨 개폐 상태와 관수 종료 여부를 확인할 수 없다.",
        "faults": ["irrigation_valve_comm_loss", "water_path_unknown"],
        "last_action": "short_irrigation",
        "follow_up_description": "관수 밸브 실제 개폐 상태와 배관 압력을 현장에서 확인한다.",
    },
    {
        "sample_id": "failure-response-209",
        "zone_id": "gh-01-dry-room",
        "growth_stage": "drying",
        "failure_type": "dehumidifier_readback_loss",
        "state_summary": "dehumidifier readback이 사라져 실제 제습 상태와 품질 보호 상태를 확인할 수 없다.",
        "faults": ["dehumidifier_readback_loss", "dry_room_execution_unknown"],
        "last_action": "pause_automation",
        "follow_up_description": "제습기 실제 가동 여부와 건조실 습도 추세를 확인한다.",
    },
    {
        "sample_id": "failure-response-210",
        "zone_id": "gh-01-zone-b",
        "growth_stage": "nursery",
        "failure_type": "vent_motor_timeout_repeated",
        "state_summary": "vent motor timeout이 반복돼 개방 상태를 더 이상 신뢰할 수 없다.",
        "faults": ["vent_timeout_repeated", "vent_position_unknown"],
        "last_action": "adjust_vent",
        "follow_up_description": "vent 실제 개방 상태와 motor fault 여부를 확인한다.",
    },
]


def main() -> None:
    safety_rows = [
        build_safety_row(**case) for case in WORKER_PRESENT_CASES + MANUAL_OVERRIDE_SAFE_MODE_CASES
    ]
    failure_rows = [build_failure_row(**case) for case in FAILURE_CASES]
    write_jsonl(OUTPUT_SAFETY, safety_rows)
    write_jsonl(OUTPUT_FAILURE, failure_rows)
    print(f"safety_rows: {len(safety_rows)}")
    print(f"failure_rows: {len(failure_rows)}")
    print(f"total_rows: {len(safety_rows) + len(failure_rows)}")


if __name__ == "__main__":
    main()
