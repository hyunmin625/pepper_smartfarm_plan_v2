#!/usr/bin/env python3
"""Run an offline/online smoke path through the LLM orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))

from llm_orchestrator import (  # noqa: E402
    LLMOrchestratorService,
    ModelConfig,
    OrchestratorRequest,
    get_resolved_model_reference,
)
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_request_payload(scenario_id: str, task_type: str, prompt_version: str) -> OrchestratorRequest:
    scenarios = {
        row["scenario_id"]: row
        for row in load_jsonl(REPO_ROOT / "data/examples/synthetic_sensor_scenarios.jsonl")
    }
    scenario = scenarios[scenario_id]
    zone_state = build_zone_state_payload(scenario)
    zone_state["state_estimate"] = estimate_zone_state(scenario).as_dict()
    zone_state["active_constraints"] = dict(scenario.get("constraints") or {})
    zone_state["current_state"]["summary"] = scenario["summary"]
    return OrchestratorRequest(
        request_id=f"smoke-{scenario_id}",
        zone_id=scenario["zone_id"],
        task_type=task_type,
        zone_state=zone_state,
        prompt_version=prompt_version,
        mode="shadow",
        farm_id=str(scenario.get("site_id") or "demo-farm"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_ORCHESTRATOR_PROVIDER", "stub"),
        choices=["stub", "openai", "gemini"],
    )
    parser.add_argument("--model-id", default=os.getenv("LLM_ORCHESTRATOR_MODEL_ID", "champion"))
    parser.add_argument("--prompt-version", default=os.getenv("LLM_ORCHESTRATOR_PROMPT_VERSION", "sft_v10"))
    parser.add_argument("--task-type", default="action_recommendation")
    parser.add_argument("--scenario-id", default="synthetic-002")
    args = parser.parse_args()

    request = build_request_payload(args.scenario_id, args.task_type, args.prompt_version)
    model_ref = get_resolved_model_reference(args.model_id)
    service = LLMOrchestratorService.from_model_config(
        ModelConfig(
            provider=args.provider,
            model_id=args.model_id,
        )
    )
    result = service.evaluate(request)
    print(
        json.dumps(
            {
                "provider": args.provider,
                "requested_model_id": args.model_id,
                "resolved_model_reference": model_ref.as_dict(),
                "request_id": result.request.request_id,
                "task_type": result.request.task_type,
                "prompt_version": result.request.prompt_version,
                "retrieval_chunk_ids": [chunk.chunk_id for chunk in result.retrieval_chunks],
                "tool_registry": [tool.name for tool in result.tool_catalog],
                "parse_result": {
                    "strict_json_ok": result.parse_result.strict_json_ok,
                    "recovered_json_ok": result.parse_result.recovered_json_ok,
                    "fallback_used": result.fallback_used,
                    "used_repair_prompt": result.used_repair_prompt,
                },
                "validator_reason_codes": result.validator_reason_codes,
                "validated_output": result.validated_output,
                "audit_path": result.audit_path,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
