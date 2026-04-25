#!/usr/bin/env python3
"""Validate the LLM orchestrator response contract checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from llm_orchestrator import LLMOrchestratorService, ModelConfig, OrchestratorRequest, validate_response_contract  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def validate_direct_contract() -> list[str]:
    errors: list[str] = []
    valid_output = {
        "risk_level": "medium",
        "confidence": 0.62,
        "retrieval_coverage": "sufficient",
        "citations": [{"chunk_id": "pepper-citation-001", "document_id": "RAG-SRC-001"}],
        "follow_up": [
            {
                "check_type": "trend_review",
                "description": "Review the last 30 minutes of climate trend before execution.",
            }
        ],
        "recommended_actions": [
            {
                "action_type": "adjust_vent",
                "target": {"target_type": "device", "target_id": "vent-east-01"},
                "parameters": {"position_pct": 35},
                "approval_required": True,
                "risk_level": "medium",
            }
        ],
        "robot_tasks": [
            {
                "task_type": "inspect_crop",
                "candidate_id": "vision-candidate-001",
                "approval_required": True,
                "reason": "Confirm fruit maturity and aisle clearance before task execution.",
            }
        ],
    }
    valid_report = validate_response_contract(
        valid_output,
        retrieved_chunk_ids={"pepper-citation-001"},
        raw_text=json.dumps(valid_output, ensure_ascii=False),
        strict_json_ok=True,
    )
    if not valid_report.ok:
        errors.append(f"valid output should pass response contract: {valid_report.errors}")

    invalid_output = {
        "risk_level": "medium",
        "confidence": 1.5,
        "retrieval_coverage": "bogus",
        "citations": [{"chunk_id": "outside-context"}],
        "follow_up": [{"type": "unknown_check"}],
        "recommended_actions": [
            {
                "action_type": "bad_action",
                "target": {"target_type": "device", "target_id": "vent-east-01"},
                "parameters": {"position_pct": 200},
            }
        ],
        "robot_tasks": [{"task_type": "bad_task"}],
    }
    invalid_report = validate_response_contract(
        invalid_output,
        retrieved_chunk_ids={"pepper-citation-001"},
        raw_text="분석: {\"confidence\": 1.5}",
        strict_json_ok=False,
    )
    expected_fragments = [
        "confidence:must_be_number_0_to_1",
        "retrieval_coverage:invalid_or_missing",
        "natural_language_leakage:non_json_prefix_or_suffix",
        "natural_language_leakage:recovered_not_strict_json",
        "recommended_actions[0].action_type:invalid",
        "recommended_actions[0].parameters.position_pct:out_of_range",
        "citations[0].chunk_id:not_in_retrieved_context",
        "follow_up[0].type:invalid",
        "follow_up[0]:missing_description_note_or_reason",
        "robot_tasks[0].task_type:invalid",
        "robot_tasks[0].reason:missing",
        "robot_tasks[0]:candidate_id_or_target_required",
    ]
    for fragment in expected_fragments:
        if fragment not in invalid_report.errors:
            errors.append(f"invalid output did not report {fragment}: {invalid_report.errors}")
    return errors


def validate_service_integration() -> tuple[list[str], dict]:
    scenarios = {
        row["scenario_id"]: row
        for row in load_jsonl(REPO_ROOT / "data/examples/synthetic_sensor_scenarios.jsonl")
    }
    scenario = scenarios["synthetic-002"]
    zone_state = build_zone_state_payload(scenario)
    zone_state["active_constraints"] = {"zone_clearance_uncertain": False}
    zone_state["state_estimate"] = estimate_zone_state(scenario).as_dict()
    zone_state["current_state"]["summary"] = scenario["summary"]

    service = LLMOrchestratorService.from_model_config(ModelConfig(provider="stub", model_id="champion"))
    result = service.evaluate(
        OrchestratorRequest(
            request_id="response-contract-validate-001",
            zone_id=scenario["zone_id"],
            task_type="state_judgement",
            zone_state=zone_state,
        )
    )
    errors: list[str] = []
    if result.response_contract_errors:
        errors.append(f"service response contract should pass: {result.response_contract_errors}")
    return errors, result.as_dict()


def main() -> int:
    errors = validate_direct_contract()
    service_errors, service_result = validate_service_integration()
    errors.extend(service_errors)
    print(
        json.dumps(
            {
                "errors": errors,
                "service_contract_errors": service_result["response_contract_errors"],
                "service_contract_warnings": service_result["response_contract_warnings"],
                "service_validator_reason_codes": service_result["validator_reason_codes"],
                "service_retrieval_chunk_ids": [chunk["chunk_id"] for chunk in service_result["retrieval_chunks"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
