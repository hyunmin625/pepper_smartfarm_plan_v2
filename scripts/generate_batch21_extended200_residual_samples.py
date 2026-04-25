#!/usr/bin/env python3
"""Generate Batch21A/B corrective samples for ds_v11 extended200 residuals.

Batch21A focuses on risk rubric boundaries. Batch21B focuses on required
action types under evidence gaps. Batch21C closes robot task enum/target
exactness that also appears in synthetic shadow day0 residuals. These samples
are future dataset scale-up seeds; they do not reopen fine-tune submit by
themselves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

BATCH21A_STATE_OUTPUT = (
    REPO_ROOT / "data/examples/state_judgement_samples_batch21a_risk_rubric_core.jsonl"
)
BATCH21A_FAILURE_OUTPUT = (
    REPO_ROOT / "data/examples/failure_response_samples_batch21a_risk_rubric_core.jsonl"
)
BATCH21A_FORBIDDEN_OUTPUT = (
    REPO_ROOT / "data/examples/forbidden_action_samples_batch21a_risk_rubric_core.jsonl"
)
BATCH21B_ACTION_OUTPUT = (
    REPO_ROOT / "data/examples/action_recommendation_samples_batch21b_required_actions.jsonl"
)
BATCH21B_STATE_OUTPUT = (
    REPO_ROOT / "data/examples/state_judgement_samples_batch21b_required_actions.jsonl"
)
BATCH21B_FAILURE_OUTPUT = (
    REPO_ROOT / "data/examples/failure_response_samples_batch21b_required_actions.jsonl"
)
BATCH21C_ROBOT_OUTPUT = (
    REPO_ROOT / "data/examples/robot_task_samples_batch21c_robot_contract_exactness.jsonl"
)

DOC_IDS = {
    "pepper-agent-001": "RAG-SRC-AGENT",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-crop-env-thresholds-001": "RAG-SRC-010",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
    "pepper-house-safety-001": "RAG-SRC-002",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-plantfactory-healing-001": "RAG-SRC-001",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-shading-strategy-001": "RAG-SRC-001",
}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def citations(chunk_ids: list[str]) -> list[dict[str, str]]:
    return [
        {"chunk_id": chunk_id, "document_id": DOC_IDS[chunk_id]}
        for chunk_id in chunk_ids
    ]


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
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action_id": f"{prefix}-act-{index:03d}",
        "action_type": action_type,
        "target": {"target_type": target_type, "target_id": target_id},
        "risk_level": risk_level,
        "approval_required": approval_required,
        "reason": reason,
        "expected_effect": expected_effect,
        "cooldown_minutes": cooldown_minutes,
    }
    if parameters is not None:
        payload["parameters"] = parameters
    return payload


def robot_task(
    prefix: str,
    index: int,
    task_type: str,
    target_type: str,
    target_id: str,
    priority: str,
    reason: str,
    *,
    candidate_id: str,
    approval_required: bool = True,
) -> dict[str, Any]:
    return {
        "task_id": f"{prefix}-task-{index:03d}",
        "task_type": task_type,
        "priority": priority,
        "approval_required": approval_required,
        "reason": reason,
        "target": {"target_type": target_type, "target_id": target_id},
        "candidate_id": candidate_id,
    }


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


def preferred_output(
    *,
    situation_summary: str,
    risk_level: str,
    diagnosis: list[str],
    recommended_actions: list[dict[str, Any]],
    follow_ups: list[dict[str, Any]],
    citation_ids: list[str],
    skipped_actions: list[dict[str, str]] | None = None,
    requires_human_approval: bool = False,
    confidence: float = 0.74,
    retrieval_coverage: str = "sufficient",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "situation_summary": situation_summary,
        "risk_level": risk_level,
        "diagnosis": diagnosis,
        "recommended_actions": recommended_actions,
        "requires_human_approval": requires_human_approval,
        "follow_up": follow_ups,
        "confidence": confidence,
        "retrieval_coverage": retrieval_coverage,
        "citations": citations(citation_ids),
    }
    if skipped_actions:
        payload["skipped_actions"] = skipped_actions
    return payload


def sample(
    sample_id: str,
    task_type: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "task_type": task_type,
        "input": input_payload,
        "preferred_output": output_payload,
    }


def evidence_unknown_rows() -> list[dict[str, Any]]:
    specs = [
        {
            "sample_id": "state-judgement-batch21a-evidence-unknown-001",
            "task_type": "rootzone_diagnosis",
            "zone_id": "gh-01-zone-a",
            "growth_stage": "fruit_expansion",
            "summary": "GT Master A구역에서 slab WC 센서가 missing이고 배액률 기록도 비어 있는데 잎 처짐 메모만 1회 남아 있다.",
            "constraints": ["rootzone_evidence_incomplete", "slab_wc_missing", "drain_volume_missing"],
            "operator": "rootzone-manager",
            "context": ["pepper-rootzone-001", "pepper-agent-001"],
        },
        {
            "sample_id": "state-judgement-batch21a-evidence-unknown-002",
            "task_type": "nutrient_risk",
            "zone_id": "gh-01-zone-b",
            "growth_stage": "fruit_set",
            "summary": "B구역 급액 EC는 정상처럼 보이지만 drain EC가 stale이고 drain pH가 flatline이라 양액 판단 근거가 불완전하다.",
            "constraints": ["fertigation_evidence_incomplete", "drain_sensor_stale", "drain_sensor_flatline"],
            "operator": "fertigation-manager",
            "context": ["pepper-hydroponic-001", "pepper-agent-001"],
        },
        {
            "sample_id": "state-judgement-batch21a-evidence-unknown-003",
            "task_type": "rootzone_diagnosis",
            "zone_id": "gh-01-zone-c",
            "growth_stage": "flowering",
            "summary": "C구역 배지 함수율 센서가 calibration error이고 수동 측정값도 없어 건조/과습 어느 쪽인지 단정할 수 없다.",
            "constraints": ["rootzone_evidence_incomplete", "core_sensor_fault", "manual_measurement_missing"],
            "operator": "rootzone-manager",
            "context": ["pepper-rootzone-001", "pepper-agent-001"],
        },
        {
            "sample_id": "state-judgement-batch21a-evidence-unknown-004",
            "task_type": "nutrient_risk",
            "zone_id": "gh-01-zone-d",
            "growth_stage": "fruit_expansion",
            "summary": "D구역 배액 EC/pH와 drain volume이 동시에 누락되어 recipe 변경 판단에 쓸 근거가 없다.",
            "constraints": ["fertigation_evidence_incomplete", "drain_ec_missing", "drain_ph_missing", "drain_volume_missing"],
            "operator": "fertigation-manager",
            "context": ["pepper-hydroponic-001", "pepper-agent-001"],
        },
    ]
    rows: list[dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        sid = spec["sample_id"]
        rows.append(
            sample(
                sid,
                spec["task_type"],
                {
                    "farm_id": "demo-farm",
                    "zone_id": spec["zone_id"],
                    "growth_stage": spec["growth_stage"],
                    "state_summary": spec["summary"],
                    "active_constraints": spec["constraints"],
                    "source_eval_ids": ["action-eval-007", "pepper-eval-049"],
                    "retrieved_context": spec["context"],
                },
                preferred_output(
                    situation_summary="근권/양액 근거가 불완전하므로 high로 과호출하지 말고 unknown으로 둔 뒤 자동화를 멈춘다.",
                    risk_level="unknown",
                    diagnosis=[
                        "핵심 센서나 배액 근거가 비어 있으면 건조·과습·염류 중 어느 쪽인지 단정할 수 없다.",
                        "이 slice는 근거 공백을 high로 올리는 대신 unknown + pause_automation + request_human_check로 고정한다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21a-evidence-{i:03d}",
                            1,
                            "pause_automation",
                            "system",
                            f"{spec['zone_id']}-auto-control",
                            "unknown",
                            "근권/양액 판단 근거가 복구될 때까지 자동 제어를 보류한다.",
                            "근거 없는 관수·양액 조정이 누적되는 것을 막는다.",
                            0,
                        ),
                        action(
                            f"batch21a-evidence-{i:03d}",
                            2,
                            "request_human_check",
                            "operator",
                            spec["operator"],
                            "unknown",
                            "누락된 센서값과 수동 측정값을 현장에서 확인한다.",
                            "unknown 상태를 실제 원인으로 분리할 수 있다.",
                            0,
                        ),
                    ],
                    skipped_actions=[
                        {
                            "action_type": "adjust_fertigation",
                            "reason": "배액/근권 근거가 비어 있으면 자동 양액 조정을 바로 실행하면 안 된다.",
                        },
                        {
                            "action_type": "short_irrigation",
                            "reason": "건조·과습 방향이 불확실한 상태에서 reflex 관수는 금지한다.",
                        },
                    ],
                    requires_human_approval=False,
                    follow_ups=[
                        follow_up("sensor_recheck", 10, "누락된 센서값과 수동 측정값을 복구한다.")
                    ],
                    citation_ids=spec["context"],
                    retrieval_coverage="partial",
                    confidence=0.68,
                ),
            )
        )
    return rows


def climate_high_rows() -> list[dict[str, Any]]:
    specs = [
        {
            "sample_id": "state-judgement-batch21a-climate-high-001",
            "task_type": "climate_risk",
            "zone_id": "gh-01-zone-nursery-a",
            "growth_stage": "nursery",
            "summary": "Delta 6.5 nursery A구역에서 post_sunset 이후 humidity가 94%로 유지되고 leaf wet 시간이 160분을 넘었다.",
            "constraints": ["delta65_nursery_leaf_wet_watch", "post_sunset_humidity_high"],
            "context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
            "source_eval_ids": ["seasonal-eval-006", "seasonal-eval-010"],
        },
        {
            "sample_id": "state-judgement-batch21a-climate-high-002",
            "task_type": "climate_risk",
            "zone_id": "gh-01-zone-nursery-b",
            "growth_stage": "nursery",
            "summary": "Delta 6.5 nursery B구역에서 야간 humidity가 높고 잎 젖음 메모가 2회 연속이며 보온커튼은 닫혀 있다.",
            "constraints": ["delta65_nursery_leaf_wet_watch", "night_heat_retention_mode"],
            "context": ["pepper-plantfactory-healing-001", "pepper-agent-001"],
            "source_eval_ids": ["seasonal-eval-011", "seasonal-eval-013"],
        },
        {
            "sample_id": "state-judgement-batch21a-climate-high-003",
            "task_type": "climate_risk",
            "zone_id": "gh-01-zone-flower-a",
            "growth_stage": "flowering",
            "summary": "개화기 A구역 상단 기온이 33℃이고 PAR가 920까지 올라 꽃가루 활력 저하와 낙화 위험이 겹친다.",
            "constraints": ["flowering_heat_stress", "high_par"],
            "context": ["pepper-climate-001", "pepper-shading-strategy-001"],
            "source_eval_ids": ["pepper-eval-021", "pepper-eval-022"],
        },
        {
            "sample_id": "state-judgement-batch21a-climate-high-004",
            "task_type": "climate_risk",
            "zone_id": "gh-01-zone-flower-b",
            "growth_stage": "flowering",
            "summary": "개화기 B구역에서 오후 고온이 32.5℃로 반복되고 차광률이 낮아 꽃 떨림 메모가 증가했다.",
            "constraints": ["flowering_heat_stress", "shade_under_target"],
            "context": ["pepper-climate-001", "pepper-shading-strategy-001"],
            "source_eval_ids": ["pepper-eval-023", "pepper-eval-056"],
        },
    ]
    rows: list[dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        rows.append(
            sample(
                spec["sample_id"],
                spec["task_type"],
                {
                    "farm_id": "demo-farm",
                    "zone_id": spec["zone_id"],
                    "growth_stage": spec["growth_stage"],
                    "state_summary": spec["summary"],
                    "active_constraints": spec["constraints"],
                    "source_eval_ids": spec["source_eval_ids"],
                    "retrieved_context": spec["context"],
                },
                preferred_output(
                    situation_summary="생육단계와 환경 조건이 겹쳐 high 위험으로 보고 알림과 현장 확인을 동시에 건다.",
                    risk_level="high",
                    diagnosis=[
                        "개화기 고온·강광 또는 육묘기 냉습·잎 젖음은 수량과 병해 리스크에 직접 연결된다.",
                        "이 slice는 medium으로 낮추면 운영자가 놓치기 쉬우므로 create_alert와 request_human_check를 같이 둔다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21a-climate-{i:03d}",
                            1,
                            "create_alert",
                            "zone",
                            spec["zone_id"],
                            "high",
                            "생육단계별 고위험 환경 신호를 운영자에게 즉시 알린다.",
                            "위험 이벤트를 shadow/operator review에 남긴다.",
                            5,
                        ),
                        action(
                            f"batch21a-climate-{i:03d}",
                            2,
                            "request_human_check",
                            "operator",
                            "climate-manager",
                            "medium",
                            "꽃 상태, 잎 젖음, 차광/보온 상태를 현장에서 확인한다.",
                            "자동 제어 전 현장 원인을 분리할 수 있다.",
                            0,
                        ),
                    ],
                    skipped_actions=[
                        {
                            "action_type": "adjust_vent",
                            "reason": "보온/풍속/작업자 상태 확인 없이 환기만 reflex로 열면 안 된다.",
                        }
                    ],
                    requires_human_approval=True,
                    follow_ups=[follow_up("trend_review", 20, "온습도·PAR·잎 젖음 추세를 재확인한다.")],
                    citation_ids=spec["context"],
                    confidence=0.78,
                ),
            )
        )
    return rows


def gt_master_high_rows() -> list[dict[str, Any]]:
    specs = [
        ("gh-01-zone-gt-a", "fruit_expansion", "새벽 WC가 63%까지 낮고 오후 잎 처짐이 3일 반복된다."),
        ("gh-01-zone-gt-b", "fruit_set", "dry-back이 19%까지 벌어지고 잎 처짐 메모가 오후마다 반복된다."),
        ("gh-01-zone-gt-c", "fruit_expansion", "배액률이 낮고 GT Master dry-back이 커지며 신초 탄력 저하가 함께 보인다."),
        ("gh-01-zone-gt-d", "fruit_set", "dual slab 중 한 줄만 WC가 급락하고 잎 처짐이 국소적으로 반복된다."),
    ]
    rows: list[dict[str, Any]] = []
    for i, (zone_id, stage, detail) in enumerate(specs, start=1):
        sid = f"state-judgement-batch21a-gtmaster-dryback-{i:03d}"
        rows.append(
            sample(
                sid,
                "rootzone_diagnosis",
                {
                    "farm_id": "demo-farm",
                    "zone_id": zone_id,
                    "growth_stage": stage,
                    "state_summary": f"GT Master {zone_id}에서 dry-back과 WC 이상이 겹친다. {detail}",
                    "active_constraints": ["gt_master_dryback_high", "repeated_afternoon_wilt"],
                    "source_eval_ids": ["blind-action-004", "blind-expert-010", "pepper-eval-003", "pepper-eval-018"],
                    "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
                },
                preferred_output(
                    situation_summary="GT Master dry-back과 반복 잎 처짐은 high 근권 위험으로 보고 먼저 알림과 현장 확인을 건다.",
                    risk_level="high",
                    diagnosis=[
                        "GT Master dry-back이 크고 WC/잎 처짐이 같이 움직이면 단순 관수 부족으로 단정하면 안 된다.",
                        "이 slice는 observe_only나 adjust_fertigation 단독이 아니라 create_alert + request_human_check가 필수다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21a-gtmaster-{i:03d}",
                            1,
                            "create_alert",
                            "zone",
                            zone_id,
                            "high",
                            "GT Master dry-back과 반복 잎 처짐을 근권 고위험 이벤트로 기록한다.",
                            "operator review와 shadow residual 추적에 남긴다.",
                            5,
                        ),
                        action(
                            f"batch21a-gtmaster-{i:03d}",
                            2,
                            "request_human_check",
                            "operator",
                            "rootzone-manager",
                            "medium",
                            "대표 slab WC, drain rate, 급액/배액 EC/pH, 실제 잎 처짐을 현장에서 확인한다.",
                            "관수 부족·염류·센서 drift를 분리할 수 있다.",
                            0,
                        ),
                    ],
                    skipped_actions=[
                        {
                            "action_type": "adjust_fertigation",
                            "reason": "dry-back + 잎 처짐 반복 상태에서 recipe/관수 조정을 단독 실행하면 원인 확인을 건너뛴다.",
                        }
                    ],
                    requires_human_approval=True,
                    follow_ups=[follow_up("visual_inspection", 15, "대표 slab와 작물 잎 처짐을 현장에서 확인한다.")],
                    citation_ids=["pepper-rootzone-001", "pepper-hydroponic-001"],
                    confidence=0.8,
                ),
            )
        )
    return rows


def batch21a_failure_rows() -> list[dict[str, Any]]:
    specs = [
        ("irrigation-pump-a", "irrigation_pump_comm_loss", "관수 펌프 A ack가 사라지고 valve readback이 마지막 명령과 맞지 않는다."),
        ("source-water-room", "source_water_pump_comm_loss", "원수 펌프 통신 손실과 압력 readback 정체가 동시에 발생했다."),
        ("irrigation-valve-b", "irrigation_valve_readback_mismatch", "B구역 관수밸브 close 명령 후 readback이 open으로 남아 있다."),
        ("fertigation-mixer-a", "fertigation_mixer_ack_loss", "양액기 mixer ack가 끊기고 마지막 recipe write가 확인되지 않는다."),
    ]
    rows: list[dict[str, Any]] = []
    for i, (target_id, fault, detail) in enumerate(specs, start=1):
        sid = f"failure-response-batch21a-safe-mode-{i:03d}"
        rows.append(
            sample(
                sid,
                "failure_response",
                {
                    "farm_id": "demo-farm",
                    "zone_id": "gh-01-water-zone",
                    "growth_stage": "fruit_expansion",
                    "failure_type": "communication_loss",
                    "state_summary": detail,
                    "active_faults": [fault],
                    "active_constraints": ["water_path_degraded", "automation_running"],
                    "source_eval_ids": ["failure-eval-001", "failure-eval-007", "failure-eval-009"],
                    "retrieved_context": ["pepper-agent-001", "pepper-house-safety-001"],
                },
                preferred_output(
                    situation_summary="급수/양액 경로의 ack/readback 손실은 critical 장애로 보고 safe mode와 현장 확인을 동시에 건다.",
                    risk_level="critical",
                    diagnosis=[
                        "water path의 통신/ack/readback이 깨지면 현재 밸브·펌프 상태를 신뢰할 수 없다.",
                        "이 경우 단순 retry보다 enter_safe_mode + request_human_check가 먼저다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21a-failure-{i:03d}",
                            1,
                            "enter_safe_mode",
                            "system",
                            target_id,
                            "critical",
                            "water path 상태가 확인될 때까지 자동 제어를 안전 상태로 전환한다.",
                            "확인되지 않은 장치 동작을 멈춘다.",
                            0,
                        ),
                        action(
                            f"batch21a-failure-{i:03d}",
                            2,
                            "create_alert",
                            "zone",
                            "gh-01-water-zone",
                            "critical",
                            "ack/readback 손실을 운영자에게 즉시 알린다.",
                            "장애 대응을 감사 로그와 operator review에 남긴다.",
                            0,
                        ),
                        action(
                            f"batch21a-failure-{i:03d}",
                            3,
                            "request_human_check",
                            "operator",
                            "water-system-manager",
                            "critical",
                            "현장 장치 위치, PLC 통신, readback 상태를 직접 확인한다.",
                            "safe mode 해제 조건을 판단할 수 있다.",
                            0,
                        ),
                    ],
                    requires_human_approval=False,
                    follow_ups=[follow_up("device_readback", 5, "장치 상태와 PLC readback을 재확인한다.")],
                    citation_ids=["pepper-agent-001", "pepper-house-safety-001"],
                    confidence=0.93,
                ),
            )
        )
    return rows


def batch21a_forbidden_rows() -> list[dict[str, Any]]:
    specs = [
        ("manual-override-fertigation", "adjust_fertigation", "manual_override가 active인데 양액 recipe 변경 요청이 들어왔다.", "critical"),
        ("safe-mode-vent", "adjust_vent", "safe_mode latch가 active인데 환기창 추가 개방 명령이 제안됐다.", "critical"),
        ("worker-robot", "create_robot_task", "작업자 출입 로그가 열린 상태에서 로봇 작업 재시작 요청이 들어왔다.", "critical"),
        ("wind-lock-vent", "adjust_vent", "강풍 lock이 active인데 환기창 개방률 상향 요청이 들어왔다.", "high"),
    ]
    rows: list[dict[str, Any]] = []
    for i, (key, blocked, summary, risk) in enumerate(specs, start=1):
        rows.append(
            sample(
                f"forbidden-action-batch21a-{key}-{i:03d}",
                "forbidden_action",
                {
                    "farm_id": "demo-farm",
                    "zone_id": f"gh-01-zone-forbid-{i}",
                    "growth_stage": "fruit_expansion",
                    "proposed_action": blocked,
                    "state_summary": summary,
                    "active_constraints": [key.replace("-", "_")],
                    "source_eval_ids": ["forbidden-eval-008", "forbidden-eval-011", "forbidden-eval-012", "forbidden-eval-014"],
                    "retrieved_context": ["pepper-agent-001"],
                },
                {
                    "decision": "block",
                    "risk_level": risk,
                    "blocked_action_type": blocked,
                    "reason": "안전/운영 lock이 active인 동안 제안된 장치 제어를 실행하면 안 된다.",
                    "required_follow_up": [
                        follow_up("operator_confirm", 0, "lock/override/작업자 상태가 해제됐는지 확인한다.")
                    ],
                    "citations": citations(["pepper-agent-001"]),
                },
            )
        )
    return rows


def batch21b_action_rows() -> list[dict[str, Any]]:
    specs = [
        ("drain-gap", "gh-01-zone-a", "fruit_expansion", "배액률과 drain pH가 비어 있는데 자동 양액 증량 제안이 생성됐다.", "adjust_fertigation"),
        ("wilt-gap", "gh-01-zone-b", "fruit_set", "잎 처짐 메모는 있지만 slab WC와 drain volume이 모두 없어 단기 관수 제안을 검증할 수 없다.", "short_irrigation"),
        ("vent-gap", "gh-01-zone-c", "flowering", "외기 풍속과 환기창 readback이 stale인데 환기창 개방 제안이 생성됐다.", "adjust_vent"),
        ("co2-gap", "gh-01-zone-d", "vegetative_growth", "CO2 센서가 flatline이고 환기 상태도 불명확한데 CO2 주입량 상향 제안이 생성됐다.", "adjust_co2"),
        ("heat-gap", "gh-01-zone-e", "flowering", "상단 기온 센서가 stale인데 고온 완화 장치 조합이 자동 제안됐다.", "adjust_shade"),
        ("nursery-gap", "gh-01-zone-nursery", "nursery", "Delta 6.5 block wet weight 기록이 없는데 정식 전 자동 관수 제안이 생성됐다.", "short_irrigation"),
        ("dryroom-gap", "dry-room-1", "harvest", "건조실 습도 센서가 missing인데 제습 강화 제안이 생성됐다.", "adjust_fan"),
        ("recipe-gap", "gh-01-zone-gt", "fruit_expansion", "급액 EC와 drain EC 차이가 비정상인데 수동 측정 없이 recipe 변경 제안이 생성됐다.", "adjust_fertigation"),
    ]
    rows: list[dict[str, Any]] = []
    for i, (key, zone_id, stage, summary, skipped) in enumerate(specs, start=1):
        sid = f"action-recommendation-batch21b-evidence-gap-{i:03d}"
        rows.append(
            sample(
                sid,
                "action_recommendation",
                {
                    "farm_id": "demo-farm",
                    "zone_id": zone_id,
                    "growth_stage": stage,
                    "state_summary": summary,
                    "active_constraints": ["evidence_gap", "automation_recommendation_pending"],
                    "source_eval_ids": ["action-eval-003", "action-eval-016", "action-eval-022", "pepper-eval-010"],
                    "retrieved_context": ["pepper-agent-001", "pepper-hydroponic-001"],
                },
                preferred_output(
                    situation_summary="근거 공백 상태에서는 reflex action을 금지하고 알림/확인/자동화 보류를 우선한다.",
                    risk_level="unknown",
                    diagnosis=[
                        "핵심 관측값이 비어 있으면 제안된 장치 제어가 맞는지 검증할 수 없다.",
                        "required_action_types_present residual을 줄이려면 pause_automation, create_alert, request_human_check를 명시해야 한다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21b-action-{i:03d}",
                            1,
                            "pause_automation",
                            "system",
                            f"{zone_id}-auto-control",
                            "unknown",
                            "근거가 복구될 때까지 해당 자동 제어 제안을 보류한다.",
                            "잘못된 reflex action 실행을 막는다.",
                            0,
                        ),
                        action(
                            f"batch21b-action-{i:03d}",
                            2,
                            "create_alert",
                            "zone",
                            zone_id,
                            "unknown",
                            "근거 공백 상태에서 제어 제안이 발생했음을 알린다.",
                            "operator review에 residual 원인을 남긴다.",
                            5,
                        ),
                        action(
                            f"batch21b-action-{i:03d}",
                            3,
                            "request_human_check",
                            "operator",
                            "duty-manager",
                            "unknown",
                            "누락된 센서값과 현장 상태를 확인한 뒤 제어 여부를 다시 판단한다.",
                            "근거 복구 후 안전한 제어로 전환할 수 있다.",
                            0,
                        ),
                    ],
                    skipped_actions=[
                        {
                            "action_type": skipped,
                            "reason": "근거 공백 상태에서 이 reflex action을 바로 실행하면 안 된다.",
                        }
                    ],
                    requires_human_approval=False,
                    follow_ups=[follow_up("sensor_recheck", 10, "누락된 핵심 관측값을 복구한다.")],
                    citation_ids=["pepper-agent-001", "pepper-hydroponic-001"],
                    retrieval_coverage="partial",
                    confidence=0.67,
                ),
            )
        )
    return rows


def batch21b_state_rows() -> list[dict[str, Any]]:
    specs = [
        ("state-judgement-batch21b-rootzone-gap-001", "rootzone_diagnosis", "gh-01-zone-rz-a", "GT Master 대표 slab 2개 중 하나만 WC가 있고 drain volume이 비어 있어 근권 stress 판단이 불완전하다.", ["rootzone_evidence_incomplete", "drain_volume_missing"]),
        ("state-judgement-batch21b-rootzone-gap-002", "rootzone_diagnosis", "gh-01-zone-rz-b", "배지 함수율 센서가 stale이고 잎 처짐 메모만 있어 과습/건조 방향을 단정할 수 없다.", ["rootzone_evidence_incomplete", "slab_wc_missing"]),
        ("state-judgement-batch21b-nutrient-gap-003", "nutrient_risk", "gh-01-zone-nu-a", "급액 pH는 정상이나 drain pH가 missing이고 EC probe calibration이 끝나지 않았다.", ["fertigation_evidence_incomplete", "drain_ph_missing"]),
        ("state-judgement-batch21b-nutrient-gap-004", "nutrient_risk", "gh-01-zone-nu-b", "recipe 변경 후 drain EC trend가 flatline이라 실제 염류 반응을 확인할 수 없다.", ["fertigation_evidence_incomplete", "drain_sensor_flatline"]),
    ]
    rows: list[dict[str, Any]] = []
    for i, (sid, task_type, zone_id, summary, constraints) in enumerate(specs, start=1):
        rows.append(
            sample(
                sid,
                task_type,
                {
                    "farm_id": "demo-farm",
                    "zone_id": zone_id,
                    "growth_stage": "fruit_expansion",
                    "state_summary": summary,
                    "active_constraints": constraints,
                    "source_eval_ids": ["pepper-eval-014", "edge-eval-012"],
                    "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
                },
                preferred_output(
                    situation_summary="근권/양액 evidence gap은 unknown으로 두고 request_human_check를 반드시 포함한다.",
                    risk_level="unknown",
                    diagnosis=[
                        "대표 slab, drain, EC/pH 중 핵심 근거가 빠지면 위험 방향을 단정할 수 없다.",
                        "이 residual slice는 action 누락 방지를 위해 pause_automation과 request_human_check를 함께 낸다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21b-state-{i:03d}",
                            1,
                            "pause_automation",
                            "system",
                            f"{zone_id}-auto-control",
                            "unknown",
                            "근거 공백이 해소될 때까지 자동 제어 판단을 보류한다.",
                            "불완전한 근거로 recipe/관수를 바꾸는 일을 막는다.",
                            0,
                        ),
                        action(
                            f"batch21b-state-{i:03d}",
                            2,
                            "request_human_check",
                            "operator",
                            "rootzone-manager",
                            "unknown",
                            "대표 slab와 배액 계측을 수동으로 확인한다.",
                            "unknown 판단을 실제 원인으로 좁힐 수 있다.",
                            0,
                        ),
                    ],
                    skipped_actions=[
                        {
                            "action_type": "adjust_fertigation",
                            "reason": "근거 공백 상태에서 자동 양액 조정을 실행하면 안 된다.",
                        }
                    ],
                    follow_ups=[follow_up("sensor_recheck", 10, "대표 slab와 drain 계측을 복구한다.")],
                    citation_ids=["pepper-rootzone-001", "pepper-hydroponic-001"],
                    retrieval_coverage="partial",
                    confidence=0.66,
                ),
            )
        )
    return rows


def batch21b_failure_rows() -> list[dict[str, Any]]:
    specs = [
        ("failure-response-batch21b-readback-gap-001", "gh-01-zone-a", "irrigation_valve_readback_mismatch", "관수밸브 close 명령 뒤 readback이 흔들리고 현장 압력 값이 비어 있다."),
        ("failure-response-batch21b-readback-gap-002", "gh-01-zone-b", "irrigation_pump_comm_loss", "관수 펌프 ack가 사라졌고 마지막 cycle 종료 확인이 없다."),
        ("failure-response-batch21b-dryroom-gap-003", "dry-room-1", "dry_room_comm_loss", "건조실 통신 손실과 reentry_pending이 겹쳐 자동 복귀 조건을 확인할 수 없다."),
        ("failure-response-batch21b-mixer-gap-004", "gh-01-zone-c", "fertigation_mixer_ack_loss", "양액기 mixer ack가 끊겼고 recipe write readback이 비어 있다."),
    ]
    rows: list[dict[str, Any]] = []
    for i, (sid, zone_id, fault, summary) in enumerate(specs, start=1):
        rows.append(
            sample(
                sid,
                "failure_response",
                {
                    "farm_id": "demo-farm",
                    "zone_id": zone_id,
                    "growth_stage": "fruit_expansion",
                    "failure_type": "readback_or_comm_loss",
                    "state_summary": summary,
                    "active_faults": [fault],
                    "active_constraints": ["device_evidence_gap", "automation_running"],
                    "source_eval_ids": ["failure-eval-003", "failure-eval-004", "failure-eval-005", "failure-eval-006", "failure-eval-011", "edge-eval-021"],
                    "retrieved_context": ["pepper-agent-001", "pepper-house-safety-001"],
                },
                preferred_output(
                    situation_summary="장치 readback/ack 공백은 critical 장애로 보고 safe mode, alert, human check를 모두 포함한다.",
                    risk_level="critical",
                    diagnosis=[
                        "장치 상태 근거가 비면 실행 결과를 확인할 수 없어 자동 제어를 계속하면 안 된다.",
                        "required_action_types_present residual을 줄이려면 enter_safe_mode, create_alert, request_human_check가 같이 필요하다.",
                    ],
                    recommended_actions=[
                        action(
                            f"batch21b-failure-{i:03d}",
                            1,
                            "enter_safe_mode",
                            "system",
                            f"{zone_id}-device-gate",
                            "critical",
                            "장치 상태 확인 전까지 자동 제어를 안전 상태로 전환한다.",
                            "확인되지 않은 장치 동작을 멈춘다.",
                            0,
                        ),
                        action(
                            f"batch21b-failure-{i:03d}",
                            2,
                            "create_alert",
                            "zone",
                            zone_id,
                            "critical",
                            "readback/ack 공백과 자동 제어 보류 상태를 운영자에게 알린다.",
                            "장애 대응과 operator review를 남긴다.",
                            0,
                        ),
                        action(
                            f"batch21b-failure-{i:03d}",
                            3,
                            "request_human_check",
                            "operator",
                            "device-manager",
                            "critical",
                            "장치 실제 위치, PLC ack, readback을 현장에서 확인한다.",
                            "safe mode 해제 여부를 판단할 수 있다.",
                            0,
                        ),
                    ],
                    requires_human_approval=False,
                    follow_ups=[follow_up("device_readback", 5, "PLC ack와 장치 readback을 재확인한다.")],
                    citation_ids=["pepper-agent-001", "pepper-house-safety-001"],
                    confidence=0.92,
                ),
            )
        )
    return rows


def batch21c_robot_rows() -> list[dict[str, Any]]:
    specs = [
        {
            "key": "hotspot-low-confidence",
            "zone_id": "gh-01-zone-robot-a",
            "candidate_id": "candidate-hotspot-021",
            "summary": "비전 후보 candidate-hotspot-021은 성숙도 confidence가 0.42이고 병반 후보와 겹쳐 harvest_candidate_review가 아니라 inspect_crop이 필요하다.",
            "task_type": "inspect_crop",
            "target_id": "hotspot-021",
            "priority": "high",
            "source_eval_ids": ["blind-robot-005", "robot-eval-013"],
        },
        {
            "key": "disease-overlap",
            "zone_id": "gh-01-zone-robot-b",
            "candidate_id": "candidate-disease-034",
            "summary": "candidate-disease-034가 탄저 의심 반점과 성숙 후보를 동시에 갖고 있어 generic manual_review 대신 inspect_crop exact enum이 필요하다.",
            "task_type": "inspect_crop",
            "target_id": "plant-row-b-17",
            "priority": "high",
            "source_eval_ids": ["blind-robot-005", "robot-eval-016"],
        },
        {
            "key": "occluded-fruit",
            "zone_id": "gh-01-zone-robot-c",
            "candidate_id": "candidate-occluded-044",
            "summary": "candidate-occluded-044는 잎 가림으로 과실 상태가 불명확해 수확 후보로 쓰지 말고 inspect_crop으로 재확인해야 한다.",
            "task_type": "inspect_crop",
            "target_id": "plant-row-c-08",
            "priority": "medium",
            "source_eval_ids": ["robot-eval-013"],
        },
        {
            "key": "blocked-aisle",
            "zone_id": "gh-01-zone-robot-d",
            "candidate_id": "candidate-blocked-052",
            "summary": "candidate-blocked-052 주변 통로가 젖어 있고 작업자 cart가 남아 있어 접근하지 말고 skip_area를 내려야 한다.",
            "task_type": "skip_area",
            "target_id": "aisle-d-03",
            "priority": "critical",
            "source_eval_ids": ["robot-eval-016"],
        },
        {
            "key": "spray-reentry",
            "zone_id": "gh-01-zone-robot-e",
            "candidate_id": "candidate-reentry-066",
            "summary": "방제 후 reentry_pending이 남아 candidate-reentry-066 접근은 금지이고 해당 구역은 skip_area로 제외해야 한다.",
            "task_type": "skip_area",
            "target_id": "zone-robot-e-reentry-block",
            "priority": "critical",
            "source_eval_ids": ["robot-eval-016", "robot-eval-015"],
        },
        {
            "key": "low-confidence-cluster",
            "zone_id": "gh-01-zone-robot-f",
            "candidate_id": "candidate-cluster-078",
            "summary": "candidate-cluster-078 주변 3개 후보가 모두 confidence 0.5 미만이고 색상/병반이 섞여 inspect_crop exact task가 필요하다.",
            "task_type": "inspect_crop",
            "target_id": "cluster-f-078",
            "priority": "high",
            "source_eval_ids": ["blind-robot-005"],
        },
    ]
    rows: list[dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        sid = f"robot-task-batch21c-{spec['key']}-{i:03d}"
        rows.append(
            sample(
                sid,
                "robot_task_prioritization",
                {
                    "farm_id": "demo-farm",
                    "zone_id": spec["zone_id"],
                    "growth_stage": "harvest",
                    "state_summary": spec["summary"],
                    "candidate_ids": [spec["candidate_id"]],
                    "active_constraints": ["robot_exact_enum_required"],
                    "source_eval_ids": spec["source_eval_ids"],
                    "retrieved_context": ["pepper-agent-001"],
                },
                {
                    "situation_summary": "로봇 후보는 generic manual_review가 아니라 exact enum, candidate_id, target을 모두 갖춘 task로 내려야 한다.",
                    "risk_level": "critical" if spec["priority"] == "critical" else "high",
                    "robot_tasks": [
                        robot_task(
                            f"batch21c-robot-{i:03d}",
                            1,
                            spec["task_type"],
                            "zone" if spec["task_type"] == "skip_area" else "plant",
                            spec["target_id"],
                            spec["priority"],
                            "candidate_id와 target이 명확한 exact robot task로 운영자가 바로 검토할 수 있게 한다.",
                            candidate_id=spec["candidate_id"],
                        )
                    ],
                    "skipped_candidates": [
                        {
                            "candidate_id": spec["candidate_id"],
                            "reason": "manual_review 같은 generic fallback은 계약상 usable robot task로 보지 않는다.",
                        }
                    ],
                    "requires_human_approval": True,
                    "follow_up": [
                        follow_up("operator_confirm", 0, "candidate_id, target, 접근 가능성을 확인한다.")
                    ],
                    "confidence": 0.74,
                    "retrieval_coverage": "sufficient",
                    "citations": citations(["pepper-agent-001"]),
                },
            )
        )
    return rows


def main() -> None:
    batch21a_state = evidence_unknown_rows() + climate_high_rows() + gt_master_high_rows()
    batch21a_failure = batch21a_failure_rows()
    batch21a_forbidden = batch21a_forbidden_rows()
    batch21b_action = batch21b_action_rows()
    batch21b_state = batch21b_state_rows()
    batch21b_failure = batch21b_failure_rows()
    batch21c_robot = batch21c_robot_rows()

    outputs = [
        (BATCH21A_STATE_OUTPUT, batch21a_state),
        (BATCH21A_FAILURE_OUTPUT, batch21a_failure),
        (BATCH21A_FORBIDDEN_OUTPUT, batch21a_forbidden),
        (BATCH21B_ACTION_OUTPUT, batch21b_action),
        (BATCH21B_STATE_OUTPUT, batch21b_state),
        (BATCH21B_FAILURE_OUTPUT, batch21b_failure),
        (BATCH21C_ROBOT_OUTPUT, batch21c_robot),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)

    print(
        json.dumps(
            {
                "outputs": {
                    str(path.relative_to(REPO_ROOT)): len(rows)
                    for path, rows in outputs
                },
                "batch21a_rows": len(batch21a_state) + len(batch21a_failure) + len(batch21a_forbidden),
                "batch21b_rows": len(batch21b_action) + len(batch21b_state) + len(batch21b_failure),
                "batch21c_rows": len(batch21c_robot),
                "total_rows": sum(len(rows) for _, rows in outputs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
