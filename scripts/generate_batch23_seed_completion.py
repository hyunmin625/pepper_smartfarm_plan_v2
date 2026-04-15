#!/usr/bin/env python3
"""Generate batch23 seed files so action/forbidden samples each reach 100 rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_OUTPUT = REPO_ROOT / "data/examples/action_recommendation_samples_batch23_seed_completion.jsonl"
FORBIDDEN_OUTPUT = REPO_ROOT / "data/examples/forbidden_action_samples_batch23_seed_completion.jsonl"

ACTION_TARGET_ROWS = 51
FORBIDDEN_TARGET_ROWS = 74

DOC_IDS = {
    "pepper-agent-001": "EXPERT-AI-DESIGN",
    "pepper-climate-001": "RAG-SRC-005",
    "pepper-crop-env-thresholds-001": "RAG-SRC-010",
    "pepper-first-frost-fruit-recovery-001": "RAG-SRC-001",
    "pepper-flowerdrop-heavy-shading-001": "RAG-SRC-020",
    "pepper-house-drying-hygiene-001": "RAG-SRC-001",
    "pepper-hydroponic-001": "RAG-SRC-003",
    "pepper-hydroponic-mixer-check-001": "RAG-SRC-003",
    "pepper-rainshelter-lowlight-yield-001": "RAG-SRC-001",
    "pepper-rootzone-001": "RAG-SRC-004",
    "pepper-shading-strategy-001": "RAG-SRC-001",
}

ACTION_VARIANTS = [
    {"zone_id": "gh-01-zone-a", "zone_label": "A구역", "operator_id": "duty-manager"},
    {"zone_id": "gh-01-zone-b", "zone_label": "B구역", "operator_id": "climate-manager"},
    {"zone_id": "gh-01-zone-c", "zone_label": "C구역", "operator_id": "fertigation-manager"},
    {"zone_id": "gh-01-zone-d", "zone_label": "D구역", "operator_id": "night-duty"},
    {"zone_id": "gh-01-zone-east", "zone_label": "동측 구역", "operator_id": "crop-manager"},
    {"zone_id": "gh-01-zone-west", "zone_label": "서측 구역", "operator_id": "rootzone-manager"},
]

FORBIDDEN_VARIANTS = [
    {"zone_id": "gh-01-zone-a", "zone_label": "A구역"},
    {"zone_id": "gh-01-zone-b", "zone_label": "B구역"},
    {"zone_id": "gh-01-zone-c", "zone_label": "C구역"},
    {"zone_id": "gh-01-zone-d", "zone_label": "D구역"},
    {"zone_id": "gh-01-zone-east", "zone_label": "동측 구역"},
    {"zone_id": "gh-01-zone-west", "zone_label": "서측 구역"},
    {"zone_id": "dry-room-1", "zone_label": "건조실 1"},
]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def citations(chunk_ids: list[str]) -> list[dict[str, str]]:
    return [{"chunk_id": chunk_id, "document_id": DOC_IDS[chunk_id]} for chunk_id in chunk_ids]


def action_entry(
    action_id: str,
    action_type: str,
    target_type: str,
    target_id: str,
    risk_level: str,
    approval_required: bool,
    reason: str,
    expected_effect: str,
    cooldown_minutes: int,
    *,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action_id": action_id,
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


def follow_up(check_type: str, due_in_minutes: int, description: str) -> dict[str, Any]:
    return {
        "check_type": check_type,
        "due_in_minutes": due_in_minutes,
        "description": description,
    }


ACTION_SCENARIOS = [
    {
        "key": "heat_shade",
        "growth_stage": "flowering",
        "retrieved_context": ["pepper-climate-001", "pepper-shading-strategy-001"],
        "risk_level": "high",
        "requires_human_approval": True,
        "approval_reason": "차광 setpoint 변경은 승인 정책 대상이다.",
        "state_summary": lambda v, n: (
            f"개화기 {v['zone_label']}에서 오전 11시 이후 기온이 {31 + (n % 3)}℃까지 오르고 "
            f"PAR가 {820 + n * 15} 수준으로 상승했지만 차광률은 아직 {15 + (n % 3) * 5}%에 머물러 있다."
        ),
        "situation_summary": "개화기 강광·고온 조합이라 차광 조정 검토와 현장 확인이 함께 필요하다.",
        "diagnosis": lambda v, n: [
            "개화기 고온과 과도한 일사는 꽃가루 활력과 착과 안정성을 빠르게 떨어뜨릴 수 있다.",
            "센서 품질이 양호하면 차광 setpoint 조정은 검토할 수 있지만, 현장 확인 없이 급격히 바꾸면 안 된다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "adjust_shade",
                "zone",
                v["zone_id"],
                "medium",
                True,
                "강광과 상단부 고온을 낮추기 위해 차광 비율 상향을 검토한다.",
                "상단부 잎 온도와 꽃 스트레스 상승 속도를 줄인다.",
                15,
                parameters={"target_pct": 35 + (n % 3) * 5},
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "꽃 상태와 환기창 실제 개방 상태를 현장에서 확인한다.",
                "차광 조정 전 현장 리스크를 함께 점검한다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "adjust_heating", "reason": "고온 위험 상태에서는 난방 관련 조정을 검토하면 안 된다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("trend_review", 20, "차광 적용 전후 기온·습도·PAR 추세를 비교한다.")
        ],
    },
    {
        "key": "humid_fan",
        "growth_stage": "fruit_set",
        "retrieved_context": ["pepper-climate-001", "pepper-crop-env-thresholds-001"],
        "risk_level": "high",
        "requires_human_approval": True,
        "approval_reason": "팬 setpoint 변경은 승인 후 적용한다.",
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 새벽 상대습도가 {92 - (n % 4)}%까지 올라가고 "
            f"잎 젖음 메모가 2회 연속 기록됐다. 현재 팬 duty는 {25 + (n % 3) * 5}%다."
        ),
        "situation_summary": "새벽 고습과 잎 젖음 반복은 결로·병해 위험을 키워 팬 운전 보강 검토가 필요하다.",
        "diagnosis": lambda v, n: [
            "새벽 RH 상승과 잎 젖음은 결로와 병해 확산 조건을 빠르게 만든다.",
            "팬 조정은 가능하지만 작업자 동선과 현재 풍량을 함께 확인한 뒤 승인하는 편이 안전하다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "adjust_fan",
                "zone",
                v["zone_id"],
                "medium",
                True,
                "새벽 결로 위험을 줄이기 위해 순환팬 duty 상향을 검토한다.",
                "정체층을 깨고 잎 젖음 지속 시간을 줄인다.",
                15,
                parameters={"target_pct": 45 + (n % 3) * 5},
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "잎 젖음 범위와 팬 풍속 체감 구간을 현장에서 확인한다.",
                "결로 원인이 실제 공기 정체인지 확인할 수 있다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "adjust_co2", "reason": "고습·결로 상황에서 CO2 주입 증대는 우선순위가 아니다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("trend_review", 15, "새벽 RH와 잎 젖음 메모가 팬 조정 후 줄어드는지 확인한다.")
        ],
    },
    {
        "key": "rootzone_salinity",
        "growth_stage": "fruit_expansion",
        "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        "risk_level": "high",
        "requires_human_approval": True,
        "approval_reason": "양액 전략 조정은 현장 확인 뒤 승인해야 한다.",
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 배액 EC가 급액 EC보다 {0.8 + (n % 3) * 0.2:.1f} dS/m 높고 "
            f"배액률은 {12 + (n % 4)}%에 머물러 rootzone 염류 집적 우려가 있다."
        ),
        "situation_summary": "배액 EC 상승과 낮은 배액률 조합은 근권 염류 집적 가능성이 높아 현장 재확인이 먼저다.",
        "diagnosis": lambda v, n: [
            "배액 EC 상승은 염류가 충분히 빠져나가지 못한다는 신호일 수 있다.",
            "레시피를 바로 바꾸기보다 수동 측정으로 급액·배액 상태를 교차 확인해야 한다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "request_human_check",
                "operator",
                v["operator_id"],
                "medium",
                False,
                "급액·배액 EC/pH와 drain 비율을 수동 측정으로 다시 확인한다.",
                "센서 기반 판단을 현장 수치로 교차 검증한다.",
                0,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "adjust_fertigation",
                "zone",
                v["zone_id"],
                "high",
                True,
                "염류 집적이 확인되면 레시피와 drain target 조정이 필요할 수 있다.",
                "근권 염류 집적 완화 방향을 검토한다.",
                60,
                parameters={"strategy": "review_feed_ec_and_drain_target"},
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "short_irrigation", "reason": "원인 확인 없이 reflex 관수를 추가하면 배지 통기 저하를 키울 수 있다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("sensor_recheck", 20, "급액·배액 EC/pH와 drain 비율을 다시 측정한다.")
        ],
    },
    {
        "key": "dryroom_humidity",
        "growth_stage": "drying",
        "retrieved_context": ["pepper-house-drying-hygiene-001"],
        "risk_level": "medium",
        "requires_human_approval": False,
        "approval_reason": None,
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 건조실 RH가 {76 + (n % 4)}%까지 올라가고 "
            f"최근 저장 lot 함수율 재측정이 지연돼 재흡습 우려가 커지고 있다."
        ),
        "situation_summary": "건조실 고습은 재흡습과 저장 품질 저하 위험을 키워 즉시 경고와 현장 점검이 필요하다.",
        "diagnosis": lambda v, n: [
            "건조실 고습은 재흡습과 곰팡이 위험을 키울 수 있다.",
            "저장 lot 함수율을 다시 보지 않으면 품질 저하 시점을 놓칠 수 있다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "create_alert",
                "zone",
                v["zone_id"],
                "medium",
                False,
                "건조실 고습과 재흡습 우려를 즉시 알린다.",
                "저장 lot 점검을 빠르게 시작할 수 있다.",
                10,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "건조실 RH, lot 함수율, 제습기 readback을 현장에서 다시 확인한다.",
                "실제 저장 품질 영향 여부를 조기에 판단한다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [],
        "follow_up": lambda v, n: [
            follow_up("lab_test", 60, "저장 lot 함수율과 곰팡이 징후를 다시 측정한다.")
        ],
    },
    {
        "key": "dawn_wc_drop",
        "growth_stage": "fruiting",
        "retrieved_context": ["pepper-rootzone-001", "pepper-hydroponic-001"],
        "risk_level": "high",
        "requires_human_approval": False,
        "approval_reason": None,
        "state_summary": lambda v, n: (
            f"{v['zone_label']} 대표 slab의 새벽 WC가 {49 - (n % 3)}%까지 떨어졌고 "
            f"야간 dry-back은 {11 + (n % 4)}%로 증가 추세다."
        ),
        "situation_summary": "새벽 WC 저하와 과도한 야간 dry-back 반복은 근권 회복 여유가 부족하다는 신호다.",
        "diagnosis": lambda v, n: [
            "새벽 WC 저하는 전날 관수 리듬과 slab 회복이 충분하지 않았을 가능성을 시사한다.",
            "지금은 자동 recipe 조정보다 현장 확인과 경보가 우선이다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "create_alert",
                "operator",
                v["operator_id"],
                "high",
                False,
                "dawn WC 저하와 dry-back 증가를 rootzone 고위험으로 알린다.",
                "근권 스트레스 징후를 놓치지 않고 대응한다.",
                0,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "high",
                False,
                "대표 slab의 dawn WC 회복과 dripper 균일도를 수동 점검한다.",
                "자동 조정 전 실제 원인을 확인한다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "adjust_fertigation", "reason": "dawn WC 저하만으로 자동 recipe 변경을 바로 걸면 안 된다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("visual_inspection", 0, "대표 slab의 dawn WC 회복과 drain 반응을 현장에서 본다.")
        ],
    },
    {
        "key": "nursery_cold_humid",
        "growth_stage": "nursery",
        "retrieved_context": ["pepper-climate-001", "pepper-crop-env-thresholds-001"],
        "risk_level": "high",
        "requires_human_approval": True,
        "approval_reason": "육묘 구간 난방 setpoint 변경은 승인 대상이다.",
        "state_summary": lambda v, n: (
            f"육묘 {v['zone_label']}에서 야간 기온이 {15 - (n % 2)}℃까지 내려가고 "
            f"RH는 {90 + (n % 3)}%로 높아 활착 지연과 과습 우려가 동시에 커지고 있다."
        ),
        "situation_summary": "육묘 야간 저온·고습 조합은 활착 지연과 병해 위험을 높여 난방 보강 검토가 필요하다.",
        "diagnosis": lambda v, n: [
            "육묘 구간의 저온·고습 조합은 활착 지연과 병해 압력을 동시에 키운다.",
            "난방 조정은 가능하지만 실제 보온 상태와 병해 흔적을 확인한 뒤 승인하는 편이 안전하다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "adjust_heating",
                "zone",
                v["zone_id"],
                "medium",
                True,
                "육묘 야간 저온을 줄이기 위해 난방 setpoint 상향을 검토한다.",
                "야간 활착 지연과 결로 시간을 완화한다.",
                20,
                parameters={"target_temp_c": 17 + (n % 2)},
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "육묘 tray 과습과 결로 흔적을 현장에서 확인한다.",
                "난방 조정 전 보온 상태와 병해 전조를 함께 본다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "short_irrigation", "reason": "야간 고습 상태에서 reflex 관수는 활착 지연을 더 키울 수 있다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("trend_review", 30, "야간 기온·RH와 tray 표면 상태가 개선되는지 확인한다.")
        ],
    },
    {
        "key": "co2_lock",
        "growth_stage": "vegetative_growth",
        "retrieved_context": ["pepper-climate-001", "pepper-agent-001"],
        "risk_level": "high",
        "requires_human_approval": False,
        "approval_reason": None,
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 CO2가 {340 + n * 5}ppm으로 낮지만 vent_open_lock이 active라 "
            f"CO2 주입 경로를 바로 열 수 없다."
        ),
        "situation_summary": "CO2 저하가 보여도 vent_open_lock이 active면 즉시 주입보다 경고와 현장 확인이 먼저다.",
        "diagnosis": lambda v, n: [
            "환기 손실이 큰 상태에서 CO2를 바로 올리면 비효율과 오판 위험이 크다.",
            "lock 조건이 풀리기 전에는 현장 상태와 vent readback을 먼저 확인해야 한다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "create_alert",
                "operator",
                v["operator_id"],
                "high",
                False,
                "CO2 부족과 vent_open_lock 동시 발생을 운영자에게 알린다.",
                "lock 상태를 무시한 제어를 예방한다.",
                0,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "medium",
                False,
                "환기창 실제 개방 상태와 CO2 인터록 조건을 확인한다.",
                "CO2 보정 가능 시점을 정확히 판단한다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "adjust_co2", "reason": "vent_open_lock이 active면 CO2 주입을 바로 추천하면 안 된다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("device_readback", 10, "환기창 readback과 CO2 인터록 해제 여부를 확인한다.")
        ],
    },
    {
        "key": "late_frost",
        "growth_stage": "harvest_ready",
        "retrieved_context": ["pepper-first-frost-fruit-recovery-001"],
        "risk_level": "medium",
        "requires_human_approval": False,
        "approval_reason": None,
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에 첫서리 예보가 12시간 안으로 들어왔고 "
            f"후기 수확 잔존 과실 비율이 {18 + n}% 수준이다."
        ),
        "situation_summary": "후기 수확 단계의 첫서리 예보는 장치 조정보다 회수 우선순위와 현장 판단이 먼저다.",
        "diagnosis": lambda v, n: [
            "후기 수확 단계에서는 첫서리 전 남은 과실 회수와 종료 판단이 더 중요할 수 있다.",
            "이 시점에는 복잡한 제어보다 경보와 수확 우선순위 확인이 적절하다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "create_alert",
                "operator",
                v["operator_id"],
                "medium",
                False,
                "첫서리 예보와 잔존 과실 회수 필요성을 알린다.",
                "수확 우선순위 조정을 빠르게 시작할 수 있다.",
                0,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "잔존 과실 회수 가능량과 종료 시점을 현장에서 확인한다.",
                "후기 운영 종료 판단을 앞당길 수 있다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [],
        "follow_up": lambda v, n: [
            follow_up("operator_confirm", 30, "후기 수확·철거 우선순위를 운영자와 확인한다.")
        ],
    },
    {
        "key": "rain_lowlight",
        "growth_stage": "fruit_set",
        "retrieved_context": ["pepper-rainshelter-lowlight-yield-001", "pepper-flowerdrop-heavy-shading-001"],
        "risk_level": "medium",
        "requires_human_approval": False,
        "approval_reason": None,
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 장마기 저일조가 {2 + (n % 3)}일째 이어지고 "
            f"차광률은 이미 {45 + (n % 3) * 5}%이며 낙화 메모가 간헐적으로 보고된다."
        ),
        "situation_summary": "장마기 저일조가 길어질 때는 추가 차광이나 과격한 제어보다 경고와 현장 재점검이 우선이다.",
        "diagnosis": lambda v, n: [
            "저일조가 길어지면 낙화와 초세 저하 위험이 높아진다.",
            "이 상황에서는 추가 차광보다 광 부족 영향과 결로 위험을 같이 점검하는 것이 낫다.",
        ],
        "recommended_actions": lambda sample_id, v, n: [
            action_entry(
                f"{sample_id}-act-001",
                "create_alert",
                "operator",
                v["operator_id"],
                "medium",
                False,
                "저일조 장기화와 낙화 메모 증가를 운영자에게 알린다.",
                "광 부족 대응 여부를 빠르게 검토할 수 있다.",
                0,
            ),
            action_entry(
                f"{sample_id}-act-002",
                "request_human_check",
                "operator",
                v["operator_id"],
                "low",
                False,
                "낙화 정도, 차광 상태, 결로 흔적을 현장에서 함께 확인한다.",
                "광 부족과 고습 영향의 우선순위를 구분한다.",
                0,
            ),
        ],
        "skipped_actions": lambda n: [
            {"action_type": "adjust_shade", "reason": "장마기 저일조 상황에서 추가 차광은 낙화 위험을 더 키울 수 있다."}
        ],
        "follow_up": lambda v, n: [
            follow_up("visual_inspection", 0, "낙화 정도와 차광 상태, 결로 흔적을 함께 본다.")
        ],
    },
]

FORBIDDEN_SCENARIOS = [
    {
        "key": "manual_override_fan",
        "growth_stage": "vegetative_growth",
        "proposed_action": "adjust_fan",
        "decision": "block",
        "risk_level": "critical",
        "retrieved_context": ["pepper-agent-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 manual_override가 active인데 순환팬 duty 상향 요청이 들어왔다.",
        "reason": lambda v, n: "manual override가 active인 동안 AI가 팬 setpoint를 덮어쓰면 사람 개입을 침범할 수 있다.",
        "follow_up": lambda v, n: [follow_up("operator_confirm", 0, "manual override 유지 이유와 해제 시점을 확인한다.")],
    },
    {
        "key": "safe_mode_vent",
        "growth_stage": "fruit_set",
        "proposed_action": "adjust_vent",
        "decision": "block",
        "risk_level": "critical",
        "retrieved_context": ["pepper-agent-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 safe_mode가 latch된 상태인데 환기창 추가 개방 명령이 제안됐다.",
        "reason": lambda v, n: "safe_mode가 active면 추가 장치 제어보다 장애 원인 확인과 해제가 먼저다.",
        "follow_up": lambda v, n: [follow_up("device_readback", 5, "safe_mode 원인과 환기창 readback을 확인한다.")],
    },
    {
        "key": "worker_robot",
        "growth_stage": "harvest",
        "proposed_action": "create_robot_task",
        "decision": "block",
        "risk_level": "critical",
        "retrieved_context": ["pepper-agent-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에 worker_present 이벤트가 active이고 로봇 작업 재시작 요청이 들어왔다.",
        "reason": lambda v, n: "작업자 존재가 확인된 동안 로봇 작업을 다시 시작하면 안 된다.",
        "follow_up": lambda v, n: [follow_up("operator_confirm", 0, "작업자 퇴장과 안전구역 clear를 확인한다.")],
    },
    {
        "key": "wind_lock_vent",
        "growth_stage": "flowering",
        "proposed_action": "adjust_vent",
        "decision": "block",
        "risk_level": "high",
        "retrieved_context": ["pepper-agent-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 외기 풍속이 {11 + (n % 3)}m/s이고 wind_lock이 active다.",
        "reason": lambda v, n: "강풍 lock이 active인 상태에서 환기창 개방을 더 늘리면 시설 손상 위험이 커진다.",
        "follow_up": lambda v, n: [follow_up("operator_confirm", 5, "강풍 상태와 lock 해제 가능 여부를 확인한다.")],
    },
    {
        "key": "vent_lock_co2",
        "growth_stage": "vegetative_growth",
        "proposed_action": "adjust_co2",
        "decision": "block",
        "risk_level": "high",
        "retrieved_context": ["pepper-climate-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 vent_open_lock이 active인데 CO2 주입량 상향 요청이 들어왔다.",
        "reason": lambda v, n: "vent_open_lock이 active인 상태에서 CO2 주입을 올리면 환기 손실과 인터록 위반 위험이 크다.",
        "follow_up": lambda v, n: [follow_up("device_readback", 5, "환기창 실제 개방 상태와 CO2 인터록 조건을 확인한다.")],
    },
    {
        "key": "tank_low_fertigation",
        "growth_stage": "fruit_expansion",
        "proposed_action": "adjust_fertigation",
        "decision": "block",
        "risk_level": "high",
        "retrieved_context": ["pepper-hydroponic-mixer-check-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 tank_low_level 인터록이 active인데 양액 recipe 변경 요청이 들어왔다.",
        "reason": lambda v, n: "탱크 저수위 인터록이 active면 recipe 변경이나 혼합 실행을 진행하면 안 된다.",
        "follow_up": lambda v, n: [follow_up("operator_confirm", 10, "탱크 수위와 보충 라인 상태를 확인한다.")],
    },
    {
        "key": "ecph_fault_fertigation",
        "growth_stage": "fruiting",
        "proposed_action": "adjust_fertigation",
        "decision": "approval_required",
        "risk_level": "high",
        "retrieved_context": ["pepper-hydroponic-001"],
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 급액 EC/pH 센서 calibration error가 있고 배액 센서도 stale라 "
            "양액 조정 근거가 불완전하다."
        ),
        "reason": lambda v, n: "EC/pH 근거가 깨진 상태에서는 자동 양액 조정보다 수동 확인과 승인 절차가 먼저다.",
        "follow_up": lambda v, n: [follow_up("sensor_recheck", 10, "급액·배액 EC/pH를 수동 측정으로 다시 확인한다.")],
    },
    {
        "key": "overwet_irrigation",
        "growth_stage": "transplanting",
        "proposed_action": "short_irrigation",
        "decision": "approval_required",
        "risk_level": "high",
        "retrieved_context": ["pepper-rootzone-001"],
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 배지 함수율이 높고 배액률이 낮으며 "
            f"rootzone 과습 메모가 {1 + (n % 2)}회 연속 기록됐다."
        ),
        "reason": lambda v, n: "배지 과습 가능성이 있는 상태에서 추가 관수는 현장 확인 없이 자동 실행하면 안 된다.",
        "follow_up": lambda v, n: [follow_up("visual_inspection", 15, "배지 과습과 뿌리 상태, drain 반응을 현장에서 확인한다.")],
    },
    {
        "key": "travel_limit_shade",
        "growth_stage": "flowering",
        "proposed_action": "adjust_shade",
        "decision": "block",
        "risk_level": "high",
        "retrieved_context": ["pepper-shading-strategy-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}에서 shade curtain travel_limit fault가 active인데 차광 100% 명령이 제안됐다.",
        "reason": lambda v, n: "travel limit fault 상태에서 차광커튼을 더 움직이면 장치 손상 위험이 있다.",
        "follow_up": lambda v, n: [follow_up("device_readback", 5, "차광커튼 limit switch와 실제 위치를 확인한다.")],
    },
    {
        "key": "hot_heating",
        "growth_stage": "fruiting",
        "proposed_action": "adjust_heating",
        "decision": "block",
        "risk_level": "critical",
        "retrieved_context": ["pepper-climate-001"],
        "state_summary": lambda v, n: (
            f"{v['zone_label']}에서 낮 기온이 {30 + (n % 3)}℃를 넘고 "
            "잎 말림과 일소 의심 메모가 있다."
        ),
        "reason": lambda v, n: "고온 스트레스가 이미 있는 상태에서 난방 setpoint를 올리면 피해를 더 키울 수 있다.",
        "follow_up": lambda v, n: [follow_up("visual_inspection", 10, "일소와 잎 말림 정도를 현장에서 확인한다.")],
    },
    {
        "key": "dryroom_fertigation",
        "growth_stage": "drying",
        "proposed_action": "adjust_fertigation",
        "decision": "block",
        "risk_level": "medium",
        "retrieved_context": ["pepper-agent-001"],
        "state_summary": lambda v, n: f"{v['zone_label']}은 건조실 zone인데 양액 recipe 변경 요청이 들어왔다.",
        "reason": lambda v, n: "건조실 zone은 양액 조정 대상이 아니므로 action target 자체가 잘못됐다.",
        "follow_up": lambda v, n: [follow_up("operator_confirm", 0, "대상 zone과 장치 종류를 다시 확인한다.")],
    },
]


def build_action_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counter = 1
    for scenario in ACTION_SCENARIOS:
        for variant in ACTION_VARIANTS:
            sample_id = f"action-recommendation-batch23-{scenario['key']}-{counter:03d}"
            rows.append(
                {
                    "sample_id": sample_id,
                    "task_type": "action_recommendation",
                    "input": {
                        "farm_id": "demo-farm",
                        "zone_id": variant["zone_id"],
                        "growth_stage": scenario["growth_stage"],
                        "state_summary": scenario["state_summary"](variant, counter),
                        "active_constraints": [scenario["key"], f"{scenario['key']}_watch"],
                        "retrieved_context": scenario["retrieved_context"],
                    },
                    "preferred_output": {
                        "situation_summary": scenario["situation_summary"],
                        "risk_level": scenario["risk_level"],
                        "diagnosis": scenario["diagnosis"](variant, counter),
                        "recommended_actions": scenario["recommended_actions"](sample_id, variant, counter),
                        "skipped_actions": scenario["skipped_actions"](counter),
                        "requires_human_approval": scenario["requires_human_approval"],
                        "approval_reason": scenario["approval_reason"],
                        "follow_up": scenario["follow_up"](variant, counter),
                        "confidence": round(0.78 + (counter % 5) * 0.02, 2),
                        "retrieval_coverage": "sufficient",
                        "citations": citations(scenario["retrieved_context"]),
                    },
                }
            )
            counter += 1
            if len(rows) == ACTION_TARGET_ROWS:
                return rows
    return rows


def build_forbidden_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counter = 1
    for scenario in FORBIDDEN_SCENARIOS:
        for variant in FORBIDDEN_VARIANTS:
            sample_id = f"forbidden-action-batch23-{scenario['key']}-{counter:03d}"
            rows.append(
                {
                    "sample_id": sample_id,
                    "task_type": "forbidden_action",
                    "input": {
                        "farm_id": "demo-farm",
                        "zone_id": variant["zone_id"],
                        "growth_stage": scenario["growth_stage"],
                        "proposed_action": scenario["proposed_action"],
                        "state_summary": scenario["state_summary"](variant, counter),
                        "retrieved_context": scenario["retrieved_context"],
                    },
                    "preferred_output": {
                        "decision": scenario["decision"],
                        "risk_level": scenario["risk_level"],
                        "blocked_action_type": scenario["proposed_action"],
                        "reason": scenario["reason"](variant, counter),
                        "required_follow_up": scenario["follow_up"](variant, counter),
                        "citations": citations(scenario["retrieved_context"]),
                    },
                }
            )
            counter += 1
            if len(rows) == FORBIDDEN_TARGET_ROWS:
                return rows
    return rows


def main() -> None:
    action_rows = build_action_rows()
    forbidden_rows = build_forbidden_rows()
    if len(action_rows) != ACTION_TARGET_ROWS:
        raise SystemExit(f"expected {ACTION_TARGET_ROWS} action rows, got {len(action_rows)}")
    if len(forbidden_rows) != FORBIDDEN_TARGET_ROWS:
        raise SystemExit(f"expected {FORBIDDEN_TARGET_ROWS} forbidden rows, got {len(forbidden_rows)}")
    write_jsonl(ACTION_OUTPUT, action_rows)
    write_jsonl(FORBIDDEN_OUTPUT, forbidden_rows)
    print(f"action_rows: {len(action_rows)}")
    print(f"action_output: {ACTION_OUTPUT.relative_to(REPO_ROOT).as_posix()}")
    print(f"forbidden_rows: {len(forbidden_rows)}")
    print(f"forbidden_output: {FORBIDDEN_OUTPUT.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
