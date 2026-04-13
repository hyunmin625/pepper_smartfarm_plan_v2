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

from llm_orchestrator import OrchestratorRequest  # noqa: E402
from ops_api.app import _build_dashboard_payload, _execute_decision_dispatch, create_app  # noqa: E402
from ops_api.config import load_settings  # noqa: E402
from ops_api.models import (  # noqa: E402
    ApprovalRecord,
    AlertRecord,
    DecisionRecord,
    DeviceRecord,
    DeviceCommandRecord,
    OperatorReviewRecord,
    PolicyEventRecord,
    PolicyEvaluationRecord,
    PolicyRecord,
    RobotTaskRecord,
    SensorRecord,
    ZoneRecord,
)
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
        expected_routes = {
            "/auth/me",
            "/runtime/mode",
            "/decisions/evaluate-zone",
            "/decisions",
            "/zones",
            "/zones/{zone_id}/history",
            "/sensors",
            "/devices",
            "/policies",
            "/policies/events",
            "/policies/{policy_id}",
            "/actions/approve",
            "/actions/execute",
            "/actions/reject",
            "/actions/history",
            "/dashboard",
            "/dashboard/data",
            "/alerts",
            "/robot/tasks",
            "/shadow/reviews",
            "/shadow/cases/capture",
            "/shadow/window",
            "/ai/chat",
        }
        for expected_route in expected_routes:
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
        zone_state["active_constraints"] = {
            "irrigation_path_degraded": True,
            "rootzone_sensor_conflict": True,
        }
        zone_state["state_estimate"] = state_estimate.as_dict()
        zone_state["current_state"]["summary"] = "fruiting heat and humidity review"
        zone_state["current_state"]["irrigation_path_degraded"] = True
        zone_state["current_state"]["rootzone_sensor_conflict"] = True

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
            validated_output = dict(result.validated_output)
            validated_output["recommended_actions"] = [
                {
                    "action_id": "ops-api-validate-short-irrigation",
                    "action_type": "short_irrigation",
                    "approval_required": False,
                    "target": {"target_type": "zone", "target_id": "gh-01-zone-a"},
                },
                {
                    "action_id": "ops-api-validate-adjust-fertigation",
                    "action_type": "adjust_fertigation",
                    "approval_required": False,
                    "target": {"target_type": "zone", "target_id": "gh-01-zone-a"},
                },
            ]

            zone_count = session.query(ZoneRecord).count()
            sensor_count = session.query(SensorRecord).count()
            device_count = session.query(DeviceRecord).count()
            policy_count_seed = session.query(PolicyRecord).count()
            if zone_count < 1:
                errors.append("expected seeded zones")
            if sensor_count < 1:
                errors.append("expected seeded sensors")
            if device_count < 1:
                errors.append("expected seeded devices")
            if policy_count_seed < 1:
                errors.append("expected seeded policies")

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
                validated_output_json=json.dumps(validated_output, ensure_ascii=False),
                zone_state_json=json.dumps(zone_state, ensure_ascii=False),
                citations_json=json.dumps(validated_output.get("citations", []), ensure_ascii=False),
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
            session.add(
                PolicyEvaluationRecord(
                    decision_id=decision.id,
                    policy_source="output_validator",
                    policy_result="approval_required",
                    reason_codes_json=json.dumps(result.validator_reason_codes, ensure_ascii=False),
                    evaluation_json=json.dumps(
                        {
                            "validated_output": validated_output,
                            "state_estimate": state_estimate.as_dict(),
                        },
                        ensure_ascii=False,
                    ),
                )
            )
            session.add(
                OperatorReviewRecord(
                    decision_id=decision.id,
                    actor_id="operator-01",
                    review_mode="shadow_review",
                    agreement_status="agree",
                    expected_risk_level=result.validated_output.get("risk_level"),
                expected_actions_json=json.dumps(
                        [action.get("action_type") for action in validated_output.get("recommended_actions", []) if isinstance(action, dict)],
                        ensure_ascii=False,
                    ),
                    expected_robot_tasks_json=json.dumps([], ensure_ascii=False),
                    note="integration shadow review",
                )
            )
            session.add(
                AlertRecord(
                    decision_id=decision.id,
                    zone_id=decision.zone_id,
                    alert_type=decision.task_type,
                    severity=result.validated_output.get("risk_level", "unknown"),
                    status="open",
                    summary=result.validated_output.get("situation_summary", "integration alert"),
                    validator_reason_codes_json=json.dumps(result.validator_reason_codes, ensure_ascii=False),
                payload_json=json.dumps(validated_output, ensure_ascii=False),
                )
            )
            session.add(
                RobotTaskRecord(
                    decision_id=decision.id,
                    zone_id=decision.zone_id,
                    candidate_id="integration-candidate-01",
                    task_type="inspect_crop",
                    priority="medium",
                    approval_required=False,
                    status="pending",
                    reason="integration robot check",
                    target_json=json.dumps(
                        {"target_type": "candidate", "target_id": "integration-candidate-01"},
                        ensure_ascii=False,
                    ),
                    payload_json=json.dumps({"actor_id": "operator-01"}, ensure_ascii=False),
                )
            )

            dispatch_results = _execute_decision_dispatch(
                decision=decision,
                actor_id="operator-01",
                services=services,
                session=session,
            )
            dispatch_statuses = [str(item.get("status") or "unknown") for item in dispatch_results]
            if not dispatch_results:
                errors.append("dispatch should generate at least one execution result")

            session.commit()

            decision_count = session.query(DecisionRecord).count()
            approval_count = session.query(ApprovalRecord).count()
            command_count = session.query(DeviceCommandRecord).count()
            policy_count = session.query(PolicyEvaluationRecord).count()
            policy_event_count = session.query(PolicyEventRecord).count()
            review_count = session.query(OperatorReviewRecord).count()
            alert_count = session.query(AlertRecord).count()
            robot_task_count = session.query(RobotTaskRecord).count()
            if decision_count != 1:
                errors.append(f"expected 1 decision row, found {decision_count}")
            if approval_count != 1:
                errors.append(f"expected 1 approval row, found {approval_count}")
            if command_count < 1:
                errors.append("expected at least 1 device command row")
            if policy_count != 1:
                errors.append(f"expected 1 policy evaluation row, found {policy_count}")
            if policy_event_count < 2:
                errors.append(f"expected at least 2 policy event rows, found {policy_event_count}")
            if review_count != 1:
                errors.append(f"expected 1 operator review row, found {review_count}")
            if alert_count != 1:
                errors.append(f"expected 1 alert row, found {alert_count}")
            if robot_task_count != 1:
                errors.append(f"expected 1 robot task row, found {robot_task_count}")

            dashboard_payload = _build_dashboard_payload(
                session,
                load_runtime_mode(services.settings.runtime_mode_path),
            )
            if dashboard_payload["summary"]["decision_count"] != 1:
                errors.append("dashboard decision count mismatch")
            if dashboard_payload["summary"]["command_count"] < 1:
                errors.append("dashboard command count mismatch")
            if dashboard_payload["summary"]["operator_agreement_rate"] != 1.0:
                errors.append("dashboard operator agreement rate mismatch")
            if len(dashboard_payload["zones"]) < 1:
                errors.append("dashboard zone overview mismatch")
            if dashboard_payload["summary"]["alert_count"] < 1:
                errors.append("dashboard alert count mismatch")
            if dashboard_payload["summary"]["robot_task_count"] < 1:
                errors.append("dashboard robot task count mismatch")
            if dashboard_payload["summary"]["policy_event_count"] < 2:
                errors.append("dashboard policy event count mismatch")
            if dashboard_payload["summary"]["policy_blocked_count"] < 1:
                errors.append("dashboard policy blocked count mismatch")

            print(
                json.dumps(
                    {
                        "errors": errors,
                        "registered_routes": sorted(expected for expected in routes if expected in expected_routes),
                        "runtime_mode": runtime_mode.as_dict(),
                        "decision_count": decision_count,
                        "approval_count": approval_count,
                        "command_count": command_count,
                        "policy_count": policy_count,
                        "policy_event_count": policy_event_count,
                        "review_count": review_count,
                        "alert_count": alert_count,
                        "robot_task_count": robot_task_count,
                        "seeded_counts": {
                            "zones": zone_count,
                            "sensors": sensor_count,
                            "devices": device_count,
                            "policies": policy_count_seed,
                        },
                        "dashboard_summary": dashboard_payload["summary"],
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
