#!/usr/bin/env python3
"""Validate llm orchestrator service with stub client and local retriever."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from llm_orchestrator import LLMOrchestratorService, ModelConfig, OrchestratorRequest  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    scenarios = {
        row["scenario_id"]: row
        for row in load_jsonl(REPO_ROOT / "data/examples/synthetic_sensor_scenarios.jsonl")
    }
    scenario = scenarios["synthetic-002"]
    zone_state = build_zone_state_payload(scenario)
    zone_state["active_constraints"] = {"zone_clearance_uncertain": False}
    zone_state["state_estimate"] = estimate_zone_state(scenario).as_dict()
    zone_state["current_state"]["summary"] = scenario["summary"]

    service = LLMOrchestratorService.from_model_config(
        ModelConfig(provider="stub", model_id="pepper-ops-local-stub")
    )
    result = service.evaluate(
        OrchestratorRequest(
            request_id="orchestrator-validate-001",
            zone_id=scenario["zone_id"],
            task_type="state_judgement",
            zone_state=zone_state,
        )
    )
    errors: list[str] = []
    if not result.parse_result.json_object_ok:
        errors.append("stub response should parse as JSON object")
    if not result.retrieval_chunks:
        errors.append("retriever should return at least one chunk")
    citations = result.validated_output.get("citations", [])
    if not citations:
        errors.append("validated output should contain citations")
    action_types = [
        action.get("action_type")
        for action in result.validated_output.get("recommended_actions", [])
        if isinstance(action, dict)
    ]
    if "request_human_check" not in action_types:
        errors.append("validated output should include request_human_check")

    print(
        json.dumps(
            {
                "request_id": result.request.request_id,
                "errors": errors,
                "retrieval_chunk_ids": [chunk.chunk_id for chunk in result.retrieval_chunks],
                "validator_reason_codes": result.validator_reason_codes,
                "action_types_after": action_types,
                "audit_path": result.audit_path,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
