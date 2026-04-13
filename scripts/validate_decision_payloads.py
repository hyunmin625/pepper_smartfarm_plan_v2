#!/usr/bin/env python3
"""Validate decision payload samples for the decision/action/state contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data/examples/decision_payload_samples.jsonl"

TASK_TYPES = {"zone_evaluation", "robot_prioritization", "shadow_review", "operator_replay", "alert_summary"}
RUNTIME_MODES = {"shadow", "approval", "auto", "manual", "simulation"}
STATUS_VALUES = {"evaluated", "approval_requested", "blocked", "approved", "rejected", "executed", "failed", "shadow_logged"}
POLICY_RESULTS = {"pass", "approval_required", "blocked", "not_evaluated"}
VALIDATOR_STATUS = {"pass", "rewritten", "blocked", "approval_required", "failed"}
APPROVAL_STATUS = {"pending", "approved", "rejected"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(item)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    errors: list[str] = []
    seen_decision_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"
        decision_id = row.get("decision_id")

        if row.get("schema_version") != "decision.v1":
            errors.append(f"{prefix}: schema_version must be decision.v1")

        if not isinstance(decision_id, str) or not decision_id:
            errors.append(f"{prefix}: decision_id must be a non-empty string")
            continue
        if decision_id in seen_decision_ids:
            errors.append(f"{prefix}: duplicate decision_id {decision_id}")
        seen_decision_ids.add(decision_id)

        if row.get("task_type") not in TASK_TYPES:
            errors.append(f"{prefix}: task_type is invalid")
        if row.get("runtime_mode") not in RUNTIME_MODES:
            errors.append(f"{prefix}: runtime_mode is invalid")
        if row.get("status") not in STATUS_VALUES:
            errors.append(f"{prefix}: status is invalid")

        state_snapshot = row.get("state_snapshot")
        if not isinstance(state_snapshot, dict) or state_snapshot.get("schema_version") != "state.v1":
            errors.append(f"{prefix}: state_snapshot.schema_version must be state.v1")

        action_payload = row.get("action_payload")
        if not isinstance(action_payload, dict) or action_payload.get("schema_version") != "action.v1":
            errors.append(f"{prefix}: action_payload.schema_version must be action.v1")
        elif action_payload.get("decision_id") != decision_id:
            errors.append(f"{prefix}: action_payload.decision_id must match decision_id")

        policy_summary = row.get("policy_summary")
        if not isinstance(policy_summary, dict) or policy_summary.get("final_result") not in POLICY_RESULTS:
            errors.append(f"{prefix}: policy_summary.final_result is invalid")

        validator_summary = row.get("validator_summary")
        if not isinstance(validator_summary, dict) or validator_summary.get("validator_status") not in VALIDATOR_STATUS:
            errors.append(f"{prefix}: validator_summary.validator_status is invalid")

        citations = row.get("citations")
        if not isinstance(citations, list) or not citations:
            errors.append(f"{prefix}: citations must be a non-empty array")

        retrieval_context = row.get("retrieval_context")
        if not isinstance(retrieval_context, list) or not retrieval_context:
            errors.append(f"{prefix}: retrieval_context must be a non-empty array")

        generated_requests = row.get("generated_requests", [])
        if not isinstance(generated_requests, list):
            errors.append(f"{prefix}: generated_requests must be an array")
        else:
            for request_index, request in enumerate(generated_requests, start=1):
                if not isinstance(request, dict):
                    errors.append(f"{prefix}: generated_requests[{request_index}] must be an object")
                    continue
                if request.get("schema_version") != "device_command_request.v1":
                    errors.append(f"{prefix}: generated_requests[{request_index}].schema_version is invalid")
                if request.get("source_decision_id") != decision_id:
                    errors.append(f"{prefix}: generated_requests[{request_index}].source_decision_id must match decision_id")

        robot_candidates = row.get("robot_candidates", [])
        candidate_ids = {
            candidate.get("candidate_id")
            for candidate in robot_candidates
            if isinstance(candidate, dict) and isinstance(candidate.get("candidate_id"), str)
        }

        robot_tasks = row.get("robot_tasks", [])
        if isinstance(robot_tasks, list):
            for task_index, task in enumerate(robot_tasks, start=1):
                if not isinstance(task, dict):
                    errors.append(f"{prefix}: robot_tasks[{task_index}] must be an object")
                    continue
                candidate_id = task.get("candidate_id")
                if candidate_id is not None and candidate_id not in candidate_ids:
                    errors.append(f"{prefix}: robot_tasks[{task_index}].candidate_id not found in robot_candidates")
        else:
            errors.append(f"{prefix}: robot_tasks must be an array")

        approval_request = row.get("approval_request")
        if approval_request is not None:
            if not isinstance(approval_request, dict) or approval_request.get("status") not in APPROVAL_STATUS:
                errors.append(f"{prefix}: approval_request.status is invalid")

        audit_refs = row.get("audit_refs")
        if not isinstance(audit_refs, dict) or not isinstance(audit_refs.get("audit_path"), str):
            errors.append(f"{prefix}: audit_refs.audit_path must be present")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
