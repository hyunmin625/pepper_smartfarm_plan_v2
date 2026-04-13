from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from .api_models import (
    ApprovalRequest,
    ApiResponse,
    EvaluateZoneRequest,
    ErrorResponse,
    ExecuteActionRequest,
    RobotTaskCreateRequest,
    ShadowCaptureRequest,
    RuntimeModeRequest,
    ShadowReviewRequest,
)
from .auth import ActorIdentity, get_authenticated_actor, require_permission
from .bootstrap import configure_repo_paths
from .config import Settings, load_settings
from .database import build_session_factory, init_db
from .errors import register_exception_handlers
from .logging import configure_logging
from .models import (
    ApprovalRecord,
    AlertRecord,
    DecisionRecord,
    DeviceRecord,
    DeviceCommandRecord,
    OperatorReviewRecord,
    PolicyEvaluationRecord,
    PolicyRecord,
    RobotCandidateRecord,
    RobotTaskRecord,
    SensorRecord,
    ZoneRecord,
)
from .planner import ActionDispatchPlanner
from .runtime_mode import load_runtime_mode, save_runtime_mode
from .seed import bootstrap_reference_data
from .shadow_mode import build_window_summary_from_paths, capture_shadow_cases

configure_repo_paths()

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402
from llm_orchestrator import LLMOrchestratorService, ModelConfig, OrchestratorRequest  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


logger = logging.getLogger(__name__)


@dataclass
class AppServices:
    settings: Settings
    session_factory: sessionmaker[Session]
    orchestrator: LLMOrchestratorService
    dispatcher: ExecutionDispatcher
    planner: ActionDispatchPlanner


def _loads_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _derive_policy_result(validated_output: dict[str, Any], validator_reason_codes: list[str]) -> str:
    decision = str(validated_output.get("decision") or "")
    if decision in {"block", "approval_required"}:
        return decision
    recommended_actions = validated_output.get("recommended_actions")
    if isinstance(recommended_actions, list):
        for action in recommended_actions:
            if isinstance(action, dict) and bool(action.get("approval_required")):
                return "approval_required"
    if any(code.startswith("HSV-") for code in validator_reason_codes):
        return "block"
    if validator_reason_codes:
        return "adjusted"
    return "pass"


def _actor_model(actor: ActorIdentity | None) -> dict[str, str] | None:
    return None if actor is None else actor.as_dict()


def _ok(data: Any, *, actor: ActorIdentity | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "meta": meta or {},
        "actor": _actor_model(actor),
    }


def _latest_approval(decision: DecisionRecord) -> ApprovalRecord | None:
    if not decision.approvals:
        return None
    return max(decision.approvals, key=lambda row: row.id)


def _latest_shadow_review(decision: DecisionRecord) -> OperatorReviewRecord | None:
    shadow_reviews = [row for row in decision.operator_reviews if row.review_mode == "shadow_review"]
    if not shadow_reviews:
        return None
    return max(shadow_reviews, key=lambda row: row.id)


def _build_decision_item(decision: DecisionRecord) -> dict[str, Any]:
    validated_output = _loads_json(decision.validated_output_json, {})
    zone_state = _loads_json(decision.zone_state_json, {})
    citations = _loads_json(decision.citations_json, [])
    validator_reason_codes = _loads_json(decision.validator_reason_codes_json, [])
    latest_approval = _latest_approval(decision)
    latest_shadow_review = _latest_shadow_review(decision)
    recommended_actions = validated_output.get("recommended_actions")
    robot_tasks = validated_output.get("robot_tasks")
    current_state = zone_state.get("current_state", {})
    risk_level = str(validated_output.get("risk_level") or "unknown")
    return {
        "decision_id": decision.id,
        "request_id": decision.request_id,
        "zone_id": decision.zone_id,
        "task_type": decision.task_type,
        "runtime_mode": decision.runtime_mode,
        "status": decision.status,
        "model_id": decision.model_id,
        "prompt_version": decision.prompt_version,
        "validated_output": validated_output,
        "citations": citations,
        "validator_reason_codes": validator_reason_codes,
        "risk_level": risk_level,
        "recommended_action_types": [
            str(action.get("action_type") or "")
            for action in (recommended_actions if isinstance(recommended_actions, list) else [])
            if isinstance(action, dict)
        ],
        "robot_task_types": [
            str(task.get("task_type") or "")
            for task in (robot_tasks if isinstance(robot_tasks, list) else [])
            if isinstance(task, dict)
        ],
        "current_state_summary": str(current_state.get("summary") or ""),
        "sensor_quality": zone_state.get("sensor_quality", {}),
        "zone_state": zone_state,
        "latest_approval": None
        if latest_approval is None
        else {
            "approval_status": latest_approval.approval_status,
            "actor_id": latest_approval.actor_id,
            "reason": latest_approval.reason,
            "created_at": latest_approval.created_at.isoformat(),
        },
        "latest_shadow_review": None
        if latest_shadow_review is None
        else {
            "agreement_status": latest_shadow_review.agreement_status,
            "actor_id": latest_shadow_review.actor_id,
            "note": latest_shadow_review.note,
            "expected_risk_level": latest_shadow_review.expected_risk_level,
            "created_at": latest_shadow_review.created_at.isoformat(),
        },
        "created_at": decision.created_at.isoformat(),
    }


