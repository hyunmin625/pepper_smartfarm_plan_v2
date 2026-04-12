#!/usr/bin/env python3
"""Generate targeted batch12 training samples for failure safe-mode and evidence gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FAILURE_OUTPUT = REPO_ROOT / "data" / "examples" / "failure_response_samples_batch11.jsonl"
STATE_OUTPUT = REPO_ROOT / "data" / "examples" / "state_judgement_samples_batch12.jsonl"

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
    "pepper-climate-001": "RAG-SRC-005",
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


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


def make_failure_sample(
    sample_number: int,
    growth_stage: str,
    zone_id: str,
    failure_type: str,
    state_summary: str,
    active_faults: list[str],
    last_action: str,
    retrieved_context: list[str],
    situation_summary: str,
    diagnosis: list[str],
    safe_target_id: str,
    operator_id: str,
    follow_up_description: str,
) -> dict[str, Any]:
    sample_id = f"failure-response-{sample_number:03d}"
    prefix = sample_id.replace("failure-response", "fail11")
    return {
        "sample_id": sample_id,
        "task_type": "failure_response",
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": growth_stage,
            "zone_id": zone_id,
            "failure_type": failure_type,
            "state_summary": state_summary,
            "active_faults": active_faults,
            "last_action": last_action,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": situation_summary,
            "risk_level": "critical",
            "diagnosis": diagnosis,
            "recommended_actions": [
                action(
                    prefix,
                    1,
                    "enter_safe_mode",
                    "system",
                    safe_target_id,
                    "critical",
                    "핵심 급수 또는 건조 경로 상태를 확정할 수 없으므로 자동 제어를 즉시 안전 모드로 전환한다.",
                    "실행 여부가 불명확한 상태에서 자동 명령이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    prefix,
                    2,
                    "request_human_check",
                    "operator",
                    operator_id,
                    "high",
                    "현장에서 전원, 통신, 실제 장치 상태를 확인해 복구 조건을 확정한다.",
                    "수동 대응으로 실제 상태를 빠르게 확인할 수 있다.",
                    0,
                ),
            ],
            "fallback_mode": "safe_mode",
            "follow_up": [follow_up("device_readback", 5, follow_up_description)],
            "confidence": 0.91,
            "retrieval_coverage": "sufficient",
            "citations": [citation(chunk_id) for chunk_id in retrieved_context],
        },
    }


def make_evidence_sample(
    sample_number: int,
    task_type: str,
    growth_stage: str,
    zone_id: str,
    state_summary: str,
    active_constraints: list[str],
    retrieved_context: list[str],
    situation_summary: str,
    diagnosis: list[str],
    automation_target_id: str,
    operator_id: str,
    follow_up_description: str,
) -> dict[str, Any]:
    sample_id = f"state-judgement-{sample_number:03d}"
    prefix = sample_id.replace("state-judgement", "state12")
    return {
        "sample_id": sample_id,
        "task_type": task_type,
        "input": {
            "farm_id": "demo-farm",
            "growth_stage": growth_stage,
            "zone_id": zone_id,
            "state_summary": state_summary,
            "active_constraints": active_constraints,
            "retrieved_context": retrieved_context,
        },
        "preferred_output": {
            "situation_summary": situation_summary,
            "risk_level": "unknown",
            "diagnosis": diagnosis,
            "recommended_actions": [
                action(
                    prefix,
                    1,
                    "pause_automation",
                    "system",
                    automation_target_id,
                    "high",
                    "근권 또는 양액 판단 근거가 복구될 때까지 자동 제어를 일시 보류한다.",
                    "불충분한 근거에서 관수·양액 명령이 누적되는 것을 막는다.",
                    0,
                ),
                action(
                    prefix,
                    2,
                    "request_human_check",
                    "operator",
                    operator_id,
                    "medium",
                    "수동 측정과 센서 상태를 함께 확인해 실제 이상과 계측 문제를 구분한다.",
                    "근거 복구 전까지 보수적으로 운영할 수 있다.",
                    0,
                ),
            ],
            "requires_human_approval": False,
            "approval_reason": None,
            "follow_up": [follow_up("sensor_recheck", 5, follow_up_description)],
            "confidence": 0.6,
            "retrieval_coverage": "partial",
            "citations": [citation(chunk_id) for chunk_id in retrieved_context],
        },
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def build_failure_samples() -> list[dict[str, Any]]:
    specs = [
        (
            31,
            "fruit_set",
            "gh-01-zone-a",
            "communication_loss",
            "관수 펌프 통신이 끊겨 마지막 펄스 실행 여부와 현재 급수 상태를 확인할 수 없다.",
            ["irrigation_pump_comm_loss", "pulse_execution_unknown"],
            "short_irrigation",
            ["pepper-rootzone-001", "pepper-agent-001"],
            "관수 펌프 통신 손실로 실제 급수 상태를 확정할 수 없어 자동 급수는 즉시 안전 모드로 전환해야 한다.",
            [
                "핵심 급수 경로의 통신 손실은 실제 실행 여부를 확정할 수 없게 만든다.",
                "이 경우 pause_automation만으로는 부족하고 safe mode와 현장 확인이 필요하다.",
            ],
            "gh-01-zone-a-irrigation-control",
            "irrigation-manager",
            "관수 펌프 전원과 실제 급수 상태를 확인한다.",
        ),
        (
            32,
            "fruit_expansion",
            "gh-01-water-room",
            "readback_mismatch",
            "원수 메인 밸브 open 명령 뒤 readback이 돌아오지 않아 공급 경로 상태를 확정할 수 없다.",
            ["source_water_valve_readback_missing"],
            "adjust_fertigation",
            ["pepper-agent-001"],
            "원수 메인 밸브 readback 불가 상태라 급수 경로를 신뢰할 수 없어 급수 계통을 안전 모드로 전환해야 한다.",
            [
                "원수 메인 밸브 상태를 모르면 관수와 양액 경로 전체가 불확실해진다.",
                "급수 경로 불확실 상태에서는 자동 명령을 누적하면 안 된다.",
            ],
            "gh-01-water-room-control",
            "facility-manager",
            "원수 메인 밸브 실제 개폐 상태와 수동 급수 가능 여부를 확인한다.",
        ),
        (
            33,
            "harvest",
            "dry-room-1",
            "communication_loss",
            "건조실 dehumidifier와 circulation fan 상태 태그가 동시에 끊겨 장치 제어 상태를 읽을 수 없다.",
            ["dry-room-comm-loss", "device_status_unknown"],
            "pause_automation",
            ["pepper-house-drying-hygiene-001", "pepper-agent-001"],
            "건조실 장치 상태를 읽을 수 없어 자동 건조 제어를 유지하면 품질 손상이 커져 즉시 안전 모드가 필요하다.",
            [
                "건조실 장치 상태 미확인은 품질 편차와 재흡습 위험을 즉시 키운다.",
                "건조 lot는 현장 확인 전까지 자동 제어를 중단해야 한다.",
            ],
            "dry-room-control",
            "storage-manager",
            "건조실 장치 전원과 네트워크, lot 상태를 확인한다.",
        ),
        (
            34,
            "fruit_expansion",
            "gh-01-zone-c",
            "irrigation_readback_mismatch",
            "관수 매니폴드 메인 밸브 open 후 readback은 계속 closed로 남아 실제 급수가 불확실하다.",
            ["irrigation_valve_readback_mismatch"],
            "short_irrigation",
            ["pepper-rootzone-001", "pepper-agent-001"],
            "관수 메인 밸브 readback 불일치로 실제 급수 여부를 확인할 수 없어 자동 급수를 안전 모드로 전환해야 한다.",
            [
                "핵심 관수 밸브 readback 불일치는 실제 급수 실행 여부를 불명확하게 만든다.",
                "이 구간에서는 수동 확인 전 자동 관수를 멈춰야 한다.",
            ],
            "gh-01-zone-c-irrigation-control",
            "irrigation-manager",
            "매니폴드 압력과 실제 밸브 개폐 상태를 확인한다.",
        ),
        (
            35,
            "fruit_set",
            "gh-01-water-room",
            "source_water_low_pressure",
            "원수 압력 lock이 반복 재발해 후속 급수 실행 여부와 공급 안정성을 신뢰할 수 없다.",
            ["low_pressure_lock", "source_water_unstable"],
            "pause_automation",
            ["pepper-agent-001", "pepper-rootzone-001"],
            "원수 압력 lock 반복으로 급수 경로 안정성을 신뢰할 수 없어 급수 계통을 안전 모드로 전환해야 한다.",
            [
                "원수 저압 반복은 급수 누락과 불완전 관수 위험을 동시에 만든다.",
                "재발형 lock 상태에서는 수동 확인 전 자동 급수를 재개하면 안 된다.",
            ],
            "source-water-control",
            "facility-manager",
            "원수 압력, 라인 상태, 예비 급수 가능 여부를 확인한다.",
        ),
        (
            36,
            "fruiting",
            "gh-01-zone-b",
            "readback_mismatch",
            "양액 공급 메인 밸브 readback이 지연되고 최근 recipe 실행 ack도 불안정해 실제 공급 경로가 불명확하다.",
            ["fertigation_main_valve_readback_mismatch", "recipe_ack_unstable"],
            "adjust_fertigation",
            ["pepper-hydroponic-001", "pepper-agent-001"],
            "양액 공급 경로 readback이 불안정해 실제 공급 상태를 확정할 수 없어 양액 계통을 안전 모드로 전환해야 한다.",
            [
                "양액 공급 readback 불일치는 실제 공급 여부를 확정하지 못하게 만든다.",
                "양액 계통은 수동 확인 전 safe mode로 전환하는 편이 안전하다.",
            ],
            "gh-01-zone-b-fertigation-control",
            "fertigation-manager",
            "메인 밸브 실제 개폐와 recipe 실행 상태를 확인한다.",
        ),
    ]
    return [make_failure_sample(*spec) for spec in specs]


def build_evidence_samples() -> list[dict[str, Any]]:
    specs = [
        (
            96,
            "rootzone_diagnosis",
            "fruit_expansion",
            "gh-01-zone-a",
            "배지 함수율은 높게 보이지만 drain 센서가 stale이라 실제 배액 회복 여부를 판단할 수 없다.",
            ["rootzone_evidence_incomplete", "drain_sensor_stale"],
            ["pepper-rootzone-001", "pepper-agent-001"],
            "배액 근거가 stale이라 현재 근권 상태를 확정할 수 없어 자동 근권 판단을 보류해야 한다.",
            [
                "drain 센서 stale 상태에서는 과습과 정상 회복을 구분할 수 없다.",
                "근거가 복구되기 전까지는 자동 관수 판단을 보수적으로 유지해야 한다.",
            ],
            "gh-01-zone-a-rootzone-control",
            "irrigation-manager",
            "배액 측정과 수동 배지 상태를 함께 확인한다.",
        ),
        (
            97,
            "rootzone_diagnosis",
            "fruit_set",
            "gh-01-zone-b",
            "slab 함수율 센서가 missing이라 최근 EC 상승이 실제 건조 스트레스인지 센서 공백인지 판단할 수 없다.",
            ["rootzone_evidence_incomplete", "slab_wc_missing"],
            ["pepper-rootzone-001"],
            "핵심 함수율 센서가 missing이라 근권 스트레스 여부를 확정할 수 없어 자동 판단을 보류해야 한다.",
            [
                "함수율 센서 공백 상태에서는 실제 건조와 계측 누락을 구분할 수 없다.",
                "자동 관수나 양액 조정보다 근거 복구가 먼저다.",
            ],
            "gh-01-zone-b-rootzone-control",
            "duty-manager",
            "대체 함수율 측정과 센서 복구 여부를 확인한다.",
        ),
        (
            98,
            "rootzone_diagnosis",
            "fruiting",
            "gh-01-zone-c",
            "drain EC 센서가 flatline으로 고정돼 염류 집적 여부를 배액 데이터로 판단할 수 없다.",
            ["fertigation_evidence_incomplete", "drain_sensor_flatline"],
            ["pepper-rootzone-001", "pepper-hydroponic-001"],
            "배액 EC 근거가 flatline이라 염류 집적 여부를 확정할 수 없어 자동 근권 판단을 보류해야 한다.",
            [
                "flatline 센서는 실제 배액 변화를 반영하지 못한다.",
                "이 상태에서는 염류 집적과 정상 범위를 구분하지 못한다.",
            ],
            "gh-01-zone-c-rootzone-control",
            "fertigation-manager",
            "배액 EC 수동 측정과 센서 상태를 확인한다.",
        ),
        (
            99,
            "rootzone_diagnosis",
            "nursery",
            "gh-01-zone-a",
            "활착기 block 간 함수율 차이가 보이지만 일부 block 센서가 calibration drift라 실제 편차를 확정할 수 없다.",
            ["rootzone_evidence_incomplete", "core_sensor_fault"],
            ["pepper-rootzone-001", "pepper-agent-001"],
            "센서 보정 drift로 block 간 함수율 편차를 확정할 수 없어 자동 관수 판단을 보류해야 한다.",
            [
                "보정 drift가 있으면 block 간 실제 편차를 센서만으로 판단할 수 없다.",
                "활착기에는 보수적으로 수동 확인을 먼저 해야 한다.",
            ],
            "gh-01-zone-a-rootzone-control",
            "nursery-manager",
            "대표 block 수동 측정과 센서 보정 상태를 확인한다.",
        ),
        (
            100,
            "nutrient_risk",
            "fruit_set",
            "gh-01-zone-b",
            "급액 EC 조정 직전 drain 센서와 slab 센서가 동시에 stale이라 현재 양분 농도 반응을 판단할 수 없다.",
            ["fertigation_evidence_incomplete", "drain_sensor_stale", "core_sensor_fault"],
            ["pepper-hydroponic-001", "pepper-agent-001"],
            "양액 반응 근거가 stale이라 현재 양분 상태를 확정할 수 없어 자동 양액 조정을 보류해야 한다.",
            [
                "배액과 slab 센서가 동시에 stale이면 현재 농도 반응을 신뢰할 수 없다.",
                "이 경우 양액 recipe 자동 조정보다 수동 확인이 먼저다.",
            ],
            "gh-01-zone-b-fertigation-control",
            "fertigation-manager",
            "급액·배액 수동 측정과 센서 통신 상태를 함께 확인한다.",
        ),
        (
            101,
            "nutrient_risk",
            "fruit_expansion",
            "gh-01-zone-c",
            "drain pH 센서 calibration error와 feed EC drift가 같이 보여 양액 불균형 여부를 확정할 수 없다.",
            ["fertigation_evidence_incomplete", "core_sensor_fault"],
            ["pepper-hydroponic-001"],
            "배액 pH 근거가 무너져 양액 불균형 여부를 확정할 수 없어 자동 양액 조정을 보류해야 한다.",
            [
                "배액 pH calibration error 상태에서는 양액 불균형을 확정하기 어렵다.",
                "근거 복구 전에는 recipe 자동 변경을 보수적으로 제한해야 한다.",
            ],
            "gh-01-zone-c-fertigation-control",
            "fertigation-manager",
            "배액 pH 수동 측정과 보정 상태를 확인한다.",
        ),
        (
            102,
            "nutrient_risk",
            "vegetative_growth",
            "gh-01-zone-a",
            "신엽이 옅어졌지만 drain EC 센서는 missing이고 최근 배액률도 기록이 끊겨 양분 희석 여부를 판단할 수 없다.",
            ["fertigation_evidence_incomplete", "drain_sensor_missing"],
            ["pepper-hydroponic-001", "pepper-agent-001"],
            "배액 근거가 missing이라 양분 희석 여부를 확정할 수 없어 자동 양액 조정을 보류해야 한다.",
            [
                "신엽 변화만으로는 결핍과 계측 공백을 구분할 수 없다.",
                "배액 데이터가 비면 자동 recipe 조정보다 수동 확인이 우선이다.",
            ],
            "gh-01-zone-a-fertigation-control",
            "duty-manager",
            "배액률과 drain EC 수동 측정을 확인한다.",
        ),
        (
            103,
            "nutrient_risk",
            "fruiting",
            "gh-01-zone-b",
            "slab EC는 오르지만 배액량 집계가 누락돼 염류 집적과 단순 계측 누락을 구분할 수 없다.",
            ["fertigation_evidence_incomplete", "drain_sensor_missing"],
            ["pepper-rootzone-001", "pepper-hydroponic-001"],
            "배액량 근거가 누락돼 염류 집적 여부를 확정할 수 없어 자동 양액 판단을 보류해야 한다.",
            [
                "slab EC 상승만으로는 실제 염류 집적을 확정할 수 없다.",
                "배액량 근거가 없으면 근권 상태를 보수적으로 해석해야 한다.",
            ],
            "gh-01-zone-b-fertigation-control",
            "fertigation-manager",
            "배액량과 slab 수동 측정을 함께 확인한다.",
        ),
    ]
    return [make_evidence_sample(*spec) for spec in specs]


def main() -> None:
    failure_rows = build_failure_samples()
    evidence_rows = build_evidence_samples()
    write_jsonl(FAILURE_OUTPUT, failure_rows)
    write_jsonl(STATE_OUTPUT, evidence_rows)
    print(f"failure_output,{FAILURE_OUTPUT.as_posix()},{len(failure_rows)}")
    print(f"state_output,{STATE_OUTPUT.as_posix()},{len(evidence_rows)}")


if __name__ == "__main__":
    main()
