from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from .api_models import (
    ApprovalRequest,
    ApiResponse,
    ChatRequest,
    EvaluateZoneRequest,
    ErrorResponse,
    ExecuteActionRequest,
    PolicyUpdateRequest,
    RobotTaskCreateRequest,
    ShadowCaptureRequest,
    RuntimeModeRequest,
    ShadowReviewRequest,
)
from .auth import ROLE_PERMISSIONS, ActorIdentity, get_authenticated_actor, require_permission
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
    PolicyEventRecord,
    PolicyEvaluationRecord,
    PolicyRecord,
    RobotCandidateRecord,
    RobotTaskRecord,
    SensorRecord,
    ZoneRecord,
)
from .planner import ActionDispatchPlanner
from .runtime_mode import load_runtime_mode, save_runtime_mode
from .policy_source import DbPolicySource
from .seed import bootstrap_reference_data
from .shadow_mode import build_window_summary_from_paths, capture_shadow_cases

configure_repo_paths()

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402
from llm_orchestrator import LLMOrchestratorService, ModelConfig, OrchestratorRequest  # noqa: E402
from policy_engine import set_active_policy_source  # noqa: E402
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


def _serialize_policy_event(row: PolicyEventRecord) -> dict[str, Any]:
    return {
        "event_id": row.id,
        "decision_id": row.decision_id,
        "request_id": row.request_id,
        "event_type": row.event_type,
        "policy_result": row.policy_result,
        "policy_ids": _loads_json(row.policy_ids_json, []),
        "reason_codes": _loads_json(row.reason_codes_json, []),
        "payload": _loads_json(row.payload_json, {}),
        "created_at": row.created_at.isoformat(),
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


def _serialize_robot_candidate(row: RobotCandidateRecord) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "decision_id": row.decision_id,
        "zone_id": row.zone_id,
        "candidate_type": row.candidate_type,
        "priority": row.priority,
        "status": row.status,
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
    zone_state = json.loads(decision.zone_state_json)
    plans = services.planner.plan(
        decision_id=decision.id,
        request_id=decision.request_id,
        zone_id=decision.zone_id,
        validated_output=validated_output,
        zone_state=zone_state,
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
        policy_event = dispatch_result.get("policy_event")
        if isinstance(policy_event, dict):
            session.add(
                PolicyEventRecord(
                    decision_id=decision.id,
                    request_id=str(policy_event.get("request_id") or decision.request_id),
                    event_type=str(policy_event.get("event_type") or "policy_event"),
                    policy_result=str(policy_event.get("policy_result") or "pass"),
                    policy_ids_json=json.dumps(policy_event.get("policy_ids", []), ensure_ascii=False),
                    reason_codes_json=json.dumps(policy_event.get("reason_codes", []), ensure_ascii=False),
                    payload_json=json.dumps(
                        {
                            "dispatch_request": plan.payload,
                            "dispatch_result": dispatch_result,
                        },
                        ensure_ascii=False,
                    ),
                )
            )
    decision.status = "approved_executed"
    return dispatch_results


TRACKED_SENSOR_METRICS: tuple[str, ...] = (
    "air_temp_c",
    "rh_pct",
    "vpd_kpa",
    "substrate_moisture_pct",
    "substrate_temp_c",
    "co2_ppm",
    "par_umol_m2_s",
    "feed_ec_ds_m",
    "drain_ec_ds_m",
    "feed_ph",
    "drain_ph",
)


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _build_sensor_series(decision_rows: list[DecisionRecord]) -> dict[str, list[dict[str, Any]]]:
    """Extract a time-ordered sensor series from decision zone_state snapshots.

    Dashboard sparklines render without time-series storage by replaying
    each decision's captured current_state. Returning older-first makes
    the client side trivially drawable.
    """
    ordered_rows = sorted(decision_rows, key=lambda row: row.created_at)
    series: dict[str, list[dict[str, Any]]] = {metric: [] for metric in TRACKED_SENSOR_METRICS}
    for row in ordered_rows:
        zone_state = _loads_json(row.zone_state_json, {})
        current_state = zone_state.get("current_state") if isinstance(zone_state, dict) else None
        if not isinstance(current_state, dict):
            continue
        timestamp = row.created_at.isoformat()
        for metric in TRACKED_SENSOR_METRICS:
            value = _coerce_numeric(current_state.get(metric))
            if value is None:
                continue
            series[metric].append({"t": timestamp, "value": value, "decision_id": row.id})
    return {metric: points for metric, points in series.items() if points}


def _compute_shadow_window(shadow_audit_path: Path | None) -> dict[str, Any] | None:
    if shadow_audit_path is None or not shadow_audit_path.exists():
        return None
    try:
        return build_window_summary_from_paths([shadow_audit_path])
    except ValueError:
        return None


def _build_dashboard_payload(
    session: Session,
    mode_state: Any,
    *,
    shadow_audit_path: Path | None = None,
) -> dict[str, Any]:
    rows = session.execute(select(DecisionRecord).order_by(desc(DecisionRecord.id)).limit(40)).scalars().all()
    command_rows = session.execute(select(DeviceCommandRecord).order_by(desc(DeviceCommandRecord.id)).limit(30)).scalars().all()
    zone_rows = session.execute(select(ZoneRecord).order_by(ZoneRecord.zone_id)).scalars().all()
    alert_rows = session.execute(select(AlertRecord).order_by(desc(AlertRecord.id)).limit(30)).scalars().all()
    robot_rows = session.execute(select(RobotTaskRecord).order_by(desc(RobotTaskRecord.id)).limit(30)).scalars().all()
    robot_candidate_rows = session.execute(
        select(RobotCandidateRecord).order_by(desc(RobotCandidateRecord.id)).limit(30)
    ).scalars().all()
    policy_rows = session.execute(select(PolicyRecord).order_by(PolicyRecord.policy_stage, PolicyRecord.policy_id)).scalars().all()
    policy_event_rows = session.execute(select(PolicyEventRecord).order_by(desc(PolicyEventRecord.id)).limit(30)).scalars().all()
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
        zone_entry = latest_zone_items[item["zone_id"]]
        if zone_entry.get("decision_id") is None or zone_entry["decision_id"] < item["decision_id"]:
            zone_entry["decision_id"] = item["decision_id"]
            zone_entry["task_type"] = item["task_type"]
            zone_entry["status"] = item["status"]
            zone_entry["risk_level"] = item["risk_level"]
            zone_entry["current_state_summary"] = item["current_state_summary"]
            zone_entry["sensor_quality"] = item["sensor_quality"]
            zone_entry["created_at"] = item["created_at"]
            zone_state = item.get("zone_state") or {}
            zone_entry["device_status"] = zone_state.get("device_status") or {}
            zone_entry["active_constraints"] = zone_state.get("active_constraints") or {}

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
    shadow_window_summary = _compute_shadow_window(shadow_audit_path)

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
            "robot_candidate_count": len(robot_candidate_rows),
            "policy_count": len(policy_rows),
            "policy_disabled_count": sum(1 for row in policy_rows if not row.enabled),
            "policy_event_count": len(policy_event_rows),
            "policy_blocked_count": sum(1 for row in policy_event_rows if row.event_type == "blocked"),
            "policy_approval_count": sum(1 for row in policy_event_rows if row.event_type == "approval_required"),
        },
        "shadow_window": shadow_window_summary,
        "zones": list(latest_zone_items.values()),
        "policies": [_serialize_policy(row) for row in policy_rows],
        "policy_events": [_serialize_policy_event(row) for row in policy_event_rows[:12]],
        "alerts": [_serialize_alert(row) for row in alert_rows[:12]],
        "robot_tasks": [_serialize_robot_task(row) for row in robot_rows[:12]],
        "robot_candidates": [_serialize_robot_candidate(row) for row in robot_candidate_rows[:12]],
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
    set_active_policy_source(DbPolicySource(session_factory))
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
    app.dependency_overrides[load_settings] = lambda: resolved_settings
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
        sensor_series = _build_sensor_series(decision_rows)
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
                "sensor_series": sensor_series,
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

    @app.get(
        "/policies/events",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_policy_events(
        limit: int = 50,
        event_type: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        stmt = select(PolicyEventRecord).order_by(desc(PolicyEventRecord.id)).limit(limit)
        if event_type:
            stmt = stmt.where(PolicyEventRecord.event_type == event_type)
        rows = session.execute(stmt).scalars().all()
        return _ok(
            {"items": [_serialize_policy_event(row) for row in rows]},
            actor=actor,
            meta={"limit": limit, "event_type": event_type},
        )

    @app.post(
        "/policies/{policy_id}",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def update_policy(
        policy_id: str,
        payload: PolicyUpdateRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("manage_policies")),
    ) -> dict[str, Any]:
        row = session.execute(select(PolicyRecord).where(PolicyRecord.policy_id == policy_id)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="policy not found")
        if payload.enabled is not None:
            row.enabled = payload.enabled
        if payload.severity is not None:
            row.severity = payload.severity
        if payload.description is not None:
            row.description = payload.description
        if payload.trigger_flags is not None:
            row.trigger_flags_json = json.dumps(payload.trigger_flags, ensure_ascii=False)
        if payload.enforcement is not None:
            row.enforcement_json = json.dumps(payload.enforcement, ensure_ascii=False)
        session.commit()
        session.refresh(row)
        return _ok({"policy": _serialize_policy(row)}, actor=actor)

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
        if not payload.append and "manage_runtime_mode" not in ROLE_PERMISSIONS.get(actor.role, set()):
            raise HTTPException(
                status_code=403,
                detail="append=false rotation requires manage_runtime_mode permission",
            )
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
        payload = _build_dashboard_payload(
            session,
            load_runtime_mode(services.settings.runtime_mode_path),
            shadow_audit_path=services.settings.shadow_audit_log_path,
        )
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

    @app.get(
        "/robot/candidates",
        tags=["operations"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_robot_candidates(
        zone_id: str | None = None,
        status: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        stmt = select(RobotCandidateRecord).order_by(desc(RobotCandidateRecord.id))
        if zone_id:
            stmt = stmt.where(RobotCandidateRecord.zone_id == zone_id)
        if status:
            stmt = stmt.where(RobotCandidateRecord.status == status)
        rows = session.execute(stmt.limit(50)).scalars().all()
        return _ok(
            {"items": [_serialize_robot_candidate(row) for row in rows]},
            actor=actor,
            meta={"zone_id": zone_id, "status": status},
        )

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

    @app.post(
        "/ai/chat",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def ai_chat(
        payload: ChatRequest,
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        if not payload.messages:
            raise HTTPException(status_code=400, detail="messages must not be empty")
        last_user = next(
            (msg for msg in reversed(payload.messages) if msg.role == "user"),
            None,
        )
        if last_user is None:
            raise HTTPException(status_code=400, detail="at least one user message is required")

        system_prompt = payload.system_prompt or _build_chat_system_prompt()
        history_text = _render_chat_history(payload.messages[:-1])
        user_payload = json.dumps(
            {
                "chat_history": history_text,
                "latest_user_message": last_user.content,
                "context": payload.context or {},
                "instruction": (
                    "위 대화 흐름을 고려해 적고추 온실 운영 관점의 한국어 답변을 작성해라. "
                    "가능하면 구체적 수치와 제안 액션을 포함하고, JSON 형식이 아닌 자연어로 답한다."
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        invocation = services.orchestrator.client.complete(
            system_prompt=system_prompt,
            user_message=user_payload,
        )
        reply_text = _extract_chat_reply(invocation.raw_text)
        return _ok(
            {
                "reply": {"role": "assistant", "content": reply_text},
                "model_id": invocation.model_id,
                "provider": invocation.provider,
                "attempts": invocation.attempts,
            },
            actor=actor,
            meta={"system_prompt_id": "chat_v1"},
        )

    @app.get("/dashboard", tags=["dashboard"], response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html()

    @app.get("/", include_in_schema=False)
    def dashboard_root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/dashboard", status_code=307)

    return app


def _build_chat_system_prompt() -> str:
    return (
        "너는 '적고추 온실 스마트팜 통합 제어' 시스템의 운영 보조 AI 어시스턴트다. "
        "역할은 파인튜닝된 재배 의사결정 모델을 기반으로, 운영자의 질문에 대해 "
        "현재 센서 상태와 기존 정책/규칙을 참고해 한국어로 답변하는 것이다. "
        "절대 안전 규칙을 위반하는 제안을 하지 않는다. "
        "장치 직접 on/off 명령을 내릴 수 없다는 점을 분명히 하고, 대신 운영자가 "
        "대시보드에서 승인/거절할 수 있는 형태로 권고한다. "
        "답변은 짧고 명확하게, 가능하면 숫자와 근거를 제시한다."
    )


def _render_chat_history(messages) -> str:
    lines: list[str] = []
    for msg in messages[-8:]:
        role = "운영자" if msg.role == "user" else ("AI" if msg.role == "assistant" else "시스템")
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines) if lines else "(이전 대화 없음)"


def _extract_chat_reply(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if not text:
        return "죄송합니다. 현재 AI 응답을 받아오지 못했습니다. 잠시 후 다시 시도해주세요."
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(parsed, dict):
        for key in ("reply", "message", "content", "answer", "response"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        summary = parsed.get("situation_summary") or parsed.get("risk_level")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    return text


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>적고추 온실 스마트팜 통합 제어</title>
  <script src="https://cdn.tailwindcss.com?plugins=forms"></script>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            'ink': '#1d2a1f',
            'muted': '#657d6a',
            'surface': '#fff9ed',
            'surface-low': '#f9f3e8',
            'surface-lowest': '#ffffff',
            'surface-container': '#f3ede2',
            'surface-container-high': '#ede7dd',
            'surface-dim': '#dfd9cf',
            'outline': '#c1c8c0',
            'primary': '#2d5338',
            'primary-dim': '#456b4f',
            'primary-container': '#bfeac7',
            'on-primary-container': '#294e35',
            'secondary': '#546255',
            'secondary-container': '#d7e7d6',
            'tertiary': '#763a20',
            'tertiary-container': '#935135',
            'warn': '#8a4a2f',
            'critical': '#7a2f21',
            'sidebar': '#1d2a1f',
            'sidebar-hover': '#2d5338',
          },
          fontFamily: {
            sans: ['Pretendard', 'Noto Sans KR', 'system-ui', 'sans-serif'],
          },
          boxShadow: {
            'soft': '0 8px 28px rgba(44,60,47,0.06)',
            'softer': '0 4px 12px rgba(0,0,0,0.02)',
          },
        },
      },
    }
  </script>
  <style>
    html, body { background-color: #f7f4ec; }
    body { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; background: #f7f4ec; background-image: linear-gradient(180deg, #f0eadf 0%, #f7f4ec 100%); color: #1d2a1f; min-height: 100vh; }
    .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
    .msf { font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24; }
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #c1c8c0; border-radius: 999px; }
    .view { display: none; }
    .view.active { display: block; }
    .chip { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; line-height: 1; }
    .chip-enabled { background: #eef4e7; color: #28523a; }
    .chip-warn { background: #f7e5db; color: #7a2f21; }
    .chip-critical { background: #ffdad6; color: #93000a; }
    .chip-dark { background: #ece8dd; color: #4b544d; }
    .chip-accent { background: #2d5338; color: white; }
    .kpi strong { color: #1d2a1f; }
    .glass { background-color: rgba(255, 249, 237, 0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
    /* Mobile drawer overlay — hidden on desktop so the workspace is not dimmed */
    #sidebarBackdrop { display: none; position: fixed; inset: 0; background-color: rgba(0, 0, 0, 0.4); z-index: 40; }
    @media (max-width: 1023px) {
      #sidebar { transform: translateX(-100%); transition: transform 0.25s ease; }
      #sidebar.open { transform: translateX(0); }
      #sidebarBackdrop.open { display: block; }
    }
  </style>
</head>
<body class="min-h-screen">
  <aside id="sidebar" class="fixed left-0 top-0 h-screen w-64 flex flex-col bg-sidebar text-white z-50 shadow-soft">
    <div class="px-6 py-6 border-b border-white/10">
      <h1 class="text-lg font-bold tracking-tight">농경 사령부</h1>
      <p class="text-[10px] tracking-[0.15em] uppercase text-white/60 mt-1">적고추 온실 · Agrarian Command</p>
    </div>
    <nav id="sidebarNav" class="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scroll">
      <a data-view="overview" class="nav-link active">
        <span class="material-symbols-outlined text-[20px]">dashboard</span>
        <span>대시보드</span>
      </a>
      <a data-view="zones" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">thermostat</span>
        <span>존 모니터링</span>
      </a>
      <a data-view="decisions" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">psychology</span>
        <span>결정 / 승인</span>
      </a>
      <a data-view="ai_chat" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">forum</span>
        <span>AI 어시스턴트</span>
      </a>
      <a data-view="alerts" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">notifications_active</span>
        <span>알림</span>
      </a>
      <a data-view="robot" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">smart_toy</span>
        <span>로봇</span>
      </a>
      <a data-view="devices" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">precision_manufacturing</span>
        <span>장치 / 제약</span>
      </a>
      <a data-view="policies" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">policy</span>
        <span>정책 / 이벤트</span>
      </a>
      <a data-view="shadow" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">visibility</span>
        <span>Shadow Mode</span>
      </a>
      <a data-view="system" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">settings</span>
        <span>시스템</span>
      </a>
    </nav>
    <div class="px-4 py-4 border-t border-white/10 space-y-3">
      <div class="flex items-center gap-2 text-[11px] text-white/75">
        <span>운영 모드</span>
        <span id="modeBadge" class="chip chip-enabled">loading</span>
      </div>
      <div id="authContextMini" class="text-[11px] text-white/60"></div>
      <button onclick="toggleMode()" class="w-full bg-primary hover:bg-primary-dim text-white text-xs font-semibold rounded-lg py-2 transition">모드 전환</button>
    </div>
  </aside>
  <div id="sidebarBackdrop" onclick="toggleSidebar(false)"></div>

  <header class="lg:ml-64 sticky top-0 h-16 z-30 glass border-b border-outline/30 flex items-center justify-between px-4 md:px-8">
    <div class="flex items-center gap-3">
      <button onclick="toggleSidebar()" class="lg:hidden text-ink p-2 hover:bg-surface-container rounded-lg">
        <span class="material-symbols-outlined">menu</span>
      </button>
      <div>
        <h2 id="viewTitle" class="text-lg md:text-xl font-bold text-ink">대시보드</h2>
        <p id="viewSub" class="text-[11px] text-muted hidden md:block">전체 운영 현황 요약</p>
      </div>
    </div>
    <div class="flex items-center gap-3 md:gap-5">
      <div class="hidden md:flex items-center gap-2 text-xs text-muted">
        <span class="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
        <span>System Status: Optimal</span>
      </div>
      <span class="material-symbols-outlined text-ink cursor-pointer">notifications</span>
      <div id="authContext" class="hidden md:block"></div>
    </div>
  </header>

  <main class="lg:ml-64 px-4 md:px-8 py-6 md:py-8 max-w-[1600px]">

    <!-- 대시보드 -->
    <section class="view active" data-view="overview">
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6" id="metricGrid"></div>
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">
        <div class="card lg:col-span-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">존 상태 요약</h3>
            <span class="text-[11px] text-muted uppercase tracking-wider">Real-Time Environmental Monitoring</span>
          </div>
          <div id="zoneList" class="space-y-3"></div>
        </div>
        <div class="card lg:col-span-2 bg-primary text-white !bg-primary">
          <p class="text-[11px] tracking-wider uppercase text-white/60 mb-1">Shadow Window Summary</p>
          <h3 class="text-xl font-bold mb-4 text-white">Automation Strategy Review</h3>
          <div id="shadowWindow"></div>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">최근 알림</h3>
            <span class="text-[11px] text-muted">View All Alerts</span>
          </div>
          <div id="alertListOverview" class="space-y-3"></div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">최근 실행</h3>
            <span class="text-[11px] text-muted">Full Audit Log</span>
          </div>
          <div id="commandListOverview" class="space-y-3"></div>
        </div>
      </div>
    </section>

    <!-- 존 모니터링 -->
    <section class="view" data-view="zones">
      <div class="card mb-5">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <p class="text-[11px] tracking-wider uppercase text-primary font-bold mb-1">Zone 시계열</p>
            <h3 class="text-lg font-bold text-ink">Zone History Chart</h3>
            <p class="text-[11px] text-muted mt-1">decision zone_state 기반 11개 지표 스파크라인</p>
          </div>
          <div class="flex items-center gap-2">
            <select id="historyZoneId" class="bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-xs">
              <option value="gh-01-zone-a">gh-01-zone-a</option>
            </select>
            <button onclick="refreshZoneHistory()" class="bg-primary text-white text-xs font-semibold rounded-lg px-4 py-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">refresh</span>
              <span>Refresh</span>
            </button>
          </div>
        </div>
        <div id="zoneHistoryCharts" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"></div>
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-ink">Zone Overview</h3>
          <span class="text-[11px] text-muted">View All</span>
        </div>
        <div id="zoneListDetailed" class="space-y-3"></div>
      </div>
    </section>

    <!-- 결정 / 승인 -->
    <section class="view" data-view="decisions">
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div class="card lg:col-span-2">
          <p class="text-[11px] tracking-wider uppercase text-primary font-bold mb-1">Intelligent Decision Engine</p>
          <h3 class="text-lg font-bold text-ink mb-4">신규 Decision 요청</h3>
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-2">Zone Select</label>
          <input id="zoneId" value="gh-01-zone-a" class="w-full bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-sm" />
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Target Task</label>
          <select id="taskType" class="w-full bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-sm">
            <option value="state_judgement">state_judgement</option>
            <option value="action_recommendation">action_recommendation</option>
            <option value="failure_response">failure_response</option>
            <option value="robot_task_prioritization">robot_task_prioritization</option>
            <option value="forbidden_action">forbidden_action</option>
          </select>
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Growth Stage</label>
          <input id="growthStage" value="fruiting" class="w-full bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-sm" />
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Current State JSON</label>
          <textarea id="currentState" rows="6" class="w-full bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-xs font-mono">{ "air_temp_c": 27.5, "rh_pct": 71.0, "substrate_moisture_pct": 54.0, "co2_ppm": 430, "feed_ph": 5.9 }</textarea>
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Sensor Quality JSON</label>
          <textarea id="sensorQuality" rows="2" class="w-full bg-surface-low border border-outline/50 rounded-lg px-3 py-2 text-xs font-mono">{ "overall": "good" }</textarea>
          <div class="flex gap-2 mt-4">
            <button onclick="submitDecision()" class="flex-1 bg-primary text-white font-semibold rounded-lg py-2 text-sm flex items-center justify-center gap-1">
              <span class="material-symbols-outlined text-[18px]">send</span>
              Request LLM Decision
            </button>
          </div>
        </div>
        <div class="card lg:col-span-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[18px]">history</span>
              Real-time Decisions
            </h3>
            <span class="text-[11px] text-muted">최근 40건</span>
          </div>
          <div id="decisionList" class="space-y-4 max-h-[720px] overflow-y-auto custom-scroll pr-1"></div>
        </div>
      </div>
    </section>

    <!-- AI 어시스턴트 (채팅) -->
    <section class="view" data-view="ai_chat">
      <div class="grid grid-cols-1 xl:grid-cols-5 gap-5 h-[calc(100vh-9rem)]">
        <div class="card xl:col-span-3 flex flex-col min-h-[500px]">
          <div class="flex items-center justify-between pb-4 border-b border-outline/30">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-sidebar flex items-center justify-center">
                <span class="material-symbols-outlined msf text-white text-[22px]">psychology</span>
              </div>
              <div>
                <h3 class="text-sm font-bold text-ink">AI AGRO-SYSTEM</h3>
                <p class="text-[10px] text-muted uppercase tracking-wider">Fine-tuned on pepper domain · sft_v10</p>
              </div>
            </div>
            <div class="chip chip-enabled">
              <span class="w-2 h-2 bg-primary rounded-full animate-pulse mr-1"></span>
              활성
            </div>
          </div>
          <div id="chatMessages" class="flex-1 overflow-y-auto custom-scroll py-4 space-y-4"></div>
          <div class="border-t border-outline/30 pt-4">
            <div class="bg-surface-low rounded-2xl p-2 flex items-end gap-2 shadow-softer">
              <textarea id="chatInput" rows="2" placeholder="온실 운영 관련 질문이나 명령을 입력하세요 (예: 'zone-a의 현재 EC 농도 확인해줘')" class="flex-1 bg-transparent border-none text-sm resize-none focus:ring-0 px-2 py-2 custom-scroll"></textarea>
              <button id="chatSendBtn" onclick="sendChatMessage()" class="bg-primary text-white p-3 rounded-xl hover:opacity-90 transition disabled:opacity-40">
                <span class="material-symbols-outlined">send</span>
              </button>
            </div>
            <div class="flex gap-2 mt-3 overflow-x-auto pb-1 custom-scroll">
              <button onclick="useQuickPrompt('zone-a 현재 상태 요약해줘')" class="whitespace-nowrap chip chip-dark hover:bg-primary/10 transition">zone-a 상태 요약</button>
              <button onclick="useQuickPrompt('blind50 residual 5건 어떻게 줄일까?')" class="whitespace-nowrap chip chip-dark hover:bg-primary/10 transition">blind50 residual</button>
              <button onclick="useQuickPrompt('현재 모든 zone의 위험도를 알려줘')" class="whitespace-nowrap chip chip-dark hover:bg-primary/10 transition">전체 위험도</button>
              <button onclick="useQuickPrompt('synthetic shadow day0 hold 해소 방법?')" class="whitespace-nowrap chip chip-dark hover:bg-primary/10 transition">shadow day0 hold</button>
              <button onclick="clearChat()" class="whitespace-nowrap chip chip-warn">대화 초기화</button>
            </div>
          </div>
        </div>
        <div class="card xl:col-span-2 flex flex-col">
          <p class="text-[11px] tracking-wider uppercase text-primary font-bold">Live Operations</p>
          <h3 class="text-xl font-bold text-ink mb-4">실시간 관제 현황</h3>
          <div class="bg-primary rounded-2xl p-5 text-white mb-4">
            <p class="text-[10px] uppercase tracking-wider text-white/60">Current Action</p>
            <h4 class="text-xl font-bold mt-2 mb-2" id="chatLiveAction">대기 중</h4>
            <p class="text-xs text-white/80" id="chatLiveDesc">AI 명령을 기다리는 중입니다.</p>
          </div>
          <div class="space-y-3 flex-1 overflow-y-auto custom-scroll" id="chatLiveLogs"></div>
          <div class="mt-4 bg-surface-low rounded-xl p-4">
            <p class="text-[10px] uppercase tracking-wider text-muted mb-2">Zone Health</p>
            <div class="grid grid-cols-3 gap-1" id="chatZoneHealth"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 알림 -->
    <section class="view" data-view="alerts">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-ink">Alerts</h3>
          <span class="text-[11px] text-muted">high / critical / unknown / validator</span>
        </div>
        <div id="alertList" class="space-y-3"></div>
      </div>
    </section>

    <!-- 로봇 -->
    <section class="view" data-view="robot">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Robot Tasks</h3>
            <span class="text-[11px] text-muted">LLM 추천 작업</span>
          </div>
          <div id="robotList" class="space-y-3"></div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Robot Candidates</h3>
            <span class="text-[11px] text-muted">vision/operator 후보</span>
          </div>
          <div id="robotCandidateList" class="space-y-3"></div>
        </div>
      </div>
    </section>

    <!-- 장치 / 제약 -->
    <section class="view" data-view="devices">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Device Status</h3>
            <span class="text-[11px] text-muted">zone별 최신 device_status</span>
          </div>
          <div id="deviceStatusList" class="space-y-3"></div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Active Constraints</h3>
            <span class="text-[11px] text-muted">현재 활성 제약</span>
          </div>
          <div id="activeConstraintsList" class="space-y-3"></div>
        </div>
      </div>
    </section>

    <!-- 정책 / 이벤트 -->
    <section class="view" data-view="policies">
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div class="card lg:col-span-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Policy Management</h3>
            <span class="text-[11px] text-muted">20 Active Rules · DB live</span>
          </div>
          <div id="policyList" class="space-y-3 max-h-[720px] overflow-y-auto custom-scroll pr-1"></div>
        </div>
        <div class="card lg:col-span-2">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Recent Policy Events</h3>
            <span class="text-[11px] text-muted">blocked / approval escalation</span>
          </div>
          <div id="policyEventList" class="space-y-3"></div>
        </div>
      </div>
    </section>

    <!-- Shadow Mode -->
    <section class="view" data-view="shadow">
      <div class="card mb-5">
        <p class="text-[11px] tracking-wider uppercase text-primary font-bold">Monitoring Module</p>
        <h3 class="text-lg font-bold text-ink mb-4">A. Shadow Window Summary</h3>
        <div id="shadowWindowDetail"></div>
      </div>
      <div class="card">
        <h3 class="text-lg font-bold text-ink mb-2">B. Shadow Review Guide</h3>
        <p class="text-xs text-muted leading-relaxed">shadow 모드에서는 실운영 환경에 영향을 주지 않으면서 신규 모델의 안정성과 정책을 검증하는 단계입니다. 결정/승인 메뉴의 decision 카드에 <b>일치</b>, <b>불일치</b> 버튼이 노출됩니다. capture 파이프라인은 <code class="bg-surface-low px-1 rounded">scripts/push_shadow_cases_to_ops_api.py</code>를 통해 외부에서 주입합니다.</p>
      </div>
    </section>

    <!-- 시스템 -->
    <section class="view" data-view="system">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Execution History</h3>
            <span class="text-[11px] text-muted">최근 dispatch</span>
          </div>
          <div id="commandList" class="space-y-3"></div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-ink">Runtime Info</h3>
            <span class="text-[11px] text-muted">auth / config</span>
          </div>
          <div id="runtimeInfo"></div>
        </div>
      </div>
    </section>

  </main>

  <style>
    .card { background: #fffdf7; border-radius: 18px; padding: 20px; box-shadow: 0 8px 28px rgba(44,60,47,0.04); }
    @media (min-width: 768px) { .card { padding: 24px; } }
    .nav-link { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.75); cursor: pointer; transition: all 0.15s; }
    .nav-link:hover { background: rgba(45, 83, 56, 0.5); color: white; }
    .nav-link.active { background: #456b4f; color: white; font-weight: 700; }
    .decision-card { background: #fffdf7; border: 1px solid rgba(193, 200, 192, 0.3); border-radius: 14px; padding: 16px; }
    .metric-card { background: #faf7ef; border-radius: 12px; padding: 12px; }
    .metric-card .label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #657d6a; font-weight: 600; }
    .metric-card .value { font-size: 20px; font-weight: 700; color: #1d2a1f; margin-top: 4px; display: block; }
    .zone-row { background: #fbf8f1; border-radius: 12px; padding: 14px; display: flex; justify-content: space-between; align-items: center; }
    .alert-row { background: #fbf8f1; border-radius: 12px; padding: 14px; }
    .placeholder { text-align: center; color: #9ba89f; padding: 24px; font-size: 13px; }
    .chat-bubble-user { max-width: 80%; background: #2d5338; color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px; font-size: 13px; line-height: 1.5; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .chat-bubble-ai { max-width: 88%; background: #fffdf7; color: #1d2a1f; padding: 14px 18px; border-radius: 18px 18px 18px 4px; font-size: 13px; line-height: 1.55; border: 1px solid rgba(193, 200, 192, 0.3); }
    .chat-bubble-error { background: #ffdad6; color: #93000a; }
  </style>

  <script>
    const VIEW_TITLES = {
      overview: ['대시보드', '전체 운영 현황 요약'],
      zones: ['존 모니터링', 'Zone 시계열 · 최신 스냅샷'],
      decisions: ['결정 / 승인', 'LLM 결정 요청과 승인 흐름'],
      ai_chat: ['AI 어시스턴트', '파인튜닝된 AI와 대화하며 관리'],
      alerts: ['알림', 'validator · risk · policy 알림'],
      robot: ['로봇', 'Robot Tasks 및 Candidate'],
      devices: ['장치 / 제약', '장치 상태와 활성 제약'],
      policies: ['정책 / 이벤트', 'Policy live toggle과 이벤트 로그'],
      shadow: ['Shadow Mode', 'real shadow window 요약'],
      system: ['시스템', 'execution history · runtime'],
    };
    function showView(name) {
      document.getElementById('viewTitle').textContent = (VIEW_TITLES[name] || VIEW_TITLES.overview)[0];
      document.getElementById('viewSub').textContent = (VIEW_TITLES[name] || VIEW_TITLES.overview)[1];
      document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === name));
      document.querySelectorAll('#sidebarNav a').forEach(a => a.classList.toggle('active', a.dataset.view === name));
      if (name === 'zones') refreshZoneHistory();
      if (name === 'ai_chat') scrollChatToBottom();
    }
    function toggleSidebar(force) {
      const sidebar = document.getElementById('sidebar');
      const backdrop = document.getElementById('sidebarBackdrop');
      const next = force !== undefined ? force : !sidebar.classList.contains('open');
      sidebar.classList.toggle('open', next);
      backdrop.classList.toggle('open', next);
    }
    async function apiFetch(url, options) {
      const res = await fetch(url, options);
      const body = await res.json();
      if (!res.ok) throw new Error(body?.error?.message || body?.detail || 'request failed');
      return body;
    }
    async function toggleMode() {
      const current = await apiFetch('/runtime/mode');
      const next = current.data.mode === 'shadow' ? 'approval' : 'shadow';
      await apiFetch('/runtime/mode', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ mode: next, actor_id:'dashboard', reason:'dashboard toggle'}) });
      await refreshDashboard();
    }
    async function submitDecision() {
      try {
        const body = {
          request_id: 'dashboard-' + Date.now(),
          zone_id: document.getElementById('zoneId').value,
          task_type: document.getElementById('taskType').value,
          growth_stage: document.getElementById('growthStage').value,
          current_state: JSON.parse(document.getElementById('currentState').value),
          sensor_quality: JSON.parse(document.getElementById('sensorQuality').value),
        };
        await apiFetch('/decisions/evaluate-zone', { method:'POST', headers:{'Content-Type':'application/json', 'X-Actor-Role':'service'}, body: JSON.stringify(body) });
        await refreshDashboard();
      } catch (err) {
        alert('Decision 요청 실패: ' + err.message);
      }
    }
    async function approve(id) {
      const reason = prompt('승인 사유', 'dashboard approve') || '';
      try { await apiFetch('/actions/approve', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: id, actor_id:'dashboard-operator', reason }) }); } catch (err) { alert(err.message); }
      await refreshDashboard();
    }
    async function reject(id) {
      const reason = prompt('거절 사유', 'dashboard reject') || '';
      try { await apiFetch('/actions/reject', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: id, actor_id:'dashboard-operator', reason }) }); } catch (err) { alert(err.message); }
      await refreshDashboard();
    }
    async function review(id, status) {
      const note = prompt(status === 'agree' ? '일치 메모' : '불일치 원인', '') || '';
      try { await apiFetch('/shadow/reviews', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: id, actor_id:'dashboard-operator', agreement_status: status, note }) }); } catch (err) { alert(err.message); }
      await refreshDashboard();
    }
    async function executeAction(id) {
      const reason = prompt('수동 execute 사유', 'dashboard manual execute') || '';
      try { await apiFetch('/actions/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: id, actor_id:'dashboard-operator', reason }) }); } catch (err) { alert('execute 실패: ' + err.message); }
      await refreshDashboard();
    }
    async function flagCase(id) {
      const note = prompt('문제 사례 태깅 — 원인/카테고리', 'flag: ') || '';
      if (!note.trim()) return;
      const tagged = note.startsWith('flag:') ? note : ('flag: ' + note);
      try { await apiFetch('/shadow/reviews', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: id, actor_id:'dashboard-operator', agreement_status:'disagree', note: tagged }) }); } catch (err) { alert(err.message); }
      await refreshDashboard();
    }
    async function togglePolicy(policyId, enabled) {
      try { await apiFetch('/policies/' + policyId, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ enabled }) }); } catch (err) { alert(err.message); }
      await refreshDashboard();
    }

    function riskChipClass(risk) {
      if (risk === 'critical') return 'chip-critical';
      if (risk === 'high' || risk === 'unknown') return 'chip-warn';
      return 'chip-dark';
    }
    function renderMetrics(summary) {
      const metrics = [
        ['결정 수', summary.decision_count ?? 0],
        ['승인 대기', summary.approval_pending_count ?? 0],
        ['Shadow 리뷰 대기', summary.shadow_review_pending_count ?? 0],
        ['차단된 결정', summary.blocked_action_count ?? 0],
        ['Safe Mode 추천', summary.safe_mode_count ?? 0],
        ['Operator 불일치', summary.operator_disagreement_count ?? 0],
        ['일치율', summary.operator_agreement_rate ?? 'n/a'],
        ['실행 명령', summary.command_count ?? 0],
        ['Policy Event', summary.policy_event_count ?? 0],
        ['Policy Block', summary.policy_blocked_count ?? 0],
        ['Alerts', summary.alert_count ?? 0],
        ['Robot Task', summary.robot_task_count ?? 0],
        ['Robot Candidate', summary.robot_candidate_count ?? 0],
        ['Policy (enabled/total)', ((summary.policy_count ?? 0) - (summary.policy_disabled_count ?? 0)) + '/' + (summary.policy_count ?? 0)],
      ];
      document.getElementById('metricGrid').innerHTML = metrics.map(([label, value]) => `
        <div class="metric-card">
          <div class="label">${label}</div>
          <strong class="value">${value}</strong>
        </div>
      `).join('');
    }
    function renderZones(zones) {
      const html = (zones || []).map(zone => `
        <div class="zone-row">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-bold text-ink truncate">${zone.zone_id}</span>
              <span class="chip ${riskChipClass(zone.risk_level)}">${zone.risk_level || 'n/a'}</span>
            </div>
            <div class="text-[11px] text-muted truncate">${zone.current_state_summary || 'summary 없음'}</div>
          </div>
          <div class="text-right text-[11px] text-muted ml-3 hidden sm:block">
            <div>${zone.task_type || '-'}</div>
            <div>${zone.status || '-'}</div>
          </div>
        </div>
      `).join('') || '<div class="placeholder">zone snapshot이 없습니다.</div>';
      const zoneList = document.getElementById('zoneList');
      if (zoneList) zoneList.innerHTML = html;
      const zoneDetailed = document.getElementById('zoneListDetailed');
      if (zoneDetailed) zoneDetailed.innerHTML = html;
    }
    function renderAlerts(items) {
      const full = (items || []).map(item => `
        <div class="alert-row">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] text-muted">#${item.decision_id} · ${item.zone_id} · ${item.alert_type}</span>
            <span class="chip ${item.severity === 'critical' ? 'chip-critical' : 'chip-warn'}">${item.severity}</span>
          </div>
          <div class="text-xs text-ink">${item.summary || 'summary 없음'}</div>
          <div class="text-[10px] text-muted mt-1">validator: ${(item.validator_reason_codes || []).join(', ') || 'none'}</div>
        </div>
      `).join('') || '<div class="placeholder">alert가 없습니다.</div>';
      const main = document.getElementById('alertList');
      if (main) main.innerHTML = full;
      const overview = document.getElementById('alertListOverview');
      if (overview) {
        overview.innerHTML = (items || []).slice(0, 5).map(item => `
          <div class="flex items-center gap-3 py-2 border-b border-outline/10 last:border-0">
            <div class="w-9 h-9 rounded-full bg-surface-low flex items-center justify-center ${item.severity === 'critical' ? 'text-critical' : 'text-warn'}">
              <span class="material-symbols-outlined text-[18px]">warning</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold text-ink truncate">${item.alert_type} · ${item.zone_id}</div>
              <div class="text-[10px] text-muted truncate">${item.summary || ''}</div>
            </div>
            <span class="chip ${item.severity === 'critical' ? 'chip-critical' : 'chip-warn'}">${item.severity}</span>
          </div>
        `).join('') || '<div class="placeholder">alert가 없습니다.</div>';
      }
    }
    function renderRobotTasks(items) {
      document.getElementById('robotList').innerHTML = (items || []).map(item => `
        <div class="zone-row">
          <div>
            <div class="text-sm font-bold text-ink">${item.task_type}</div>
            <div class="text-[11px] text-muted">#${item.decision_id} · ${item.zone_id} · candidate=${item.candidate_id || 'none'}</div>
          </div>
          <div class="flex items-center gap-2">
            <span class="chip chip-dark">${item.priority}</span>
            <span class="chip ${item.status === 'pending' ? 'chip-warn' : 'chip-enabled'}">${item.status}</span>
          </div>
        </div>
      `).join('') || '<div class="placeholder">robot task가 없습니다.</div>';
    }
    function renderRobotCandidates(items) {
      const host = document.getElementById('robotCandidateList');
      if (!host) return;
      host.innerHTML = (items || []).map(item => `
        <div class="zone-row">
          <div>
            <div class="text-sm font-bold text-ink">${item.candidate_id}</div>
            <div class="text-[11px] text-muted">${item.zone_id} · ${item.candidate_type}</div>
          </div>
          <div class="flex items-center gap-2">
            <span class="chip chip-dark">${item.priority}</span>
            <span class="chip ${item.status === 'rejected' ? 'chip-warn' : (item.status === 'approved' ? 'chip-enabled' : 'chip-dark')}">${item.status}</span>
          </div>
        </div>
      `).join('') || '<div class="placeholder">robot candidate가 없습니다.</div>';
    }
    function renderDeviceStatus(zones) {
      const host = document.getElementById('deviceStatusList');
      if (!host) return;
      const entries = (zones || []).filter(z => z.device_status && Object.keys(z.device_status).length > 0);
      if (entries.length === 0) { host.innerHTML = '<div class="placeholder">device_status 기록이 없습니다.</div>'; return; }
      host.innerHTML = entries.map(zone => {
        const devices = Object.entries(zone.device_status).map(([deviceId, info]) => {
          const status = (info && typeof info === 'object') ? (info.status || info.state || JSON.stringify(info)) : info;
          const cls = status === 'fault' ? 'chip-critical' : (status === 'on' ? 'chip-enabled' : 'chip-dark');
          return `<div class="flex items-center justify-between text-[11px] py-1">
            <span class="text-muted truncate flex-1 mr-2">${deviceId}</span>
            <span class="chip ${cls}">${status}</span>
          </div>`;
        }).join('');
        return `<div class="alert-row"><div class="text-xs font-bold text-ink mb-2">${zone.zone_id} · decision=${zone.decision_id || 'none'}</div>${devices}</div>`;
      }).join('');
    }
    function renderActiveConstraints(zones) {
      const host = document.getElementById('activeConstraintsList');
      if (!host) return;
      const entries = (zones || []).filter(z => z.active_constraints && Object.keys(z.active_constraints).length > 0);
      if (entries.length === 0) { host.innerHTML = '<div class="placeholder">현재 active constraint가 없습니다.</div>'; return; }
      host.innerHTML = entries.map(zone => {
        const flags = Object.entries(zone.active_constraints).map(([key, value]) => {
          const on = value === true || value === 'true' || value === 1;
          return `<span class="chip ${on ? 'chip-warn' : 'chip-dark'} mr-1 mb-1 inline-block">${key}${on ? '' : '=' + value}</span>`;
        }).join('');
        return `<div class="alert-row"><div class="text-xs font-bold text-ink mb-2">${zone.zone_id}</div><div>${flags}</div></div>`;
      }).join('');
    }
    function renderShadowWindow(summary) {
      const mini = document.getElementById('shadowWindow');
      if (mini) {
        mini.innerHTML = summary ? `
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="bg-white/10 rounded-xl p-3">
              <div class="text-[10px] uppercase text-white/60">Promote</div>
              <div class="text-2xl font-bold text-white mt-1">${summary.decision_count || 0}</div>
            </div>
            <div class="bg-white/10 rounded-xl p-3">
              <div class="text-[10px] uppercase text-white/60">Hold</div>
              <div class="text-2xl font-bold text-white mt-1">${summary.critical_disagreement_count || 0}</div>
            </div>
            <div class="bg-white/10 rounded-xl p-3">
              <div class="text-[10px] uppercase text-white/60">Result</div>
              <div class="text-lg font-bold text-white mt-1">${summary.promotion_decision || 'n/a'}</div>
            </div>
          </div>
          <div class="text-[11px] text-white/75">Agreement ${(summary.operator_agreement_rate ?? 'n/a')} · Citation ${(summary.citation_coverage ?? 'n/a')}</div>
        ` : '<div class="text-white/70 text-sm">shadow window가 아직 없습니다.</div>';
      }
      const detail = document.getElementById('shadowWindowDetail');
      if (detail) {
        detail.innerHTML = summary ? `
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div class="bg-surface-low rounded-xl p-3">
              <div class="text-[10px] uppercase text-muted">Promotion Decision</div>
              <div class="chip ${summary.promotion_decision === 'rollback' ? 'chip-critical' : (summary.promotion_decision === 'hold' ? 'chip-warn' : 'chip-enabled')} mt-2">${summary.promotion_decision}</div>
            </div>
            <div class="bg-surface-low rounded-xl p-3">
              <div class="text-[10px] uppercase text-muted">Model ID</div>
              <div class="text-xs font-mono text-ink mt-2 truncate">${summary.model_id || 'n/a'}</div>
            </div>
            <div class="bg-surface-low rounded-xl p-3">
              <div class="text-[10px] uppercase text-muted">Prompt ID</div>
              <div class="text-xs font-mono text-ink mt-2">${summary.prompt_id || 'n/a'}</div>
            </div>
            <div class="bg-surface-low rounded-xl p-3">
              <div class="text-[10px] uppercase text-muted">Dataset ID</div>
              <div class="text-xs font-mono text-ink mt-2">${summary.dataset_id || 'n/a'}</div>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div><div class="text-[10px] uppercase text-muted">Decision Count</div><div class="text-2xl font-bold text-ink mt-1">${summary.decision_count}</div></div>
            <div><div class="text-[10px] uppercase text-muted">Agreement Rate</div><div class="text-2xl font-bold text-ink mt-1">${summary.operator_agreement_rate}</div></div>
            <div><div class="text-[10px] uppercase text-muted">Critical Disagreement</div><div class="text-2xl font-bold text-ink mt-1">${summary.critical_disagreement_count}</div></div>
            <div><div class="text-[10px] uppercase text-muted">Citation Coverage</div><div class="text-2xl font-bold text-ink mt-1">${summary.citation_coverage}</div></div>
          </div>
          <div class="text-[11px] text-muted">Window: ${summary.window_start || 'n/a'} ~ ${summary.window_end || 'n/a'}</div>
          <div class="text-[11px] text-muted">policy_mismatch=${summary.policy_mismatch_count} · retrieval_hit_rate=${summary.retrieval_hit_rate}</div>
        ` : '<div class="placeholder">shadow window가 아직 없습니다.</div>';
      }
    }
    function renderAuthContext(actor) {
      const main = document.getElementById('authContext');
      const mini = document.getElementById('authContextMini');
      if (!actor) {
        if (main) main.innerHTML = '';
        if (mini) mini.innerHTML = '';
        return;
      }
      if (main) {
        main.innerHTML = `
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-primary text-[11px] font-bold">${(actor.actor_id || '').slice(0, 2).toUpperCase()}</div>
            <div class="text-right">
              <div class="text-xs font-bold text-ink">${actor.actor_id}</div>
              <div class="text-[10px] text-muted">${actor.role} · ${actor.auth_mode}</div>
            </div>
          </div>
        `;
      }
      if (mini) mini.innerHTML = `<div class="truncate">${actor.actor_id} · ${actor.role}</div>`;
      const runtime = document.getElementById('runtimeInfo');
      if (runtime) {
        runtime.innerHTML = `
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-muted">actor_id</span><span class="font-bold">${actor.actor_id}</span></div>
            <div class="flex justify-between"><span class="text-muted">role</span><span class="font-bold">${actor.role}</span></div>
            <div class="flex justify-between"><span class="text-muted">auth_mode</span><span class="font-bold">${actor.auth_mode}</span></div>
          </div>
        `;
      }
    }
    function renderPolicies(items) {
      document.getElementById('policyList').innerHTML = (items || []).map(item => `
        <div class="alert-row">
          <div class="flex items-start justify-between mb-1">
            <div>
              <div class="text-sm font-bold text-ink">${item.policy_id}</div>
              <div class="text-[10px] text-muted uppercase tracking-wider">${item.policy_stage}</div>
            </div>
            <div class="flex items-center gap-1">
              <span class="chip ${item.enabled ? 'chip-enabled' : 'chip-warn'}">${item.enabled ? 'ENABLED' : 'DISABLED'}</span>
              <span class="chip chip-dark">${item.severity}</span>
            </div>
          </div>
          <div class="text-xs text-ink mb-2 leading-relaxed">${item.description || 'description 없음'}</div>
          <div class="text-[10px] text-muted mb-2">trigger_flags: ${(item.trigger_flags || []).join(', ') || 'none'}</div>
          <button onclick="togglePolicy('${item.policy_id}', ${item.enabled ? 'false' : 'true'})" class="text-[11px] font-semibold ${item.enabled ? 'text-warn' : 'text-primary'} hover:underline">${item.enabled ? '비활성화' : '활성화'}</button>
        </div>
      `).join('') || '<div class="placeholder">policy가 없습니다.</div>';
    }
    function renderPolicyEvents(items) {
      document.getElementById('policyEventList').innerHTML = (items || []).map(item => `
        <div class="alert-row">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] text-muted">decision=#${item.decision_id || 'none'}</span>
            <span class="chip ${item.event_type === 'blocked' ? 'chip-critical' : 'chip-warn'}">${item.event_type}</span>
          </div>
          <div class="text-xs text-ink">${item.request_id}</div>
          <div class="text-[10px] text-muted">policy_ids: ${(item.policy_ids || []).join(', ') || 'none'}</div>
          <div class="text-[10px] text-muted">reasons: ${(item.reason_codes || []).join(', ') || 'none'}</div>
        </div>
      `).join('') || '<div class="placeholder">policy event가 없습니다.</div>';
    }
    function renderCommands(items) {
      const row = (item) => `
        <div class="zone-row">
          <div class="min-w-0 flex-1">
            <div class="text-sm font-bold text-ink truncate">${item.action_type}</div>
            <div class="text-[11px] text-muted truncate">#${item.decision_id} · ${item.target_id}</div>
          </div>
          <span class="chip ${item.status === 'acknowledged' || item.status === 'state_updated' ? 'chip-enabled' : 'chip-warn'} ml-2">${item.status}</span>
        </div>`;
      const html = (items || []).map(row).join('') || '<div class="placeholder">dispatch 기록이 없습니다.</div>';
      const main = document.getElementById('commandList');
      if (main) main.innerHTML = html;
      const overview = document.getElementById('commandListOverview');
      if (overview) overview.innerHTML = (items || []).slice(0, 5).map(row).join('') || '<div class="placeholder">dispatch 기록이 없습니다.</div>';
    }
    function renderDecisions(mode, items) {
      document.getElementById('decisionList').innerHTML = (items || []).map(item => `
        <div class="decision-card">
          <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2 gap-2">
            <div>
              <div class="text-xs text-muted font-mono">ID #${item.decision_id} · ${item.zone_id}</div>
              <div class="text-sm font-bold text-ink mt-1">${item.task_type} · ${item.status}</div>
              <div class="text-[11px] text-muted mt-1">risk=${item.risk_level || 'unknown'} · ${item.prompt_version}</div>
            </div>
            <span class="chip ${riskChipClass(item.risk_level)}">${item.risk_level || 'n/a'}</span>
          </div>
          <div class="text-[11px] text-muted mb-2 italic">${item.current_state_summary || 'no summary'}</div>
          <pre class="bg-surface-low rounded-lg p-3 text-[10px] font-mono overflow-auto max-h-40 custom-scroll">${JSON.stringify(item.validated_output, null, 2)}</pre>
          <div class="text-[10px] text-muted mt-2">citations: ${(item.citations || []).map(c => c.chunk_id).join(', ') || 'none'} · validator: ${(item.validator_reason_codes || []).join(', ') || 'none'}</div>
          <div class="flex flex-wrap gap-2 mt-3">
            ${mode === 'approval' && item.runtime_mode === 'approval' && item.status === 'evaluated' ? `
              <button onclick="approve(${item.decision_id})" class="bg-primary text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">check</span>승인</button>
              <button onclick="reject(${item.decision_id})" class="bg-surface-container text-ink text-[11px] font-semibold px-3 py-1.5 rounded-lg">거절</button>
              <button onclick="executeAction(${item.decision_id})" class="bg-secondary text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg">수동 Execute</button>
            ` : ''}
            ${mode === 'shadow' && item.runtime_mode === 'shadow' && item.status === 'evaluated' ? `
              <button onclick="review(${item.decision_id}, 'agree')" class="bg-primary text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg">일치</button>
              <button onclick="review(${item.decision_id}, 'disagree')" class="bg-warn text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg">불일치</button>
            ` : ''}
            <button onclick="flagCase(${item.decision_id})" class="bg-tertiary text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">flag</span>문제 사례</button>
          </div>
          <div class="text-[10px] text-muted mt-2">approval=${item.latest_approval ? item.latest_approval.approval_status : 'none'} · shadow_review=${item.latest_shadow_review ? item.latest_shadow_review.agreement_status : 'none'}</div>
        </div>
      `).join('') || '<div class="placeholder">아직 decision이 없습니다.</div>';
    }

    function syncZoneHistoryOptions(zones) {
      const select = document.getElementById('historyZoneId');
      if (!select) return;
      const current = select.value;
      const ids = (zones || []).map(z => z.zone_id).filter(Boolean);
      if (!ids.includes('gh-01-zone-a')) ids.unshift('gh-01-zone-a');
      const uniqueIds = Array.from(new Set(ids));
      select.innerHTML = uniqueIds.map(id => `<option value="${id}">${id}</option>`).join('');
      if (uniqueIds.includes(current)) select.value = current;
    }
    async function refreshZoneHistory() {
      const select = document.getElementById('historyZoneId');
      if (!select) return;
      const zoneId = select.value || 'gh-01-zone-a';
      try {
        const body = await apiFetch('/zones/' + encodeURIComponent(zoneId) + '/history?limit=30');
        renderZoneHistory(body.data || {});
      } catch (err) {
        document.getElementById('zoneHistoryCharts').innerHTML = `<div class="placeholder">zone history 조회 실패: ${err.message}</div>`;
      }
    }
    function renderZoneHistory(data) {
      const series = data.sensor_series || {};
      const container = document.getElementById('zoneHistoryCharts');
      const metrics = Object.keys(series);
      if (metrics.length === 0) { container.innerHTML = '<div class="placeholder col-span-full">zone decision이 쌓이면 센서 차트가 나타납니다.</div>'; return; }
      container.innerHTML = metrics.map(metric => {
        const points = series[metric] || [];
        if (points.length === 0) return '';
        const values = points.map(p => p.value);
        const last = values[values.length - 1];
        const min = Math.min(...values);
        const max = Math.max(...values);
        return `
          <div class="bg-surface-low rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] uppercase tracking-wider text-muted font-bold">${metric}</span>
              <span class="text-lg font-bold text-primary">${typeof last === 'number' ? last.toFixed(2) : last}</span>
            </div>
            ${renderSparkline(points)}
            <div class="text-[10px] text-muted mt-2">MIN ${min.toFixed(2)} · MAX ${max.toFixed(2)} · points=${points.length}</div>
          </div>
        `;
      }).join('');
    }
    function renderSparkline(points) {
      if (!points || points.length === 0) return '';
      const values = points.map(p => p.value);
      const minV = Math.min(...values);
      const maxV = Math.max(...values);
      const range = (maxV - minV) || 1;
      const width = 320;
      const height = 48;
      const stepX = points.length > 1 ? width / (points.length - 1) : 0;
      const coords = points.map((p, i) => {
        const x = points.length === 1 ? width / 2 : i * stepX;
        const y = height - ((p.value - minV) / range) * (height - 8) - 4;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
      return `<svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" preserveAspectRatio="none">
        <polyline fill="none" stroke="#2d5338" stroke-width="2" points="${coords}" />
      </svg>`;
    }

    // ===== AI Chat =====
    const chatState = { messages: [], sending: false };
    function chatBubbleUser(content, ts) {
      return `<div class="flex justify-end">
        <div>
          <div class="chat-bubble-user">${escapeHtml(content)}</div>
          <div class="text-[10px] text-muted mt-1 text-right">${ts}</div>
        </div>
      </div>`;
    }
    function chatBubbleAssistant(content, ts) {
      return `<div class="flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-full bg-sidebar flex items-center justify-center">
            <span class="material-symbols-outlined msf text-white text-[14px]">psychology</span>
          </div>
          <span class="text-[11px] font-bold text-primary uppercase tracking-wider">AI AGRO-SYSTEM</span>
        </div>
        <div class="chat-bubble-ai">${escapeHtml(content).replace(/\\n/g, '<br>')}</div>
        <div class="text-[10px] text-muted">${ts}</div>
      </div>`;
    }
    function chatBubbleError(content) {
      return `<div class="chat-bubble-ai chat-bubble-error">${escapeHtml(content)}</div>`;
    }
    function chatBubblePending() {
      return `<div class="chat-bubble-ai animate-pulse">AI 응답을 생성 중입니다...</div>`;
    }
    function escapeHtml(str) {
      return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function renderChat() {
      const host = document.getElementById('chatMessages');
      if (!host) return;
      if (chatState.messages.length === 0) {
        host.innerHTML = `<div class="text-center text-muted text-xs py-6"><span class="chip chip-dark">오늘의 운용 로그 시작</span></div><div class="chat-bubble-ai mx-auto max-w-md">안녕하세요. 적고추 온실 스마트팜 통합 제어 AI 어시스턴트입니다. 현재 존 상태, 정책, 결정을 질문하시면 파인튜닝된 모델이 답변합니다. 하단 빠른 질문 버튼도 활용해보세요.</div>`;
        return;
      }
      host.innerHTML = chatState.messages.map(msg => {
        if (msg.role === 'user') return chatBubbleUser(msg.content, msg.ts || '');
        if (msg.role === 'error') return chatBubbleError(msg.content);
        if (msg.role === 'pending') return chatBubblePending();
        return chatBubbleAssistant(msg.content, msg.ts || '');
      }).join('');
      scrollChatToBottom();
    }
    function scrollChatToBottom() {
      const host = document.getElementById('chatMessages');
      if (host) host.scrollTop = host.scrollHeight;
    }
    function nowLabel() {
      const d = new Date();
      return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }
    function useQuickPrompt(text) {
      const input = document.getElementById('chatInput');
      if (input) input.value = text;
    }
    function clearChat() {
      chatState.messages = [];
      renderChat();
    }
    async function sendChatMessage() {
      if (chatState.sending) return;
      const input = document.getElementById('chatInput');
      const text = (input?.value || '').trim();
      if (!text) return;
      chatState.sending = true;
      chatState.messages.push({ role: 'user', content: text, ts: nowLabel() });
      chatState.messages.push({ role: 'pending', content: '' });
      renderChat();
      input.value = '';
      try {
        const body = {
          messages: chatState.messages.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({ role: m.role, content: m.content })),
          context: { zone_hint: 'gh-01-zone-a' },
        };
        const res = await apiFetch('/ai/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        const reply = res?.data?.reply?.content || '응답을 읽어오지 못했습니다.';
        chatState.messages = chatState.messages.filter(m => m.role !== 'pending');
        chatState.messages.push({ role: 'assistant', content: reply, ts: nowLabel() });
      } catch (err) {
        chatState.messages = chatState.messages.filter(m => m.role !== 'pending');
        chatState.messages.push({ role: 'error', content: 'AI 호출 실패: ' + err.message });
      } finally {
        chatState.sending = false;
        renderChat();
      }
    }
    function renderChatLiveOps(data) {
      const logs = document.getElementById('chatLiveLogs');
      if (logs) {
        const commands = (data.commands || []).slice(0, 5);
        logs.innerHTML = commands.map(c => `
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-surface-low flex items-center justify-center text-primary">
              <span class="material-symbols-outlined text-[18px]">bolt</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold text-ink truncate">${c.action_type}</div>
              <div class="text-[10px] text-muted truncate">#${c.decision_id} · ${c.target_id}</div>
            </div>
            <span class="chip chip-dark">${c.status}</span>
          </div>
        `).join('') || '<div class="placeholder">최근 dispatch 없음</div>';
      }
      const zoneHealth = document.getElementById('chatZoneHealth');
      if (zoneHealth) {
        const zones = (data.zones || []).slice(0, 9);
        const fillers = Math.max(0, 9 - zones.length);
        zoneHealth.innerHTML = zones.map(z => {
          const risk = z.risk_level || 'low';
          const color = risk === 'critical' ? 'bg-critical/40' : (risk === 'high' || risk === 'unknown' ? 'bg-warn/40' : 'bg-primary/40');
          return `<div class="aspect-square rounded-lg ${color} flex items-center justify-center text-[9px] text-white/90 font-bold">${(z.zone_id || '').split('-').pop()}</div>`;
        }).join('') + Array.from({ length: fillers }).map(() => '<div class="aspect-square rounded-lg bg-surface-low"></div>').join('');
      }
      const action = document.getElementById('chatLiveAction');
      const desc = document.getElementById('chatLiveDesc');
      if (action && desc) {
        const anyAlert = (data.alerts || [])[0];
        if (anyAlert) {
          action.textContent = anyAlert.alert_type + ' · ' + anyAlert.severity;
          desc.textContent = anyAlert.summary || '최근 알림을 확인해주세요.';
        } else {
          action.textContent = '정상 운영 중';
          desc.textContent = '현재 critical 알림이 없습니다.';
        }
      }
    }

    async function refreshDashboard() {
      try {
        const response = await apiFetch('/dashboard/data');
        const data = response.data;
        document.getElementById('modeBadge').textContent = data.runtime_mode.mode;
        renderAuthContext(response.actor);
        renderMetrics(data.summary);
        renderZones(data.zones);
        renderShadowWindow(data.shadow_window);
        renderPolicies(data.policies || []);
        renderPolicyEvents(data.policy_events || []);
        renderAlerts(data.alerts);
        renderRobotTasks(data.robot_tasks);
        renderRobotCandidates(data.robot_candidates || []);
        renderDeviceStatus(data.zones || []);
        renderActiveConstraints(data.zones || []);
        renderCommands(data.commands);
        renderDecisions(data.runtime_mode.mode, data.decisions);
        renderChatLiveOps(data);
        syncZoneHistoryOptions(data.zones || []);
        const activeView = document.querySelector('.view.active')?.dataset.view;
        if (activeView === 'zones') await refreshZoneHistory();
      } catch (err) {
        console.error('refreshDashboard failed', err);
      }
    }
    function setupNav() {
      document.querySelectorAll('#sidebarNav a').forEach(link => {
        link.addEventListener('click', (event) => {
          event.preventDefault();
          showView(link.dataset.view);
          if (window.innerWidth < 1024) toggleSidebar(false);
        });
      });
      const input = document.getElementById('chatInput');
      if (input) {
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
          }
        });
      }
    }
    setupNav();
    showView('overview');
    renderChat();
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
  </script>
</body>
</html>"""