def _serialize_zone(row: ZoneRecord) -> dict[str, Any]:
    return {
        "zone_id": row.zone_id,
        "zone_type": row.zone_type,
        "priority": row.priority,
        "description": row.description,
        "metadata": _loads_json(row.metadata_json, {}),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _serialize_sensor(row: SensorRecord) -> dict[str, Any]:
    return {
        "sensor_id": row.sensor_id,
        "zone_id": row.zone_id,
        "sensor_type": row.sensor_type,
        "measurement_fields": _loads_json(row.measurement_fields_json, []),
        "unit": row.unit,
        "raw_sample_seconds": row.raw_sample_seconds,
        "ai_aggregation_seconds": row.ai_aggregation_seconds,
        "priority": row.priority,
        "model_profile": row.model_profile,
        "protocol": row.protocol,
        "install_location": row.install_location,
        "calibration_interval_days": row.calibration_interval_days,
        "redundancy_group": row.redundancy_group,
        "quality_flags": _loads_json(row.quality_flags_json, []),
        "metadata": _loads_json(row.metadata_json, {}),
    }


def _serialize_device(row: DeviceRecord) -> dict[str, Any]:
    return {
        "device_id": row.device_id,
        "zone_id": row.zone_id,
        "device_type": row.device_type,
        "priority": row.priority,
        "model_profile": row.model_profile,
        "controller_id": row.controller_id,
        "protocol": row.protocol,
        "control_mode": row.control_mode,
        "response_timeout_seconds": row.response_timeout_seconds,
        "write_channel_ref": row.write_channel_ref,
        "read_channel_refs": _loads_json(row.read_channel_refs_json, []),
        "supported_action_types": _loads_json(row.supported_action_types_json, []),
        "safety_interlocks": _loads_json(row.safety_interlocks_json, []),
        "metadata": _loads_json(row.metadata_json, {}),
    }


def _serialize_policy(row: PolicyRecord) -> dict[str, Any]:
    return {
        "policy_id": row.policy_id,
        "policy_stage": row.policy_stage,
        "severity": row.severity,
        "enabled": row.enabled,
        "description": row.description,
        "trigger_flags": _loads_json(row.trigger_flags_json, []),
        "enforcement": _loads_json(row.enforcement_json, {}),
        "source_version": row.source_version,
        "updated_at": row.updated_at.isoformat(),
    }


def _serialize_alert(row: AlertRecord) -> dict[str, Any]:
    return {
        "alert_id": row.id,
        "decision_id": row.decision_id,
        "zone_id": row.zone_id,
        "alert_type": row.alert_type,
        "severity": row.severity,
        "status": row.status,
        "summary": row.summary,
        "validator_reason_codes": _loads_json(row.validator_reason_codes_json, []),
        "payload": _loads_json(row.payload_json, {}),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _serialize_robot_task(row: RobotTaskRecord) -> dict[str, Any]:
    return {
        "task_id": row.id,
        "decision_id": row.decision_id,
        "zone_id": row.zone_id,
        "candidate_id": row.candidate_id,
        "task_type": row.task_type,
        "priority": row.priority,
        "approval_required": row.approval_required,
        "status": row.status,
        "reason": row.reason,
        "target": _loads_json(row.target_json, {}),
        "payload": _loads_json(row.payload_json, {}),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _refresh_alerts_for_decision(
    *,
    session: Session,
    decision: DecisionRecord,
    validated_output: dict[str, Any],
    validator_reason_codes: list[str],
    zone_state: dict[str, Any],
) -> None:
    session.query(AlertRecord).filter(AlertRecord.decision_id == decision.id).delete()
    risk_level = str(validated_output.get("risk_level") or "unknown")
    should_alert = risk_level in {"high", "critical", "unknown"} or bool(validator_reason_codes)
    if not should_alert:
        return
    summary = str(
        validated_output.get("situation_summary")
        or zone_state.get("current_state", {}).get("summary")
        or f"{decision.task_type} alert"
    )
    session.add(
        AlertRecord(
            decision_id=decision.id,
            zone_id=decision.zone_id,
            alert_type=decision.task_type,
            severity=risk_level,
            status="open",
            summary=summary,
            validator_reason_codes_json=json.dumps(validator_reason_codes, ensure_ascii=False),
            payload_json=json.dumps(
                {
                    "validated_output": validated_output,
                    "zone_state": zone_state,
                },
                ensure_ascii=False,
            ),
        )
    )


def _refresh_robot_records_for_decision(
    *,
    session: Session,
    decision: DecisionRecord,
    candidates: list[dict[str, Any]],
    validated_output: dict[str, Any],
) -> None:
    session.query(RobotCandidateRecord).filter(RobotCandidateRecord.decision_id == decision.id).delete()
    session.query(RobotTaskRecord).filter(RobotTaskRecord.decision_id == decision.id).delete()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        existing = (
            session.query(RobotCandidateRecord)
            .filter(RobotCandidateRecord.candidate_id == candidate_id)
            .one_or_none()
        )
        record = existing or RobotCandidateRecord(candidate_id=candidate_id)
        record.decision_id = decision.id
        record.zone_id = decision.zone_id
        record.candidate_type = str(candidate.get("candidate_type") or "crop_candidate")
        record.priority = str(candidate.get("priority") or "medium")
        record.status = str(candidate.get("status") or "observed")
        record.payload_json = json.dumps(candidate, ensure_ascii=False)
        if existing is None:
            session.add(record)
    for task in validated_output.get("robot_tasks", []):
        if not isinstance(task, dict):
            continue
        session.add(
            RobotTaskRecord(
                decision_id=decision.id,
                zone_id=decision.zone_id,
                candidate_id=(str(task.get("candidate_id")) if task.get("candidate_id") is not None else None),
                task_type=str(task.get("task_type") or "manual_review"),
                priority=str(task.get("priority") or "medium"),
                approval_required=bool(task.get("approval_required", False)),
                status="pending",
                reason=str(task.get("reason") or ""),
                target_json=json.dumps(task.get("target", {}), ensure_ascii=False),
                payload_json=json.dumps(task, ensure_ascii=False),
            )
        )


def _record_approval(
    *,
    session: Session,
    decision_id: int,
    actor_id: str,
    approval_status: str,
    reason: str,
    payload: dict[str, Any],
) -> ApprovalRecord:
    record = ApprovalRecord(
        decision_id=decision_id,
        actor_id=actor_id,
        approval_status=approval_status,
        reason=reason,
        approval_payload_json=json.dumps(payload, ensure_ascii=False),
    )
    session.add(record)
    session.flush()
    return record


def _execute_decision_dispatch(
    *,
    decision: DecisionRecord,
    actor_id: str,
    services: AppServices,
    session: Session,
) -> list[dict[str, Any]]:
    validated_output = json.loads(decision.validated_output_json)
    plans = services.planner.plan(
        decision_id=decision.id,
        request_id=decision.request_id,
        zone_id=decision.zone_id,
        validated_output=validated_output,
        actor_id=actor_id,
    )
    dispatch_results: list[dict[str, Any]] = []
    for plan in plans:
        if plan.kind == "device_command":
            dispatch_result = services.dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(plan.payload)).as_dict()
        elif plan.kind == "control_override":
            dispatch_result = services.dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(plan.payload)).as_dict()
        else:
            dispatch_result = {"status": "logged_only", "allow_dispatch": False, "reasons": ["non_dispatchable_action"]}
        dispatch_results.append(dispatch_result)
        session.add(
            DeviceCommandRecord(
                decision_id=decision.id,
                command_kind=plan.kind,
                target_id=plan.target_id,
                action_type=plan.action_type,
                status=str(dispatch_result.get("status") or "logged_only"),
                payload_json=json.dumps(plan.payload, ensure_ascii=False),
                adapter_result_json=json.dumps(dispatch_result, ensure_ascii=False),
            )
        )
    decision.status = "approved_executed"
    return dispatch_results


def _build_dashboard_payload(session: Session, mode_state: Any) -> dict[str, Any]:
    rows = session.execute(select(DecisionRecord).order_by(desc(DecisionRecord.id)).limit(40)).scalars().all()
    command_rows = session.execute(select(DeviceCommandRecord).order_by(desc(DeviceCommandRecord.id)).limit(30)).scalars().all()
    zone_rows = session.execute(select(ZoneRecord).order_by(ZoneRecord.zone_id)).scalars().all()
    alert_rows = session.execute(select(AlertRecord).order_by(desc(AlertRecord.id)).limit(30)).scalars().all()
    robot_rows = session.execute(select(RobotTaskRecord).order_by(desc(RobotTaskRecord.id)).limit(30)).scalars().all()
    decision_items = [_build_decision_item(row) for row in rows]
    latest_zone_items: dict[str, dict[str, Any]] = {
        zone.zone_id: {
            "zone_id": zone.zone_id,
            "zone_type": zone.zone_type,
            "priority": zone.priority,
            "description": zone.description,
            "decision_id": None,
            "task_type": None,
            "status": "catalog_only",
            "risk_level": None,
            "current_state_summary": "",
            "sensor_quality": {},
            "created_at": zone.updated_at.isoformat(),
        }
        for zone in zone_rows
    }
    approval_pending_count = 0
    shadow_review_pending_count = 0
    blocked_action_count = 0
    safe_mode_count = 0
    disagreement_count = 0

    for item in decision_items:
        if item["zone_id"] not in latest_zone_items:
            latest_zone_items[item["zone_id"]] = {
                "zone_id": item["zone_id"],
                "decision_id": item["decision_id"],
                "task_type": item["task_type"],
                "status": item["status"],
                "risk_level": item["risk_level"],
                "current_state_summary": item["current_state_summary"],
                "sensor_quality": item["sensor_quality"],
                "created_at": item["created_at"],
            }

        if item["runtime_mode"] == "approval" and item["status"] == "evaluated":
            approval_pending_count += 1
        if item["runtime_mode"] == "shadow" and item["status"] == "evaluated":
            shadow_review_pending_count += 1
        if item["latest_shadow_review"] and item["latest_shadow_review"]["agreement_status"] == "disagree":
            disagreement_count += 1

        if item["validated_output"].get("decision") == "block":
            blocked_action_count += 1
        if "enter_safe_mode" in item["recommended_action_types"]:
            safe_mode_count += 1

    agreement_rows = [item for item in decision_items if item["latest_shadow_review"]]
    agree_count = sum(
        1
        for item in agreement_rows
        if item["latest_shadow_review"] and item["latest_shadow_review"]["agreement_status"] == "agree"
    )
    operator_agreement_rate = round(agree_count / len(agreement_rows), 4) if agreement_rows else None
    shadow_window_summary = None

    return {
        "runtime_mode": mode_state.as_dict(),
        "summary": {
            "decision_count": len(decision_items),
            "approval_pending_count": approval_pending_count,
            "shadow_review_pending_count": shadow_review_pending_count,
            "blocked_action_count": blocked_action_count,
            "safe_mode_count": safe_mode_count,
            "operator_disagreement_count": disagreement_count,
            "operator_agreement_rate": operator_agreement_rate,
            "command_count": len(command_rows),
            "alert_count": len(alert_rows),
            "robot_task_count": len(robot_rows),
        },
        "shadow_window": shadow_window_summary,
        "zones": list(latest_zone_items.values()),
        "alerts": [_serialize_alert(row) for row in alert_rows[:12]],
        "robot_tasks": [_serialize_robot_task(row) for row in robot_rows[:12]],
        "decisions": decision_items,
        "commands": [
            {
                "id": row.id,
                "decision_id": row.decision_id,
                "command_kind": row.command_kind,
                "target_id": row.target_id,
                "action_type": row.action_type,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in command_rows
        ],
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or load_settings()
    session_factory = build_session_factory(resolved_settings.database_url)
    init_db(session_factory)
    bootstrap_reference_data(session_factory)
    current_mode = load_runtime_mode(resolved_settings.runtime_mode_path)
    save_runtime_mode(
        resolved_settings.runtime_mode_path,
        mode=current_mode.mode,
        actor_id=current_mode.actor_id,
        reason=current_mode.reason,
    )
    services = AppServices(
        settings=resolved_settings,
        session_factory=session_factory,
        orchestrator=LLMOrchestratorService.from_model_config(
            ModelConfig(
                provider=resolved_settings.llm_provider,
                model_id=resolved_settings.llm_model_id,
                timeout_seconds=resolved_settings.llm_timeout_seconds,
                max_retries=resolved_settings.llm_max_retries,
            )
        ),
        dispatcher=ExecutionDispatcher.default(adapter_kind="mock"),
        planner=ActionDispatchPlanner(),
    )

    app = FastAPI(
        title="Pepper Smartfarm Ops API",
        version="0.2.0",
        description="LLM 의사결정, approval dispatch, shadow review, 운영 카탈로그를 제공하는 백엔드",
        openapi_tags=[
            {"name": "system", "description": "health, auth, runtime mode"},
            {"name": "decisions", "description": "LLM evaluation and history"},
            {"name": "catalog", "description": "zones, sensors, devices, policies"},
            {"name": "operations", "description": "approvals, execute, alerts, robot tasks"},
            {"name": "dashboard", "description": "operator dashboard and shadow review"},
        ],
    )
    app.state.services = services
    register_exception_handlers(app)

    def get_services():
        return app.state.services

    def get_session(services=Depends(get_services)):
        session = services.session_factory()
        try:
            yield session
        finally:
            session.close()

    @app.get("/health", tags=["system"], response_model=ApiResponse)
    def health(services=Depends(get_services)) -> dict[str, Any]:
        mode_state = load_runtime_mode(services.settings.runtime_mode_path)
        return _ok({"status": "ok", "runtime_mode": mode_state.as_dict()})

    @app.get("/auth/me", tags=["system"], response_model=ApiResponse)
    def auth_me(actor: ActorIdentity = Depends(get_authenticated_actor)) -> dict[str, Any]:
        return _ok(actor.as_dict(), actor=actor)

    @app.get("/runtime/mode", tags=["system"], response_model=ApiResponse)
    def get_runtime_mode(
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        return _ok(load_runtime_mode(services.settings.runtime_mode_path).as_dict(), actor=actor)

    @app.post("/runtime/mode", tags=["system"], response_model=ApiResponse, responses={403: {"model": ErrorResponse}})
    def set_runtime_mode(
        payload: RuntimeModeRequest,
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("manage_runtime_mode")),
    ) -> dict[str, Any]:
        state = save_runtime_mode(
            services.settings.runtime_mode_path,
            mode=payload.mode,
            actor_id=actor.actor_id,
            reason=payload.reason,
        )
        return _ok({"runtime_mode": state.as_dict()}, actor=actor)

    @app.post(
        "/decisions/evaluate-zone",
        tags=["decisions"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def evaluate_zone(
        payload: EvaluateZoneRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("evaluate_zone")),
    ) -> dict[str, Any]:
        mode_state = load_runtime_mode(services.settings.runtime_mode_path)
        effective_mode = payload.mode or mode_state.mode
        snapshot = {
            "zone_id": payload.zone_id,
            "growth_stage": payload.growth_stage,
            "current_state": payload.current_state,
            "history": payload.history,
            "sensor_quality": payload.sensor_quality,
            "device_status": payload.device_status,
            "weather_context": payload.weather_context,
            "constraints": payload.constraints,
        }
        state_estimate = estimate_zone_state(snapshot)
        zone_state = build_zone_state_payload(snapshot)
        zone_state["active_constraints"] = payload.constraints
        zone_state["current_state"]["summary"] = (
            zone_state["current_state"].get("summary")
            or f"{state_estimate.risk_level} risk; recommended {', '.join(state_estimate.recommended_action_types)}"
        )
        zone_state["state_estimate"] = state_estimate.as_dict()

        result = services.orchestrator.evaluate(
            OrchestratorRequest(
                request_id=payload.request_id,
                zone_id=payload.zone_id,
                task_type=payload.task_type,
                zone_state=zone_state,
                prompt_version=payload.prompt_version,
                retrieval_limit=payload.retrieval_limit,
                mode=effective_mode,
            )
        )

        decision = DecisionRecord(
            request_id=payload.request_id,
            zone_id=payload.zone_id,
            task_type=payload.task_type,
            runtime_mode=effective_mode,
            status="evaluated",
            model_id=result.model_id,
            prompt_version=payload.prompt_version,
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
            candidates=payload.candidates,
            validated_output=result.validated_output,
        )
        session.commit()
        session.refresh(decision)
        return _ok(
            {
                "decision_id": decision.id,
                "runtime_mode": effective_mode,
                "state_estimate": state_estimate.as_dict(),
                "validated_output": result.validated_output,
                "citations": result.validated_output.get("citations", []),
                "retrieval_context": [chunk.as_prompt_dict() for chunk in result.retrieval_chunks],
                "validator_reason_codes": result.validator_reason_codes,
            },
            actor=actor,
        )

    @app.get(
        "/decisions",
        tags=["decisions"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_decisions(
        limit: int = 30,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        rows = session.execute(select(DecisionRecord).order_by(desc(DecisionRecord.id)).limit(limit)).scalars().all()
        return _ok(
            {
                "items": [
                    {
                        "decision_id": row.id,
                        "request_id": row.request_id,
                        "zone_id": row.zone_id,
                        "task_type": row.task_type,
                        "runtime_mode": row.runtime_mode,
                        "status": row.status,
                        "model_id": row.model_id,
                        "validated_output": _loads_json(row.validated_output_json, {}),
                        "citations": _loads_json(row.citations_json, []),
                        "validator_reason_codes": _loads_json(row.validator_reason_codes_json, []),
                        "current_state_summary": _loads_json(row.zone_state_json, {}).get("current_state", {}).get("summary", ""),
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in rows
                ]
            },
            actor=actor,
            meta={"limit": limit},
        )

    @app.get(
        "/zones",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_zones(
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_catalog")),
    ) -> dict[str, Any]:
        rows = session.execute(select(ZoneRecord).order_by(ZoneRecord.zone_id)).scalars().all()
        return _ok({"items": [_serialize_zone(row) for row in rows]}, actor=actor)

    @app.get(
        "/zones/{zone_id}/history",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def get_zone_history(
        zone_id: str,
        limit: int = 20,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        decision_rows = session.execute(
            select(DecisionRecord)
            .where(DecisionRecord.zone_id == zone_id)
            .order_by(desc(DecisionRecord.id))
            .limit(limit)
        ).scalars().all()
        alert_rows = session.execute(
            select(AlertRecord)
            .where(AlertRecord.zone_id == zone_id)
            .order_by(desc(AlertRecord.id))
            .limit(limit)
        ).scalars().all()
        command_rows = session.execute(
            select(DeviceCommandRecord)
            .join(DecisionRecord, DeviceCommandRecord.decision_id == DecisionRecord.id)
            .where(DecisionRecord.zone_id == zone_id)
            .order_by(desc(DeviceCommandRecord.id))
            .limit(limit)
        ).scalars().all()
        robot_rows = session.execute(
            select(RobotTaskRecord)
            .where(RobotTaskRecord.zone_id == zone_id)
            .order_by(desc(RobotTaskRecord.id))
            .limit(limit)
        ).scalars().all()
        return _ok(
            {
                "zone_id": zone_id,
                "decisions": [_build_decision_item(row) for row in decision_rows],
                "alerts": [_serialize_alert(row) for row in alert_rows],
                "commands": [
                    {
                        "id": row.id,
                        "decision_id": row.decision_id,
                        "command_kind": row.command_kind,
                        "target_id": row.target_id,
                        "action_type": row.action_type,
                        "status": row.status,
                        "payload": _loads_json(row.payload_json, {}),
                        "adapter_result": _loads_json(row.adapter_result_json, {}),
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in command_rows
                ],
                "robot_tasks": [_serialize_robot_task(row) for row in robot_rows],
            },
            actor=actor,
            meta={"zone_id": zone_id, "limit": limit},
        )

    @app.get(
        "/sensors",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_sensors(
        zone_id: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_catalog")),
    ) -> dict[str, Any]:
        stmt = select(SensorRecord).order_by(SensorRecord.sensor_id)
        if zone_id:
            stmt = stmt.where(SensorRecord.zone_id == zone_id)
        rows = session.execute(stmt).scalars().all()
        return _ok({"items": [_serialize_sensor(row) for row in rows]}, actor=actor, meta={"zone_id": zone_id})

    @app.get(
        "/devices",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_devices(
        zone_id: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_catalog")),
    ) -> dict[str, Any]:
        stmt = select(DeviceRecord).order_by(DeviceRecord.device_id)
        if zone_id:
            stmt = stmt.where(DeviceRecord.zone_id == zone_id)
        rows = session.execute(stmt).scalars().all()
        return _ok({"items": [_serialize_device(row) for row in rows]}, actor=actor, meta={"zone_id": zone_id})

    @app.get(
        "/policies",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_policies(
        enabled_only: bool = False,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_catalog")),
    ) -> dict[str, Any]:
        stmt = select(PolicyRecord).order_by(PolicyRecord.policy_stage, PolicyRecord.policy_id)
        if enabled_only:
            stmt = stmt.where(PolicyRecord.enabled.is_(True))
        rows = session.execute(stmt).scalars().all()
        return _ok({"items": [_serialize_policy(row) for row in rows]}, actor=actor, meta={"enabled_only": enabled_only})

    @app.post(
        "/shadow/reviews",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def create_shadow_review(
        payload: ShadowReviewRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("review_shadow")),
    ) -> dict[str, Any]:
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        runtime_mode = load_runtime_mode(services.settings.runtime_mode_path)
        review = OperatorReviewRecord(
            decision_id=decision.id,
            actor_id=actor.actor_id,
            review_mode="shadow_review" if runtime_mode.mode == "shadow" else "posthoc_review",
            agreement_status=payload.agreement_status,
            expected_risk_level=payload.expected_risk_level,
            expected_actions_json=json.dumps(payload.expected_actions, ensure_ascii=False),
            expected_robot_tasks_json=json.dumps(payload.expected_robot_tasks, ensure_ascii=False),
            note=payload.note,
        )
        session.add(review)
        if decision.runtime_mode == "shadow" and decision.status == "evaluated":
            decision.status = (
                "shadow_reviewed_agree"
                if payload.agreement_status == "agree"
                else "shadow_reviewed_disagree"
            )
        session.commit()
        session.refresh(review)
        return _ok(
            {
                "decision_id": decision.id,
                "review_id": review.id,
                "agreement_status": payload.agreement_status,
            },
            actor=actor,
        )

    @app.get(
        "/shadow/reviews",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_shadow_reviews(
        limit: int = 50,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        rows = session.execute(
            select(OperatorReviewRecord).order_by(desc(OperatorReviewRecord.id)).limit(limit)
        ).scalars().all()
        return _ok(
            {
                "items": [
                    {
                        "review_id": row.id,
                        "decision_id": row.decision_id,
                        "actor_id": row.actor_id,
                        "review_mode": row.review_mode,
                        "agreement_status": row.agreement_status,
                        "expected_risk_level": row.expected_risk_level,
                        "expected_actions": _loads_json(row.expected_actions_json, []),
                        "expected_robot_tasks": _loads_json(row.expected_robot_tasks_json, []),
                        "note": row.note,
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in rows
                ]
            },
            actor=actor,
            meta={"limit": limit},
        )

    @app.post(
        "/shadow/cases/capture",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def capture_shadow_runtime_cases(
        payload: ShadowCaptureRequest,
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("review_shadow")),
    ) -> dict[str, Any]:
        summary = capture_shadow_cases(
            [item.model_dump() for item in payload.cases],
            shadow_audit_log_path=services.settings.shadow_audit_log_path,
            validator_audit_log_path=services.settings.validator_audit_log_path,
            append=payload.append,
        )
        return _ok(
            {
                "captured_case_count": len(payload.cases),
                "shadow_window": summary,
            },
            actor=actor,
        )

    @app.get(
        "/shadow/window",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def get_shadow_window_summary(
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        audit_path = services.settings.shadow_audit_log_path
        if not audit_path.exists():
            raise HTTPException(status_code=404, detail="shadow audit log not found")
        try:
            summary = build_window_summary_from_paths([audit_path])
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _ok(summary, actor=actor)

    @app.get(
        "/zones/{zone_id}/state",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def get_zone_state(
        zone_id: str,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        row = session.execute(
            select(DecisionRecord)
            .where(DecisionRecord.zone_id == zone_id)
            .order_by(desc(DecisionRecord.id))
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="zone state not found")
        return _ok(
            {
                "zone_id": zone_id,
                "zone_state": json.loads(row.zone_state_json),
                "decision_id": row.id,
                "updated_at": row.updated_at.isoformat(),
            },
            actor=actor,
        )

    @app.get(
        "/actions/history",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def action_history(
        limit: int = 50,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        rows = session.execute(select(DeviceCommandRecord).order_by(desc(DeviceCommandRecord.id)).limit(limit)).scalars().all()
        return _ok(
            {
                "items": [
                    {
                        "id": row.id,
                        "decision_id": row.decision_id,
                        "command_kind": row.command_kind,
                        "target_id": row.target_id,
                        "action_type": row.action_type,
                        "status": row.status,
                        "payload": json.loads(row.payload_json),
                        "adapter_result": json.loads(row.adapter_result_json),
                        "created_at": row.created_at.isoformat(),
                    }
                    for row in rows
                ]
            },
            actor=actor,
            meta={"limit": limit},
        )

    @app.get(
        "/dashboard/data",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def dashboard_data(
        session: Session = Depends(get_session),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        payload = _build_dashboard_payload(session, load_runtime_mode(services.settings.runtime_mode_path))
        audit_path = services.settings.shadow_audit_log_path
        if audit_path.exists():
            try:
                payload["shadow_window"] = build_window_summary_from_paths([audit_path])
            except ValueError:
                payload["shadow_window"] = None
        return _ok(payload, actor=actor)

    @app.get(
        "/alerts",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_alerts(
        zone_id: str | None = None,
        status: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        stmt = select(AlertRecord).order_by(desc(AlertRecord.id))
        if zone_id:
            stmt = stmt.where(AlertRecord.zone_id == zone_id)
        if status:
            stmt = stmt.where(AlertRecord.status == status)
        rows = session.execute(stmt.limit(50)).scalars().all()
        return _ok({"items": [_serialize_alert(row) for row in rows]}, actor=actor, meta={"zone_id": zone_id, "status": status})

    @app.get(
        "/robot/tasks",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_robot_tasks(
        zone_id: str | None = None,
        status: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        stmt = select(RobotTaskRecord).order_by(desc(RobotTaskRecord.id))
        if zone_id:
            stmt = stmt.where(RobotTaskRecord.zone_id == zone_id)
        if status:
            stmt = stmt.where(RobotTaskRecord.status == status)
        rows = session.execute(stmt.limit(50)).scalars().all()
        return _ok({"items": [_serialize_robot_task(row) for row in rows]}, actor=actor, meta={"zone_id": zone_id, "status": status})

    @app.post(
        "/robot/tasks",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def create_robot_task(
        payload: RobotTaskCreateRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("write_robot_tasks")),
    ) -> dict[str, Any]:
        row = RobotTaskRecord(
            decision_id=payload.decision_id,
            zone_id=payload.zone_id,
            candidate_id=payload.candidate_id,
            task_type=payload.task_type,
            priority=payload.priority,
            approval_required=payload.approval_required,
            status=payload.status,
            reason=payload.reason,
            target_json=json.dumps(payload.target, ensure_ascii=False),
            payload_json=json.dumps(
                {
                    "actor_id": actor.actor_id,
                    **payload.payload,
                },
                ensure_ascii=False,
            ),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _ok({"task": _serialize_robot_task(row)}, actor=actor)

    @app.post(
        "/actions/approve",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def approve_action(
        payload: ApprovalRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("approve_actions")),
    ) -> dict[str, Any]:
        runtime_mode = load_runtime_mode(services.settings.runtime_mode_path)
        if runtime_mode.mode != "approval":
            raise HTTPException(status_code=409, detail="runtime mode must be approval to execute actions")
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        if decision.status == "rejected":
            raise HTTPException(status_code=409, detail="decision already rejected")
        _record_approval(
            session=session,
            decision_id=decision.id,
            actor_id=actor.actor_id,
            approval_status="approved",
            reason=payload.reason,
            payload=payload.model_dump(),
        )
        dispatch_results = _execute_decision_dispatch(
            decision=decision,
            actor_id=actor.actor_id,
            services=services,
            session=session,
        )
        session.commit()
        return _ok(
            {
                "decision_id": decision.id,
                "approval_status": "approved",
                "dispatch_results": dispatch_results,
            },
            actor=actor,
        )

    @app.post(
        "/actions/execute",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def execute_action(
        payload: ExecuteActionRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("execute_actions")),
    ) -> dict[str, Any]:
        runtime_mode = load_runtime_mode(services.settings.runtime_mode_path)
        if runtime_mode.mode != "approval":
            raise HTTPException(status_code=409, detail="runtime mode must be approval to execute actions")
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        if decision.status == "rejected":
            raise HTTPException(status_code=409, detail="decision already rejected")
        if decision.status == "approved_executed":
            raise HTTPException(status_code=409, detail="decision already executed")

        latest_approval = _latest_approval(decision)
        if latest_approval is None or latest_approval.approval_status != "approved":
            _record_approval(
                session=session,
                decision_id=decision.id,
                actor_id=actor.actor_id,
                approval_status="approved",
                reason=payload.reason,
                payload=payload.model_dump(),
            )
        dispatch_results = _execute_decision_dispatch(
            decision=decision,
            actor_id=actor.actor_id,
            services=services,
            session=session,
        )
        session.commit()
        return _ok(
            {
                "decision_id": decision.id,
                "approval_status": "approved",
                "dispatch_results": dispatch_results,
            },
            actor=actor,
        )

    @app.post(
        "/actions/reject",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def reject_action(
        payload: ApprovalRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("approve_actions")),
    ) -> dict[str, Any]:
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        approval = ApprovalRecord(
            decision_id=decision.id,
            actor_id=actor.actor_id,
            approval_status="rejected",
            reason=payload.reason,
            approval_payload_json=json.dumps(payload.model_dump(), ensure_ascii=False),
        )
        session.add(approval)
        decision.status = "rejected"
        session.commit()
        return _ok({"decision_id": decision.id, "approval_status": "rejected"}, actor=actor)

    @app.get("/dashboard", tags=["dashboard"], response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html()

    return app


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>Pepper Smartfarm Approval Dashboard</title>
  <style>
    :root { --bg:#f4f1e8; --ink:#1d2a1f; --card:#fffdf7; --line:#d8d1c3; --accent:#456b4f; --warn:#8a4a2f; --muted:#657d6a; --critical:#7a2f21; }
    body { margin:0; font-family: 'Noto Sans KR', sans-serif; background:linear-gradient(180deg,#f0eadf 0%,#f7f4ec 100%); color:var(--ink); }
    header { padding:24px 28px; border-bottom:1px solid var(--line); background:rgba(255,255,255,0.6); backdrop-filter: blur(8px); }
    main { display:grid; grid-template-columns: 400px 1fr; gap:20px; padding:20px; }
    .card { background:var(--card); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 8px 30px rgba(44,60,47,0.06); }
    h1,h2,h3 { margin:0 0 12px; }
    label { display:block; font-size:13px; margin:8px 0 4px; color:#4a5b4d; }
    input, select, textarea, button { width:100%; box-sizing:border-box; border-radius:12px; border:1px solid var(--line); padding:10px 12px; font:inherit; }
    textarea { min-height:120px; resize:vertical; }
    button { background:var(--accent); color:white; cursor:pointer; border:none; margin-top:10px; }
    button.secondary { background:#657d6a; }
    button.warn { background:var(--warn); }
    .mode { display:inline-block; padding:6px 10px; border-radius:999px; background:#e3ecd9; color:#28523a; font-weight:700; }
    .grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:12px; margin-bottom:16px; }
    .metric { padding:14px; border-radius:14px; border:1px solid var(--line); background:#faf7ef; }
    .metric strong { display:block; font-size:24px; margin-top:6px; }
    .content-grid { display:grid; grid-template-columns: 1.1fr 0.9fr; gap:16px; }
    .stack { display:grid; gap:16px; }
    .decision { padding:14px; border:1px solid var(--line); border-radius:14px; margin-bottom:12px; }
    .decision pre { white-space:pre-wrap; word-break:break-word; background:#f6f3ea; padding:10px; border-radius:10px; }
    .meta { font-size:12px; color:#5b685e; margin-bottom:8px; }
    .row { display:flex; gap:8px; }
    .row > * { flex:1; }
    .zone, .alert, .robot, .command { padding:12px; border:1px solid var(--line); border-radius:14px; margin-bottom:10px; background:#fbf8f1; }
    .badge { display:inline-block; padding:4px 8px; border-radius:999px; font-size:12px; font-weight:700; background:#eef4e7; color:#28523a; margin-right:6px; }
    .badge.warn { background:#f7e5db; color:#7a2f21; }
    .badge.dark { background:#ece8dd; color:#4b544d; }
    .decision-actions { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:8px; margin-top:10px; }
    .section-title { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
    .small { font-size:12px; color:#5b685e; }
    @media (max-width: 1200px) {
      main, .content-grid, .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Approval Dashboard</h1>
    <div>현재 모드: <span id="modeBadge" class="mode">loading</span></div>
  </header>
  <main>
    <section class="card">
      <h2>Decision Request</h2>
      <label>Zone</label>
      <input id="zoneId" value="gh-01-zone-a" />
      <label>Task</label>
      <select id="taskType">
        <option value="state_judgement">state_judgement</option>
        <option value="action_recommendation">action_recommendation</option>
        <option value="failure_response">failure_response</option>
        <option value="robot_task_prioritization">robot_task_prioritization</option>
        <option value="forbidden_action">forbidden_action</option>
      </select>
      <label>Growth Stage</label>
      <input id="growthStage" value="fruiting" />
      <label>Current State JSON</label>
      <textarea id="currentState">{ "air_temp_c": 31.5, "rh_pct": 88.0, "substrate_moisture_pct": 24.0, "ripe_fruit_count": 72 }</textarea>
      <label>Sensor Quality JSON</label>
      <textarea id="sensorQuality">{ "overall": "good" }</textarea>
      <div class="row">
        <button onclick="submitDecision()">Evaluate</button>
        <button class="secondary" onclick="toggleMode()">Toggle Mode</button>
      </div>
      <p class="small">shadow 모드에서는 운영자가 일치/불일치를 기록하고, approval 모드에서는 승인 후에만 dispatch가 실행됩니다.</p>
    </section>
    <section class="card">
      <div class="grid" id="metricGrid"></div>
      <div class="content-grid">
        <div class="stack">
          <section>
            <div class="section-title">
              <h2>Zone Overview</h2>
              <span class="small">latest by zone</span>
            </div>
            <div id="zoneList"></div>
          </section>
          <section>
            <div class="section-title">
              <h2>Real-time Decisions</h2>
              <span class="small">최근 40건</span>
            </div>
            <div id="decisionList"></div>
          </section>
        </div>
        <div class="stack">
          <section>
            <div class="section-title">
              <h2>Shadow Window</h2>
              <span class="small">real shadow audit summary</span>
            </div>
            <div id="shadowWindow"></div>
          </section>
          <section>
            <div class="section-title">
              <h2>Alerts</h2>
              <span class="small">high / critical / unknown / validator</span>
            </div>
            <div id="alertList"></div>
          </section>
          <section>
            <div class="section-title">
              <h2>Robot Tasks</h2>
              <span class="small">최근 추천된 작업</span>
            </div>
            <div id="robotList"></div>
          </section>
          <section>
            <div class="section-title">
              <h2>Execution History</h2>
              <span class="small">최근 dispatch</span>
            </div>
            <div id="commandList"></div>
          </section>
        </div>
      </div>
    </section>
  </main>
  <script>
    async function apiFetch(url, options) {
      const res = await fetch(url, options);
      const body = await res.json();
      if (!res.ok) {
        const message = body?.error?.message || body?.detail || 'request failed';
        throw new Error(message);
      }
      return body;
    }
    async function toggleMode() {
      const current = await apiFetch('/runtime/mode');
      const next = current.data.mode === 'shadow' ? 'approval' : 'shadow';
      await apiFetch('/runtime/mode', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ mode: next, actor_id:'dashboard', reason:'dashboard toggle'}) });
      await refreshDashboard();
    }
    async function submitDecision() {
      const body = {
        request_id: 'dashboard-' + Date.now(),
        zone_id: document.getElementById('zoneId').value,
        task_type: document.getElementById('taskType').value,
        growth_stage: document.getElementById('growthStage').value,
        current_state: JSON.parse(document.getElementById('currentState').value),
        sensor_quality: JSON.parse(document.getElementById('sensorQuality').value),
      };
      await apiFetch('/decisions/evaluate-zone', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      await refreshDashboard();
    }
    async function approve(decisionId) {
      const reason = window.prompt('승인 사유를 입력하세요.', 'dashboard approve') || '';
      await apiFetch('/actions/approve', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: decisionId, actor_id:'dashboard-operator', reason }) });
      await refreshDashboard();
    }
    async function reject(decisionId) {
      const reason = window.prompt('거절 사유를 입력하세요.', 'dashboard reject') || '';
      await apiFetch('/actions/reject', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: decisionId, actor_id:'dashboard-operator', reason }) });
      await refreshDashboard();
    }
    async function review(decisionId, agreementStatus) {
      const note = window.prompt(agreementStatus === 'agree' ? '일치 메모를 입력하세요.' : '불일치 원인을 입력하세요.', '') || '';
      await apiFetch('/shadow/reviews', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          decision_id: decisionId,
          actor_id:'dashboard-operator',
          agreement_status: agreementStatus,
          note
        })
      });
      await refreshDashboard();
    }
    function renderMetrics(summary) {
      const metrics = [
        ['Decision', summary.decision_count],
        ['Approval Pending', summary.approval_pending_count],
        ['Shadow Review Pending', summary.shadow_review_pending_count],
        ['Blocked Actions', summary.blocked_action_count],
        ['Safe Mode', summary.safe_mode_count],
        ['Operator Disagree', summary.operator_disagreement_count],
        ['Agreement Rate', summary.operator_agreement_rate ?? 'n/a'],
        ['Commands', summary.command_count],
      ];
      document.getElementById('metricGrid').innerHTML = metrics.map(([label, value]) => `
        <div class="metric">
          <div class="small">${label}</div>
          <strong>${value}</strong>
        </div>
      `).join('');
    }
    function renderZones(zones) {
      document.getElementById('zoneList').innerHTML = zones.map(zone => `
        <div class="zone">
          <div class="meta">${zone.zone_id} · ${zone.task_type} · ${zone.status}</div>
          <div><span class="badge ${zone.risk_level === 'critical' ? 'warn' : 'dark'}">${zone.risk_level}</span>${zone.current_state_summary || 'summary 없음'}</div>
          <div class="small">sensor_quality: ${JSON.stringify(zone.sensor_quality)}</div>
        </div>
      `).join('') || '<div>zone snapshot이 없습니다.</div>';
    }
    function renderAlerts(items) {
      document.getElementById('alertList').innerHTML = items.map(item => `
        <div class="alert">
          <div class="meta">#${item.decision_id} · ${item.zone_id} · ${item.alert_type}</div>
          <div><span class="badge warn">${item.severity}</span>${item.summary || 'summary 없음'}</div>
          <div class="small">validator: ${(item.validator_reason_codes || []).join(', ') || 'none'}</div>
        </div>
      `).join('') || '<div>alert가 없습니다.</div>';
    }
    function renderRobotTasks(items) {
      document.getElementById('robotList').innerHTML = items.map(item => `
        <div class="robot">
          <div class="meta">#${item.decision_id} · ${item.zone_id}</div>
          <div><span class="badge">${item.task_type}</span><span class="badge dark">${item.priority}</span></div>
          <div class="small">candidate=${item.candidate_id || 'none'} · status=${item.status}</div>
        </div>
      `).join('') || '<div>robot task가 없습니다.</div>';
    }
    function renderShadowWindow(summary) {
      if (!summary) {
        document.getElementById('shadowWindow').innerHTML = '<div class="zone">shadow window가 아직 없습니다.</div>';
        return;
      }
      document.getElementById('shadowWindow').innerHTML = `
        <div class="zone">
          <div><span class="badge ${summary.promotion_decision === 'rollback' ? 'warn' : 'dark'}">${summary.promotion_decision}</span></div>
          <div class="small">decision=${summary.decision_count} · agreement=${summary.operator_agreement_rate} · critical_disagreement=${summary.critical_disagreement_count}</div>
          <div class="small">citation=${summary.citation_coverage} · retrieval=${summary.retrieval_hit_rate} · policy_mismatch=${summary.policy_mismatch_count}</div>
          <div class="small">window=${summary.window_start || 'n/a'} ~ ${summary.window_end || 'n/a'}</div>
        </div>
      `;
    }
    function renderCommands(items) {
      document.getElementById('commandList').innerHTML = items.map(item => `
        <div class="command">
          <div class="meta">#${item.decision_id} · ${item.target_id}</div>
          <div><span class="badge">${item.action_type}</span><span class="badge dark">${item.status}</span></div>
        </div>
      `).join('') || '<div>dispatch 기록이 없습니다.</div>';
    }
    function renderDecisions(mode, items) {
      const html = items.map(item => `
        <div class="decision">
          <div class="meta">#${item.decision_id} · ${item.zone_id} · ${item.task_type} · ${item.status}</div>
          <div class="meta">risk=${item.risk_level || 'unknown'} · model=${item.model_id} · prompt=${item.prompt_version}</div>
          <div class="meta">summary: ${item.current_state_summary || 'none'}</div>
          <pre>${JSON.stringify(item.validated_output, null, 2)}</pre>
          <div class="meta">citations: ${(item.citations || []).map(c => c.chunk_id).join(', ') || 'none'}</div>
          <div class="meta">validator: ${(item.validator_reason_codes || []).join(', ') || 'none'}</div>
          <div class="decision-actions">
            ${mode === 'approval' && item.runtime_mode === 'approval' && item.status === 'evaluated' ? `
              <button onclick="approve(${item.decision_id})">승인</button>
              <button class="secondary" onclick="reject(${item.decision_id})">거절</button>
            ` : ''}
            ${mode === 'shadow' && item.runtime_mode === 'shadow' && item.status === 'evaluated' ? `
              <button onclick="review(${item.decision_id}, 'agree')">일치</button>
              <button class="warn" onclick="review(${item.decision_id}, 'disagree')">불일치</button>
            ` : ''}
          </div>
          <div class="small">
            approval=${item.latest_approval ? item.latest_approval.approval_status : 'none'}
            · shadow_review=${item.latest_shadow_review ? item.latest_shadow_review.agreement_status : 'none'}
          </div>
        </div>
      `).join('');
      document.getElementById('decisionList').innerHTML = html || '<div>아직 decision이 없습니다.</div>';
    }
    async function refreshDashboard() {
      const response = await apiFetch('/dashboard/data');
      const data = response.data;
      document.getElementById('modeBadge').textContent = data.runtime_mode.mode;
      renderMetrics(data.summary);
      renderZones(data.zones);
      renderShadowWindow(data.shadow_window);
      renderAlerts(data.alerts);
      renderRobotTasks(data.robot_tasks);
      renderCommands(data.commands);
      renderDecisions(data.runtime_mode.mode, data.decisions);
    }
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
  </script>
</body>
</html>"""
