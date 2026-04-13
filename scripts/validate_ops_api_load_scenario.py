#!/usr/bin/env python3
"""Run a minimal repeated ops-api load scenario on SQLite + stub LLM."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator import OrchestratorRequest  # noqa: E402
from ops_api.app import (  # noqa: E402
    _derive_policy_result,
    _execute_decision_dispatch,
    _record_approval,
    _refresh_alerts_for_decision,
    _refresh_robot_records_for_decision,
    create_app,
)
from ops_api.config import load_settings  # noqa: E402
from ops_api.models import (  # noqa: E402
    ApprovalRecord,
    DecisionRecord,
    DeviceCommandRecord,
    PolicyEvaluationRecord,
    RobotTaskRecord,
)
from ops_api.runtime_mode import load_runtime_mode, save_runtime_mode  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


def _percentile_ms(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * percentile))))
    return round(ordered[index], 2)


def _build_case(round_idx: int, task_type: str, zone_id: str) -> dict[str, object]:
    base_temp = 27.5 + (round_idx % 4) * 1.1
    base_rh = 70.0 + (round_idx % 3) * 4.0
    base_wc = 27.0 - (round_idx % 5) * 0.8
    current_state = {
        "air_temp_c": round(base_temp, 1),
        "rh_pct": round(base_rh, 1),
        "substrate_moisture_pct": round(base_wc, 1),
        "ripe_fruit_count": 40 + round_idx,
        "summary": f"{task_type} synthetic load case {round_idx}",
    }
    sensor_quality = {"overall": "good"}
    constraints: dict[str, object] = {}
    candidates: list[dict[str, object]] = []
    if task_type == "failure_response":
        sensor_quality = {"overall": "bad", "temperature": "stale"}
        constraints = {"core_water_path_degraded": True}
    if task_type == "forbidden_action":
        current_state["manual_override"] = True
        current_state["summary"] = "manual override load case"
    if task_type == "robot_task_prioritization":
        candidates = [
            {
                "candidate_id": f"{zone_id}-candidate-{round_idx:03d}",
                "candidate_type": "crop_candidate",
                "priority": "high",
                "status": "observed",
            }
        ]
    return {
        "zone_id": zone_id,
        "task_type": task_type,
        "growth_stage": "fruiting",
        "current_state": current_state,
        "sensor_quality": sensor_quality,
        "constraints": constraints,
        "candidates": candidates,
    }


def main() -> int:
    errors: list[str] = []
    decision_latencies_ms: list[float] = []
    full_cycle_latencies_ms: list[float] = []

    with tempfile.TemporaryDirectory(prefix="ops-api-load-") as tmp_dir:
        db_path = Path(tmp_dir) / "ops_load.db"
        runtime_mode_path = Path(tmp_dir) / "runtime_mode.json"
        os.environ["OPS_API_DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["OPS_API_RUNTIME_MODE_PATH"] = str(runtime_mode_path)
        os.environ["OPS_API_LLM_PROVIDER"] = "stub"
        os.environ["OPS_API_MODEL_ID"] = "pepper-ops-local-stub"

        app = create_app(load_settings())
        services = app.state.services
        save_runtime_mode(
            services.settings.runtime_mode_path,
            mode="approval",
            actor_id="load-test",
            reason="ops-api minimal load scenario",
        )
        runtime_mode = load_runtime_mode(services.settings.runtime_mode_path)

        total_started = time.perf_counter()
        session = services.session_factory()
        try:
            zone_task_pairs = [
                ("gh-01-zone-a", "action_recommendation"),
                ("gh-01-zone-b", "failure_response"),
                ("gh-02-zone-a", "forbidden_action"),
                ("gh-02-zone-b", "robot_task_prioritization"),
            ]
            rounds = 12
            expected_decisions = len(zone_task_pairs) * rounds

            for round_idx in range(rounds):
                for zone_id, task_type in zone_task_pairs:
                    case = _build_case(round_idx, task_type, zone_id)
                    started = time.perf_counter()
                    snapshot = {
                        "zone_id": case["zone_id"],
                        "growth_stage": case["growth_stage"],
                        "current_state": case["current_state"],
                        "history": {},
                        "sensor_quality": case["sensor_quality"],
                        "device_status": {},
                        "weather_context": {},
                        "constraints": case["constraints"],
                    }
                    state_estimate = estimate_zone_state(snapshot)
                    zone_state = build_zone_state_payload(snapshot)
                    zone_state["active_constraints"] = case["constraints"]
                    zone_state["state_estimate"] = state_estimate.as_dict()

                    result = services.orchestrator.evaluate(
                        OrchestratorRequest(
                            request_id=f"load-{round_idx:02d}-{zone_id}-{task_type}",
                            zone_id=zone_id,
                            task_type=task_type,
                            zone_state=zone_state,
                            mode=runtime_mode.mode,
                            prompt_version="sft_v10",
                        )
                    )
                    decision_latencies_ms.append(round((time.perf_counter() - started) * 1000, 2))

                    decision = DecisionRecord(
                        request_id=f"load-{round_idx:02d}-{zone_id}-{task_type}",
                        zone_id=zone_id,
                        task_type=task_type,
                        runtime_mode=runtime_mode.mode,
                        status="evaluated",
                        model_id=result.model_id,
                        prompt_version="sft_v10",
                        raw_output_json=json.dumps({"raw_text": result.raw_text}, ensure_ascii=False),
                        parsed_output_json=json.dumps(result.parsed_output, ensure_ascii=False),
                        validated_output_json=json.dumps(result.validated_output, ensure_ascii=False),
                        zone_state_json=json.dumps(zone_state, ensure_ascii=False),
                        citations_json=json.dumps(result.validated_output.get("citations", []), ensure_ascii=False),
                        retrieval_context_json=json.dumps([chunk.as_prompt_dict() for chunk in result.retrieval_chunks], ensure_ascii=False),
                        audit_path=result.audit_path,
                        validator_reason_codes_json=json.dumps(result.validator_reason_codes, ensure_ascii=False),
                    )
                    session.add(decision)
                    session.flush()
                    session.add(
                        PolicyEvaluationRecord(
                            decision_id=decision.id,
                            policy_source="output_validator",
                            policy_result=_derive_policy_result(result.validated_output, result.validator_reason_codes),
                            reason_codes_json=json.dumps(result.validator_reason_codes, ensure_ascii=False),
                            evaluation_json=json.dumps(
                                {
                                    "validated_output": result.validated_output,
                                    "state_estimate": state_estimate.as_dict(),
                                },
                                ensure_ascii=False,
                            ),
                        )
                    )
                    _refresh_alerts_for_decision(
                        session=session,
                        decision=decision,
                        validated_output=result.validated_output,
                        validator_reason_codes=result.validator_reason_codes,
                        zone_state=zone_state,
                    )
                    _refresh_robot_records_for_decision(
                        session=session,
                        decision=decision,
                        candidates=list(case["candidates"]),
                        validated_output=result.validated_output,
                    )
                    _record_approval(
                        session=session,
                        decision_id=decision.id,
                        actor_id="load-operator",
                        approval_status="approved",
                        reason="load scenario approve",
                        payload={"decision_id": decision.id},
                    )
                    _execute_decision_dispatch(
                        decision=decision,
                        actor_id="load-operator",
                        services=services,
                        session=session,
                    )
                    session.commit()
                    full_cycle_latencies_ms.append(round((time.perf_counter() - started) * 1000, 2))

            total_elapsed_ms = round((time.perf_counter() - total_started) * 1000, 2)
            decision_count = session.query(DecisionRecord).count()
            approval_count = session.query(ApprovalRecord).count()
            command_count = session.query(DeviceCommandRecord).count()
            robot_task_count = session.query(RobotTaskRecord).count()

            if decision_count != expected_decisions:
                errors.append(f"expected {expected_decisions} decisions, found {decision_count}")
            if approval_count != expected_decisions:
                errors.append(f"expected {expected_decisions} approvals, found {approval_count}")
            if command_count < expected_decisions // 2:
                errors.append(f"expected at least {expected_decisions // 2} command rows, found {command_count}")
            if robot_task_count < rounds:
                errors.append(f"expected at least {rounds} robot tasks, found {robot_task_count}")
            if _percentile_ms(full_cycle_latencies_ms, 0.95) > 5000:
                errors.append("full cycle p95 exceeded 5000ms in stub load scenario")

            print(
                json.dumps(
                    {
                        "errors": errors,
                        "rounds": rounds,
                        "zone_task_pairs": len(zone_task_pairs),
                        "decision_count": decision_count,
                        "approval_count": approval_count,
                        "command_count": command_count,
                        "robot_task_count": robot_task_count,
                        "total_elapsed_ms": total_elapsed_ms,
                        "throughput_decisions_per_sec": round(decision_count / max(total_elapsed_ms / 1000, 0.001), 2),
                        "decision_latency_ms": {
                            "p50": _percentile_ms(decision_latencies_ms, 0.50),
                            "p95": _percentile_ms(decision_latencies_ms, 0.95),
                            "max": round(max(decision_latencies_ms), 2) if decision_latencies_ms else 0.0,
                        },
                        "full_cycle_latency_ms": {
                            "p50": _percentile_ms(full_cycle_latencies_ms, 0.50),
                            "p95": _percentile_ms(full_cycle_latencies_ms, 0.95),
                            "max": round(max(full_cycle_latencies_ms), 2) if full_cycle_latencies_ms else 0.0,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
