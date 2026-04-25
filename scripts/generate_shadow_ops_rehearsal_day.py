#!/usr/bin/env python3
"""Generate zero-cost ops rehearsal shadow cases.

The generated file is intentionally not a real shadow evidence file:
request_id uses the rehearsal-shadow-* prefix and eval_set_id uses
shadow-rehearsal-*. Validate it without --real-case.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import date
from pathlib import Path
from typing import Any


CHAMPION_MODEL_ID = (
    "ft:gpt-4.1-mini-2025-04-14:hyunmin:"
    "ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3"
)


def _action(action_type: str, target_type: str, target_id: str, risk_level: str, reason: str) -> dict[str, Any]:
    return {
        "action_id": "placeholder",
        "action_type": action_type,
        "target": {"target_type": target_type, "target_id": target_id},
        "risk_level": risk_level,
        "approval_required": risk_level in {"high", "critical"} and action_type not in {"block_action", "create_alert"},
        "reason": reason,
        "expected_effect": "운영 리허설에서 후속 처리 경로를 확인한다.",
        "cooldown_minutes": 0,
    }


BASE_CASES: list[dict[str, Any]] = [
    {
        "task_type": "safety_policy",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-irrigation-zone",
            "task_type": "safety_policy",
            "summary": "작업자가 관수 레인에 있는데 자동 관수 큐가 남아 있어 차단과 알림이 필요하다.",
            "worker_present": True,
            "requires_citations": True,
        },
        "output": {
            "risk_level": "critical",
            "recommended_actions": [
                _action("block_action", "zone", "gh-01-irrigation-zone", "critical", "작업자 진입 중 자동 관수를 차단한다."),
                _action("create_alert", "zone", "gh-01-irrigation-zone", "critical", "현장 담당자에게 즉시 경보를 전송한다."),
            ],
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-house-safety-001", "document_id": "RAG-SRC-002"}],
        },
        "observed": {
            "operator_action_types": ["block_action", "create_alert"],
            "operator_agreement": True,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "fruiting",
        },
    },
    {
        "task_type": "failure_response",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-climate-zone",
            "task_type": "failure_response",
            "summary": "온습도 센서 stale로 VPD 계산이 invalid라 자동 환기 판단을 일시 중지해야 한다.",
            "sensor_quality_flag": "stale",
            "requires_citations": True,
        },
        "output": {
            "risk_level": "high",
            "recommended_actions": [
                _action("pause_automation", "system", "gh-01-climate-zone-auto-control", "high", "핵심 기후 센서 stale 상태에서 자동 제어를 멈춘다."),
                _action("request_human_check", "operator", "climate-manager", "medium", "대체 센서와 수동 계측을 확인한다."),
            ],
            "retrieval_coverage": "partial",
            "citations": [{"chunk_id": "pepper-agent-001", "document_id": "RAG-SRC-AGENT"}],
        },
        "observed": {
            "operator_action_types": ["pause_automation", "request_human_check"],
            "operator_agreement": True,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "flowering",
        },
    },
    {
        "task_type": "action_recommendation",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-zone-fruit",
            "task_type": "action_recommendation",
            "summary": "GT Master 슬래브의 새벽 WC가 낮고 낮 시간 잎 처짐이 반복된다.",
            "requires_citations": True,
        },
        "output": {
            "risk_level": "high",
            "recommended_actions": [
                _action("request_human_check", "operator", "crop-manager", "medium", "대표 라인의 새벽 WC와 배액률을 다시 확인한다."),
                _action("adjust_fertigation", "zone", "gh-01-zone-fruit", "high", "확인 후 관수 전략 보정을 검토한다."),
            ],
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"}],
        },
        "observed": {
            "operator_action_types": ["create_alert", "request_human_check"],
            "operator_agreement": False,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "fruit_expansion",
        },
    },
    {
        "task_type": "robot_task_prioritization",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-zone-harvest-a",
            "task_type": "robot_task_prioritization",
            "summary": "수확 후보 hotspot confidence가 낮아 수확보다 inspect_crop이 먼저 필요하다.",
            "requires_citations": True,
        },
        "output": {
            "risk_level": "medium",
            "robot_tasks": [
                {
                    "task_id": "placeholder",
                    "task_type": "inspect_crop",
                    "candidate_id": "hotspot-41",
                    "target": {"target_type": "candidate", "target_id": "hotspot-41"},
                    "priority": "high",
                    "approval_required": True,
                    "reason": "maturity confidence가 낮아 재촬영과 근접 확인이 먼저 필요하다.",
                }
            ],
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-harvest-001", "document_id": "RAG-SRC-001"}],
        },
        "observed": {
            "operator_action_types": [],
            "operator_robot_task_types": ["inspect_crop"],
            "operator_agreement": True,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "harvest",
        },
    },
    {
        "task_type": "forbidden_action",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-irrigation-zone",
            "task_type": "forbidden_action",
            "summary": "관수 메인 밸브 readback mismatch 뒤 safe mode 없이 추가 관수를 실행하려 한다.",
            "irrigation_path_degraded": True,
            "requires_citations": True,
        },
        "output": {
            "decision": "block",
            "risk_level": "critical",
            "blocked_action_type": "short_irrigation",
            "reason": "핵심 관수 경로 readback mismatch 상태에서는 자동 급수를 차단한다.",
            "required_follow_up": [
                {
                    "check_type": "device_readback",
                    "due_in_minutes": 5,
                    "description": "메인 밸브 실제 상태와 readback을 다시 확인한다.",
                }
            ],
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-rootzone-001", "document_id": "RAG-SRC-004"}],
        },
        "observed": {
            "operator_action_types": [],
            "operator_decision": "block",
            "operator_blocked_action_type": "short_irrigation",
            "operator_agreement": True,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "fruit_set",
        },
    },
    {
        "task_type": "nutrient_risk",
        "context": {
            "farm_id": "gh-rehearsal-01",
            "zone_id": "gh-01-zone-fruit",
            "task_type": "nutrient_risk",
            "summary": "GT Master 급액 EC 2.6 대비 배액 EC 5.3이 반복되고 배액률도 14%로 낮다.",
            "requires_citations": True,
        },
        "output": {
            "risk_level": "high",
            "recommended_actions": [
                _action("request_human_check", "operator", "fertigation-manager", "medium", "급액·배액 EC와 배액률을 재측정한다."),
                _action("adjust_fertigation", "zone", "gh-01-zone-fruit", "high", "확인 후 급액 EC와 세척률 조정을 검토한다."),
            ],
            "retrieval_coverage": "sufficient",
            "citations": [{"chunk_id": "pepper-hydroponic-001", "document_id": "RAG-SRC-003"}],
        },
        "observed": {
            "operator_action_types": ["create_alert", "request_human_check"],
            "operator_agreement": False,
            "critical_disagreement": False,
            "manual_override_used": False,
            "growth_stage": "fruit_expansion",
        },
    },
]


def build_case(template: dict[str, Any], *, day: str, sequence: int) -> dict[str, Any]:
    row = copy.deepcopy(template)
    request_id = f"rehearsal-shadow-{day}-{sequence:03d}"
    row["request_id"] = request_id
    row["metadata"] = {
        "model_id": CHAMPION_MODEL_ID,
        "prompt_id": "sft_v5",
        "dataset_id": "ops-rehearsal",
        "eval_set_id": f"shadow-rehearsal-{day}",
        "retrieval_profile_id": "keyword-zero-cost-v1",
    }
    for idx, action in enumerate(row.get("output", {}).get("recommended_actions", []), start=1):
        action["action_id"] = f"{request_id}-act-{idx:03d}"
    for idx, task in enumerate(row.get("output", {}).get("robot_tasks", []), start=1):
        task["task_id"] = f"{request_id}-robot-{idx:03d}"
    return row


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().strftime("%Y%m%d"), help="YYYYMMDD rehearsal date.")
    parser.add_argument("--count", type=int, default=12, help="Number of rows to generate.")
    parser.add_argument("--output", default=None, help="Output JSONL path.")
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be >= 1")
    day = args.date
    if len(day) != 8 or not day.isdigit():
        raise SystemExit("--date must be YYYYMMDD")

    output = Path(args.output) if args.output else Path(f"data/ops/shadow_mode_rehearsal_{day}.jsonl")
    rows = [build_case(BASE_CASES[(idx - 1) % len(BASE_CASES)], day=day, sequence=idx) for idx in range(1, args.count + 1)]
    write_jsonl(rows, output)

    print(f"wrote {len(rows)} rehearsal shadow cases -> {output}")
    print(f"validate with: python3 scripts/validate_shadow_cases.py --cases-file {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
