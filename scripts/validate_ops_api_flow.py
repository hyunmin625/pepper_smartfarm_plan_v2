#!/usr/bin/env python3
"""Validate ops-api wiring without ASGI test client."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from llm_orchestrator import OrchestratorRequest  # noqa: E402
from ops_api.app import create_app  # noqa: E402
from ops_api.config import load_settings  # noqa: E402
from ops_api.models import ApprovalRecord, DecisionRecord, DeviceCommandRecord  # noqa: E402
from ops_api.runtime_mode import load_runtime_mode, save_runtime_mode  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ops-api-validate-") as tmp_dir:
        db_path = Path(tmp_dir) / "ops.db"
        mode_path = Path(tmp_dir) / "runtime_mode.json"
        os.environ["OPS_API_DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["OPS_API_RUNTIME_MODE_PATH"] = str(mode_path)
        os.environ["OPS_API_LLM_PROVIDER"] = "stub"
        os.environ["OPS_API_MODEL_ID"] = "pepper-ops-local-stub"

        app = create_app(load_settings())
        services = app.state.services
        routes = {route.path for route in app.router.routes}
        for expected_route in {
            "/runtime/mode",
            "/decisions/evaluate-zone",
            "/actions/approve",
            "/actions/reject",
            "/actions/history",
            "/dashboard",
        }:
            if expected_route not in routes:
                errors.append(f"missing route {expected_route}")

        runtime_mode = save_runtime_mode(
            services.settings.runtime_mode_path,
            mode="approval",
            actor_id="validator",
            reason="integration test",
        )
        if load_runtime_mode(services.settings.runtime_mode_path).mode != "approval":
            errors.append("runtime mode was not persisted")

        snapshot = {
            "zone_id": "gh-01-zone-a",
            "growth_stage": "fruiting",
            "current_state": {
                "air_temp_c": 31.2,
                "rh_pct": 84.0,
                "substrate_moisture_pct": 28.0,
                "ripe_fruit_count": 64,
            },
            "sensor_quality": {"overall": "bad", "temperature": "stale"},
            "constraints": {},
        }
        state_estimate = estimate_zone_state(snapshot)
        zone_state = build_zone_state_payload(snapshot)
        zone_state["active_constraints"] = {}
        zone_state["state_estimate"] = state_estimate.as_dict()
        zone_state["current_state"]["summary"] = "fruiting heat and humidity review"

        result = services.orchestrator.evaluate(
            OrchestratorRequest(
                request_id="ops-api-001",
                zone_id="gh-01-zone-a",
                task_type="action_recommendation",
                zone_state=zone_state,
                mode=runtime_mode.mode,
            )
        )

        session = services.session_factory()
        try:
            decision = DecisionRecord(
                request_id="ops-api-001",
                zone_id="gh-01-zone-a",
                task_type="action_recommendation",
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
            session.commit()
            session.refresh(decision)

            approval = ApprovalRecord(
                decision_id=decision.id,
                actor_id="operator-01",
                approval_status="approved",
                reason="integration approve",
                approval_payload_json=json.dumps({"decision_id": decision.id}, ensure_ascii=False),
            )
            session.add(approval)

            plans = services.planner.plan(
                decision_id=decision.id,
                request_id=decision.request_id,
                zone_id=decision.zone_id,
                validated_output=json.loads(decision.validated_output_json),
                actor_id="operator-01",
            )
            if not plans:
                errors.append("planner should generate at least one dispatch plan")

            dispatch_statuses: list[str] = []
            for plan in plans:
                if plan.kind == "device_command":
                    dispatch_result = services.dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(plan.payload)).as_dict()
                elif plan.kind == "control_override":
                    dispatch_result = services.dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(plan.payload)).as_dict()
                else:
                    dispatch_result = {"status": "logged_only"}
                dispatch_statuses.append(str(dispatch_result.get("status") or "unknown"))
                session.add(
                    DeviceCommandRecord(
                        decision_id=decision.id,
                        command_kind=plan.kind,
                        target_id=plan.target_id,
                        action_type=plan.action_type,
                        status=str(dispatch_result.get("status") or "unknown"),
                        payload_json=json.dumps(plan.payload, ensure_ascii=False),
                        adapter_result_json=json.dumps(dispatch_result, ensure_ascii=False),
                    )
                )

            decision.status = "approved_executed"
            session.commit()

            decision_count = session.query(DecisionRecord).count()
            approval_count = session.query(ApprovalRecord).count()
            command_count = session.query(DeviceCommandRecord).count()
            if decision_count != 1:
                errors.append(f"expected 1 decision row, found {decision_count}")
            if approval_count != 1:
                errors.append(f"expected 1 approval row, found {approval_count}")
            if command_count < 1:
                errors.append("expected at least 1 device command row")

            print(
                json.dumps(
                    {
                        "errors": errors,
                        "registered_routes": sorted(expected for expected in routes if expected in {
                            "/runtime/mode",
                            "/decisions/evaluate-zone",
                            "/actions/approve",
                            "/actions/reject",
                            "/actions/history",
                            "/dashboard",
                        }),
                        "runtime_mode": runtime_mode.as_dict(),
                        "decision_count": decision_count,
                        "approval_count": approval_count,
                        "command_count": command_count,
                        "dispatch_statuses": dispatch_statuses,
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
