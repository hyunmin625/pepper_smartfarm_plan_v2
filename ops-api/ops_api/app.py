from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session, sessionmaker

from .api_models import (
    ApprovalRequest,
    ApiResponse,
    AutomationEvaluateRequest,
    AutomationRuleRequest,
    AutomationRuleToggleRequest,
    AutomationRuleUpdateRequest,
    AutomationTriggerReviewRequest,
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
from .automation import evaluate_rules, serialize_rule, serialize_trigger
from .automation_runner import AutomationRunner
from .auth import ROLE_PERMISSIONS, ActorIdentity, get_authenticated_actor, require_permission
from .bootstrap import configure_repo_paths
from .config import Settings, load_settings
from .database import build_session_factory, init_db
from .errors import register_exception_handlers
from .logging import configure_logging
from .models import (
    ApprovalRecord,
    AlertRecord,
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    DecisionRecord,
    DeviceRecord,
    DeviceCommandRecord,
    OperatorReviewRecord,
    PolicyEventRecord,
    PolicyEvaluationRecord,
    PolicyRecord,
    RobotCandidateRecord,
    RobotTaskRecord,
    SensorReadingRecord,
    SensorRecord,
    ZoneRecord,
    utc_now,
)
from .planner import ActionDispatchPlanner
from .runtime_mode import load_runtime_mode, save_runtime_mode
from .policy_source import DbPolicySource
from .realtime_broker import RealtimeBroker
from .seed import bootstrap_reference_data
from .shadow_mode import build_window_summary_from_paths, capture_shadow_cases

configure_repo_paths()

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402
from llm_orchestrator import (  # noqa: E402
    LLMOrchestratorService,
    ModelConfig,
    OrchestratorRequest,
    create_retriever,
)
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
    realtime_broker: "RealtimeBroker"
    automation_runner: "AutomationRunner | None" = None


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


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(tz=None).replace(tzinfo=None)
    return parsed


def _group_timeseries(
    rows: list[SensorReadingRecord],
    *,
    bucket_seconds: int,
) -> dict[str, list[dict[str, Any]]]:
    """Bucket sensor readings by metric_name and (optionally) by time bucket.

    Production deployments will route 5m/30m queries to the
    ``zone_metric_5m`` / ``zone_metric_30m`` continuous aggregates from
    migration 002. The current read path keeps an in-process aggregation
    fallback so the API response contract stays stable until the direct
    continuous-aggregate query path is wired in.
    """

    series: dict[str, list[dict[str, Any]]] = {}
    if bucket_seconds <= 0:
        for row in rows:
            metric = row.metric_name
            point = {
                "t": row.measured_at.isoformat() if row.measured_at else None,
                "value": row.metric_value_double,
                "value_text": row.metric_value_text,
                "quality_flag": row.quality_flag,
                "source_id": row.source_id,
            }
            series.setdefault(metric, []).append(point)
        return series

    bucket_accumulator: dict[tuple[str, datetime], list[float]] = {}
    bucket_quality: dict[tuple[str, datetime], str] = {}
    from datetime import timezone as _tz
    for row in rows:
        if row.metric_value_double is None or row.measured_at is None:
            continue
        # sensor_readings.measured_at is stored as naive UTC (TIMESTAMP
        # WITHOUT TIME ZONE); .timestamp() on a naive datetime interprets
        # it in local tz, which shifts buckets off on non-UTC hosts.
        epoch = int(row.measured_at.replace(tzinfo=_tz.utc).timestamp())
        bucket_epoch = epoch - (epoch % bucket_seconds)
        bucket_start = datetime.utcfromtimestamp(bucket_epoch)
        key = (row.metric_name, bucket_start)
        bucket_accumulator.setdefault(key, []).append(row.metric_value_double)
        bucket_quality[key] = row.quality_flag
    for (metric, bucket_start), values in sorted(bucket_accumulator.items()):
        avg = sum(values) / len(values)
        series.setdefault(metric, []).append(
            {
                "t": bucket_start.isoformat(),
                "value": avg,
                "min": min(values),
                "max": max(values),
                "sample_count": len(values),
                "quality_flag": bucket_quality.get((metric, bucket_start)),
            }
        )
    return series


def _read_recent_sensor_readings(
    *,
    session_factory: sessionmaker[Session],
    zone_id: str,
    seconds: int,
    limit: int = 600,
) -> list[dict[str, Any]]:
    """Return the most recent sensor_readings rows for SSE bootstrap."""

    cutoff = datetime.utcnow() - timedelta(seconds=seconds)
    session = session_factory()
    try:
        rows = session.execute(
            select(SensorReadingRecord)
            .where(
                SensorReadingRecord.zone_id == zone_id,
                SensorReadingRecord.measured_at >= cutoff,
                SensorReadingRecord.record_kind == "sensor",
            )
            .order_by(asc(SensorReadingRecord.measured_at))
            .limit(limit)
        ).scalars().all()
    finally:
        session.close()
    return [
        {
            "measured_at": row.measured_at.isoformat() if row.measured_at else None,
            "site_id": row.site_id,
            "zone_id": row.zone_id,
            "record_kind": row.record_kind,
            "source_id": row.source_id,
            "source_type": row.source_type,
            "metric_name": row.metric_name,
            "value_double": row.metric_value_double,
            "value_text": row.metric_value_text,
            "quality_flag": row.quality_flag,
        }
        for row in rows
    ]


def _sse_event(event_name: str, payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, default=str)
    return (f"event: {event_name}\ndata: {body}\n\n").encode("utf-8")


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
    # Build the retriever selected by OPS_API_RETRIEVER_TYPE. Default is
    # 'keyword' so existing deployments stay on the historical backend;
    # operators can opt in to 'openai' (text-embedding-3-small) for a
    # roughly 2.1x recall@5 improvement once the index is built via
    # scripts/build_rag_index.py. If the factory call fails (e.g. the
    # openai index is missing), fall back to keyword rather than blocking
    # app startup.
    rag_index_override = resolved_settings.retriever_rag_index_path or None
    try:
        retriever_instance = create_retriever(
            resolved_settings.retriever_type,
            rag_index_path=rag_index_override,
        )
    except Exception as exc:
        logger.warning(
            "retriever_fallback type=%s error=%s -- using keyword retriever",
            resolved_settings.retriever_type,
            exc,
        )
        retriever_instance = create_retriever("keyword")

    dispatcher = ExecutionDispatcher.default(adapter_kind="mock")
    automation_runner = AutomationRunner(
        session_factory=session_factory,
        settings=resolved_settings,
        dispatcher=dispatcher,
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
            ),
            retriever=retriever_instance,
        ),
        dispatcher=dispatcher,
        planner=ActionDispatchPlanner(),
        realtime_broker=RealtimeBroker(),
        automation_runner=automation_runner,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await automation_runner.start()
        try:
            yield
        finally:
            await automation_runner.stop()

    app = FastAPI(
        title="Pepper Smartfarm Ops API",
        version="0.2.0",
        description="LLM 의사결정, approval dispatch, shadow review, 운영 카탈로그를 제공하는 백엔드",
        lifespan=lifespan,
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
        "/zones/{zone_id}/timeseries",
        tags=["catalog"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def get_zone_timeseries(
        zone_id: str,
        metric: list[str] | None = Query(default=None),
        from_: str | None = Query(default=None, alias="from"),
        to: str | None = Query(default=None),
        interval: str = Query(default="raw"),
        limit: int = Query(default=2000, ge=1, le=20000),
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        if interval not in {"raw", "1m", "5m", "30m"}:
            raise HTTPException(status_code=400, detail="interval must be one of raw|1m|5m|30m")
        from_ts = _parse_iso(from_) or (datetime.utcnow() - timedelta(hours=1))
        to_ts = _parse_iso(to) or datetime.utcnow()
        if from_ts >= to_ts:
            raise HTTPException(status_code=400, detail="from must be earlier than to")
        # Phase 3 read path: interval -> hypertable. The 5m and 30m
        # branches currently aggregate the fetched rows in-process;
        # production PostgreSQL+TimescaleDB should be switched to direct
        # zone_metric_5m / zone_metric_30m reads once that query path is
        # finalized.
        stmt = (
            select(SensorReadingRecord)
            .where(
                SensorReadingRecord.zone_id == zone_id,
                SensorReadingRecord.measured_at >= from_ts,
                SensorReadingRecord.measured_at <= to_ts,
                SensorReadingRecord.record_kind == "sensor",
            )
            .order_by(asc(SensorReadingRecord.measured_at))
            .limit(limit)
        )
        if metric:
            stmt = stmt.where(SensorReadingRecord.metric_name.in_(metric))
        rows = session.execute(stmt).scalars().all()
        bucket_seconds = {"raw": 0, "1m": 60, "5m": 300, "30m": 1800}[interval]
        series = _group_timeseries(rows, bucket_seconds=bucket_seconds)
        return _ok(
            {
                "zone_id": zone_id,
                "interval": interval,
                "from": from_ts.isoformat(),
                "to": to_ts.isoformat(),
                "metric_count": len(series),
                "series": series,
            },
            actor=actor,
            meta={"zone_id": zone_id, "metric_filter": metric, "row_count": len(rows)},
        )

    @app.get(
        "/zones/{zone_id}/stream",
        tags=["catalog"],
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    async def get_zone_stream(
        zone_id: str,
        bootstrap_seconds: int = Query(default=300, ge=0, le=3600),
        services=Depends(get_services),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> StreamingResponse:
        broker: RealtimeBroker = services.realtime_broker
        session_factory = services.session_factory

        async def event_source() -> AsyncIterator[bytes]:
            yield _sse_event(
                "ready",
                {
                    "zone_id": zone_id,
                    "actor_id": actor.actor_id,
                    "role": actor.role,
                    "bootstrap_seconds": bootstrap_seconds,
                },
            )
            if bootstrap_seconds > 0:
                bootstrap = _read_recent_sensor_readings(
                    session_factory=session_factory,
                    zone_id=zone_id,
                    seconds=bootstrap_seconds,
                )
                for record in bootstrap:
                    yield _sse_event("bootstrap", record)
                yield _sse_event("bootstrap_complete", {"count": len(bootstrap)})
            async with broker.subscribe(zone_id=zone_id) as queue:
                while True:
                    try:
                        record = await asyncio.wait_for(queue.get(), timeout=15.0)
                    except asyncio.TimeoutError:
                        yield b": keepalive\n\n"
                        continue
                    yield _sse_event("reading", record)

        return StreamingResponse(
            event_source(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
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
        session: Session = Depends(get_session),
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

        zone_hint = _detect_zone_hint(last_user.content, payload.context)
        grounding_context = _build_chat_grounding_context(
            session=session,
            zone_id=zone_hint,
            extra_context=payload.context or {},
        )
        system_prompt = payload.system_prompt or _build_chat_system_prompt()
        history_text = _render_chat_history(payload.messages[:-1])
        user_payload = json.dumps(
            {
                "task_type": "chat",
                "input": {
                    "zone_id": zone_hint or grounding_context.get("zone_id"),
                    "latest_user_message": last_user.content,
                    "chat_history": history_text,
                    "context": grounding_context,
                    "instruction": (
                        "운영자의 질문에 적고추 온실 운영 관점에서 한국어 자연어로 답한다. "
                        "주어진 context의 숫자와 최근 결정/정책을 근거로 쓰고, 없으면 일반 재배 지식을 사용한다. "
                        "장치 직접 on/off 명령은 금지 — 대시보드 승인 경로로만 권고한다. "
                        "응답 형식은 {\"reply\": \"여기에 한국어 자연어 답변\"} JSON 한 객체로 반환한다."
                    ),
                },
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
                "grounding_keys": sorted(list(grounding_context.keys())),
                "zone_hint": zone_hint,
            },
            actor=actor,
            meta={"system_prompt_id": "chat_v2"},
        )

    @app.get(
        "/ai/config",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def ai_config(
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        """Return the active LLM + retriever + prompt configuration used by
        both the decision path (evaluate_zone) and the assistant chat path
        (/ai/chat). Dashboard UI uses this to render a transparent model
        badge so operators can verify which fine-tune checkpoint is answering.
        """
        model_id = resolved_settings.llm_model_id or ""
        # Only expose the opaque checkpoint suffix when it is a fine-tuned id,
        # otherwise the raw id is short enough to show as-is.
        if model_id.startswith("ft:"):
            model_tail = model_id.rsplit(":", 1)[-1]
            model_label = f"ft:{model_tail}"
            model_family = "gpt-4.1-mini (ds_v11 frozen)" if "ds-v11" in model_id else "fine-tuned"
        else:
            model_label = model_id
            model_family = model_id
        return _ok(
            {
                "llm_provider": resolved_settings.llm_provider,
                "llm_model_id": model_id,
                "llm_model_label": model_label,
                "llm_model_family": model_family,
                "llm_prompt_version": resolved_settings.llm_prompt_version,
                "retriever_type": resolved_settings.retriever_type,
                "chat_system_prompt_id": "chat_v2",
            },
            actor=actor,
        )

    # ---- Automation rules (operator threshold-driven device control) ----

    def _persist_new_rule(session: Session, payload: AutomationRuleRequest, actor: ActorIdentity) -> AutomationRuleRecord:
        rule = AutomationRuleRecord(
            rule_id=payload.rule_id,
            name=payload.name,
            description=payload.description,
            zone_id=payload.zone_id,
            sensor_key=payload.sensor_key,
            operator=payload.operator,
            threshold_value=payload.threshold_value,
            threshold_min=payload.threshold_min,
            threshold_max=payload.threshold_max,
            hysteresis_value=payload.hysteresis_value,
            cooldown_minutes=payload.cooldown_minutes,
            target_device_type=payload.target_device_type,
            target_device_id=payload.target_device_id,
            target_action=payload.target_action,
            action_payload_json=json.dumps(payload.action_payload, ensure_ascii=False),
            priority=payload.priority,
            enabled=1 if payload.enabled else 0,
            runtime_mode_gate=payload.runtime_mode_gate,
            owner_role=payload.owner_role,
            created_by=actor.actor_id,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule

    @app.get(
        "/automation/rules",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_automation_rules(
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        rows = session.scalars(
            select(AutomationRuleRecord).order_by(
                AutomationRuleRecord.priority.asc(), AutomationRuleRecord.id.asc()
            )
        ).all()
        return _ok({"rules": [serialize_rule(r) for r in rows]}, actor=actor)

    @app.post(
        "/automation/rules",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    )
    def create_automation_rule(
        payload: AutomationRuleRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("manage_automation")),
    ) -> dict[str, Any]:
        existing = session.scalar(
            select(AutomationRuleRecord).where(AutomationRuleRecord.rule_id == payload.rule_id)
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"rule_id '{payload.rule_id}' already exists")
        rule = _persist_new_rule(session, payload, actor)
        return _ok(serialize_rule(rule), actor=actor, meta={"created": True})

    @app.get(
        "/automation/rules/{rule_id}",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def get_automation_rule(
        rule_id: str,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        rule = session.scalar(
            select(AutomationRuleRecord).where(AutomationRuleRecord.rule_id == rule_id)
        )
        if rule is None:
            raise HTTPException(status_code=404, detail=f"automation rule '{rule_id}' not found")
        return _ok(serialize_rule(rule), actor=actor)

    @app.patch(
        "/automation/rules/{rule_id}",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def update_automation_rule(
        rule_id: str,
        payload: AutomationRuleUpdateRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("manage_automation")),
    ) -> dict[str, Any]:
        rule = session.scalar(
            select(AutomationRuleRecord).where(AutomationRuleRecord.rule_id == rule_id)
        )
        if rule is None:
            raise HTTPException(status_code=404, detail=f"automation rule '{rule_id}' not found")
        for field_name in (
            "name", "description", "zone_id", "operator",
            "threshold_value", "threshold_min", "threshold_max",
            "hysteresis_value", "cooldown_minutes",
            "target_device_id", "target_action", "priority",
            "runtime_mode_gate",
        ):
            value = getattr(payload, field_name, None)
            if value is not None:
                setattr(rule, field_name, value)
        if payload.enabled is not None:
            rule.enabled = 1 if payload.enabled else 0
        if payload.action_payload is not None:
            rule.action_payload_json = json.dumps(payload.action_payload, ensure_ascii=False)
        rule.updated_at = utc_now()
        session.commit()
        session.refresh(rule)
        return _ok(serialize_rule(rule), actor=actor, meta={"updated": True})

    @app.delete(
        "/automation/rules/{rule_id}",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def delete_automation_rule(
        rule_id: str,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("manage_automation")),
    ) -> dict[str, Any]:
        rule = session.scalar(
            select(AutomationRuleRecord).where(AutomationRuleRecord.rule_id == rule_id)
        )
        if rule is None:
            raise HTTPException(status_code=404, detail=f"automation rule '{rule_id}' not found")
        session.delete(rule)
        session.commit()
        return _ok({"rule_id": rule_id, "deleted": True}, actor=actor)

    @app.patch(
        "/automation/rules/{rule_id}/toggle",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def toggle_automation_rule(
        rule_id: str,
        payload: AutomationRuleToggleRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("manage_automation")),
    ) -> dict[str, Any]:
        rule = session.scalar(
            select(AutomationRuleRecord).where(AutomationRuleRecord.rule_id == rule_id)
        )
        if rule is None:
            raise HTTPException(status_code=404, detail=f"automation rule '{rule_id}' not found")
        rule.enabled = 1 if payload.enabled else 0
        rule.updated_at = utc_now()
        session.commit()
        session.refresh(rule)
        return _ok(serialize_rule(rule), actor=actor, meta={"toggled": True})

    @app.get(
        "/automation/triggers",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def list_automation_triggers(
        limit: int = 50,
        status: str | None = None,
        zone_id: str | None = None,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), 200))
        stmt = select(AutomationRuleTriggerRecord)
        if status:
            stmt = stmt.where(AutomationRuleTriggerRecord.status == status)
        if zone_id:
            stmt = stmt.where(AutomationRuleTriggerRecord.zone_id == zone_id)
        stmt = stmt.order_by(AutomationRuleTriggerRecord.triggered_at.desc()).limit(limit)
        rows = session.scalars(stmt).all()
        return _ok({"triggers": [serialize_trigger(r) for r in rows]}, actor=actor)

    @app.post(
        "/automation/triggers/{trigger_id}/approve",
        tags=["operations"],
        response_model=ApiResponse,
        responses={
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
        },
    )
    def approve_automation_trigger(
        trigger_id: int,
        payload: AutomationTriggerReviewRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("approve_actions")),
    ) -> dict[str, Any]:
        trigger = session.get(AutomationRuleTriggerRecord, trigger_id)
        if trigger is None:
            raise HTTPException(status_code=404, detail="automation trigger not found")
        if trigger.status != "approval_pending":
            raise HTTPException(
                status_code=409,
                detail=f"trigger status must be approval_pending (got {trigger.status})",
            )
        trigger.status = "approved"
        trigger.reviewed_by = actor.actor_id
        trigger.reviewed_at = utc_now()
        trigger.review_reason = payload.reason
        session.commit()
        session.refresh(trigger)
        return _ok(serialize_trigger(trigger), actor=actor, meta={"reviewed": "approved"})

    @app.post(
        "/automation/triggers/{trigger_id}/reject",
        tags=["operations"],
        response_model=ApiResponse,
        responses={
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
        },
    )
    def reject_automation_trigger(
        trigger_id: int,
        payload: AutomationTriggerReviewRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("approve_actions")),
    ) -> dict[str, Any]:
        trigger = session.get(AutomationRuleTriggerRecord, trigger_id)
        if trigger is None:
            raise HTTPException(status_code=404, detail="automation trigger not found")
        if trigger.status != "approval_pending":
            raise HTTPException(
                status_code=409,
                detail=f"trigger status must be approval_pending (got {trigger.status})",
            )
        trigger.status = "rejected"
        trigger.reviewed_by = actor.actor_id
        trigger.reviewed_at = utc_now()
        trigger.review_reason = payload.reason
        session.commit()
        session.refresh(trigger)
        return _ok(serialize_trigger(trigger), actor=actor, meta={"reviewed": "rejected"})

    @app.post(
        "/automation/evaluate",
        tags=["dashboard"],
        response_model=ApiResponse,
        responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    )
    def evaluate_automation_rules(
        payload: AutomationEvaluateRequest,
        session: Session = Depends(get_session),
        actor: ActorIdentity = Depends(require_permission("read_runtime")),
    ) -> dict[str, Any]:
        # Dry-run evaluate with the supplied sensor snapshot. Does not persist
        # triggers so operators can safely preview rules without polluting
        # the audit log. runtime_mode override falls back to the farm-wide mode.
        from .runtime_mode import load_runtime_mode
        mode_state = load_runtime_mode(services.settings.runtime_mode_path)
        runtime_mode = payload.runtime_mode_override or mode_state.mode
        report = evaluate_rules(
            session,
            runtime_mode=runtime_mode,
            sensor_snapshot=payload.sensor_snapshot,
            zone_id=payload.zone_id,
            persist=False,
        )
        return _ok(report.as_dict(), actor=actor, meta={"dry_run": True})

    @app.get("/dashboard", tags=["dashboard"], response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html()

    @app.get("/", include_in_schema=False)
    def dashboard_root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/dashboard", status_code=307)

    return app


def _build_chat_system_prompt() -> str:
    return (
        "너는 'iFarm 통합제어 (적고추 온실 스마트팜)' 시스템의 운영 어시스턴트다. "
        "본체는 적고추 재배 도메인에 파인튜닝된 언어 모델이고, 이 경로에서는 결정 JSON이 아니라 "
        "운영자와의 **자연어 대화**로 상태 설명, 권고, 운영 조언을 제공한다. "
        "\n\n역할과 규칙:\n"
        "- 답변 언어는 **한국어**. 전문 용어(EC, VPD, PAR, DLI 등)는 한국어 설명과 함께 병기한다.\n"
        "- 답변 길이는 2~5문장으로 짧고 명확하게. 필요하면 bullet list.\n"
        "- 입력에 포함된 `context`의 숫자·최근 결정·활성 정책을 근거로 답하고, 숫자를 그대로 인용한다.\n"
        "- context가 비어 있거나 해당 값이 없으면 일반 적고추 재배 지식으로 답하되 '현재 시스템에 해당 데이터가 없다'고 명시한다.\n"
        "- 장치 직접 on/off 지시 금지. 대신 'approval 모드에서 dashboard에서 승인 후 실행'을 권고한다.\n"
        "- 안전 규칙(HSV-01~10, operator_present, manual_override, safe_mode)을 위반하는 제안 금지.\n"
        "- 출력 형식: 반드시 `{\"reply\": \"여기에 한국어 답변\"}` 단일 JSON 객체 한 개. 다른 키 없음. 결정 JSON 템플릿 사용 금지."
    )


def _render_chat_history(messages) -> str:
    lines: list[str] = []
    for msg in messages[-8:]:
        role = "운영자" if msg.role == "user" else ("AI" if msg.role == "assistant" else "시스템")
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines) if lines else "(이전 대화 없음)"


def _detect_zone_hint(user_text: str, context: dict[str, Any] | None) -> str | None:
    """Best-effort zone_id extraction from the user message or context hint."""

    if isinstance(context, dict):
        hint = context.get("zone_id") or context.get("zone_hint")
        if isinstance(hint, str) and hint.strip():
            return hint.strip()
    if not isinstance(user_text, str):
        return None
    import re

    match = re.search(r"gh-\d{2}-[a-z0-9\-]+", user_text)
    if match:
        return match.group(0)
    # Common Korean shorthand like "zone-a", "A구역"
    if "zone-a" in user_text.lower():
        return "gh-01-zone-a"
    if "zone-b" in user_text.lower():
        return "gh-01-zone-b"
    for shorthand, mapped in (("a구역", "gh-01-zone-a"), ("b구역", "gh-01-zone-b"), ("zone a", "gh-01-zone-a"), ("zone b", "gh-01-zone-b")):
        if shorthand in user_text.lower():
            return mapped
    return None


def _build_chat_grounding_context(
    *,
    session: Session,
    zone_id: str | None,
    extra_context: dict[str, Any],
) -> dict[str, Any]:
    """Pull the latest decision, sensor snapshot, and policy highlights for
    the referenced zone so the shared orchestrator model can ground its reply."""

    context: dict[str, Any] = {
        "zone_id": zone_id,
        "operator_context": extra_context,
    }
    if zone_id:
        latest_decision = session.execute(
            select(DecisionRecord)
            .where(DecisionRecord.zone_id == zone_id)
            .order_by(desc(DecisionRecord.id))
            .limit(1)
        ).scalar_one_or_none()
        if latest_decision is not None:
            zone_state = _loads_json(latest_decision.zone_state_json, {})
            current_state = zone_state.get("current_state") if isinstance(zone_state, dict) else None
            validated = _loads_json(latest_decision.validated_output_json, {})
            context["zone_snapshot"] = {
                "decision_id": latest_decision.id,
                "task_type": latest_decision.task_type,
                "runtime_mode": latest_decision.runtime_mode,
                "status": latest_decision.status,
                "risk_level": validated.get("risk_level") if isinstance(validated, dict) else None,
                "current_state": current_state or {},
                "summary": (current_state or {}).get("summary"),
                "recommended_actions": validated.get("recommended_actions") if isinstance(validated, dict) else None,
                "created_at": latest_decision.created_at.isoformat() if latest_decision.created_at else None,
            }
        recent_alerts = session.execute(
            select(AlertRecord)
            .where(AlertRecord.zone_id == zone_id)
            .order_by(desc(AlertRecord.id))
            .limit(3)
        ).scalars().all()
        if recent_alerts:
            context["recent_alerts"] = [
                {
                    "alert_type": row.alert_type,
                    "severity": row.severity,
                    "status": row.status,
                    "summary": row.summary,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in recent_alerts
            ]
    try:
        sensor_rows = session.execute(
            select(SensorReadingRecord)
            .where(SensorReadingRecord.zone_id == zone_id)
            .order_by(desc(SensorReadingRecord.measured_at))
            .limit(16)
        ).scalars().all() if zone_id else []
    except Exception:
        sensor_rows = []
    if sensor_rows:
        latest_metrics: dict[str, Any] = {}
        for row in sensor_rows:
            if row.metric_name in latest_metrics:
                continue
            latest_metrics[row.metric_name] = {
                "value": row.metric_value_double if row.metric_value_double is not None else row.metric_value_text,
                "measured_at": row.measured_at.isoformat() if row.measured_at else None,
                "quality_flag": row.quality_flag,
            }
        context["latest_sensor_readings"] = latest_metrics
    try:
        enabled_policies = session.execute(
            select(PolicyRecord)
            .where(PolicyRecord.enabled.is_(True))
            .order_by(PolicyRecord.policy_stage, PolicyRecord.policy_id)
            .limit(8)
        ).scalars().all()
    except Exception:
        enabled_policies = []
    if enabled_policies:
        context["active_policies"] = [
            {
                "policy_id": row.policy_id,
                "stage": row.policy_stage,
                "severity": row.severity,
                "description": row.description,
            }
            for row in enabled_policies
        ]
    return context


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
  <title>iFarm 통합제어 · 적고추 온실 스마트팜</title>
  <script src="https://cdn.tailwindcss.com?plugins=forms"></script>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/uplot@1.6.30/dist/uPlot.min.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/uplot@1.6.30/dist/uPlot.iife.min.js"></script>
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet" />
  <script>
    // Stitch v2 "Digital Agronomist" palette
    // - background  #f5f7f9, surface lowest #ffffff
    // - primary     #006a26 (vivid growth green)
    // - tertiary    #006571 (atmosphere)
    // - error       #b02500
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            'ink': '#2c2f31',
            'muted': '#595c5e',
            'background': '#f5f7f9',
            'surface': '#f5f7f9',
            'surface-low': '#eef1f3',
            'surface-lowest': '#ffffff',
            'surface-container': '#e5e9eb',
            'surface-container-high': '#dfe3e6',
            'surface-bright': '#ffffff',
            'surface-dim': '#d0d5d8',
            'outline': '#abadaf',
            'outline-variant': '#abadaf',
            'primary': '#006a26',
            'primary-dim': '#005d20',
            'primary-container': '#87ff94',
            'on-primary': '#ffffff',
            'on-primary-container': '#006122',
            'secondary': '#00693e',
            'secondary-container': '#76f2aa',
            'tertiary': '#006571',
            'tertiary-container': '#cdf2f9',
            'warn': '#b46a1d',
            'critical': '#b02500',
            'error': '#b02500',
            'error-container': '#ffdad4',
            'sidebar': '#eef1f3',
            'sidebar-hover': '#e0e7e2',
          },
          fontFamily: {
            sans: ['Pretendard', 'Inter', 'Noto Sans KR', 'system-ui', 'sans-serif'],
            headline: ['Manrope', 'Pretendard', 'Noto Sans KR', 'system-ui', 'sans-serif'],
          },
          boxShadow: {
            'soft': '0 18px 48px -22px rgba(44,47,49,0.18)',
            'softer': '0 8px 24px -16px rgba(44,47,49,0.12)',
            'glow-primary': '0 8px 28px -12px rgba(0,106,38,0.45)',
          },
        },
      },
    }
  </script>
  <style>
    /* ─────────────────────────────────────────────────────────────
       Stitch v2 "Digital Agronomist" — global tokens & primitives
       Philosophy: tonal layering, no 1px borders for sectioning,
       generous whitespace, glass overlays, rounded-full pills.

       ACCESSIBILITY (60-70대 저시력 사용자 대응):
       - 베이스 폰트 16px → 17.5px (root font-size 109%)
       - line-height 1.55 (가독성 우선)
       - 모든 text-[9~13px] arbitrary 클래스를 자동 승급 (아래 a11y 블록)
       - chip / metric / nav-link 컴포넌트 모두 키움
       ───────────────────────────────────────────────────────────── */
    html { font-size: 17.5px; background-color: #f5f7f9; }
    body {
      font-family: 'Pretendard', 'Inter', 'Noto Sans KR', system-ui, sans-serif;
      background: #f5f7f9;
      color: #2c2f31;
      min-height: 100vh;
      line-height: 1.55;
      letter-spacing: -0.005em;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }
    /* a11y — auto-promote tiny arbitrary Tailwind sizes to readable minimums */
    [class*="text-[9px]"]  { font-size: 13px !important; }
    [class*="text-[10px]"] { font-size: 14px !important; }
    [class*="text-[11px]"] { font-size: 15px !important; }
    [class*="text-[12px]"] { font-size: 15px !important; }
    [class*="text-[13px]"] { font-size: 16px !important; }
    [class*="text-[14px]"] { font-size: 16px !important; }
    /* Tailwind utility size bumps */
    .text-xs  { font-size: 14px !important; line-height: 1.5; }
    .text-sm  { font-size: 16px !important; line-height: 1.55; }
    .text-base{ font-size: 17px !important; }
    .text-lg  { font-size: 20px !important; }
    .text-xl  { font-size: 23px !important; }
    .text-2xl { font-size: 28px !important; }
    .text-3xl { font-size: 34px !important; }
    h1, h2, h3, h4 { font-family: 'Manrope', 'Pretendard', 'Noto Sans KR', system-ui, sans-serif; letter-spacing: -0.015em; }
    .font-headline { font-family: 'Manrope', 'Pretendard', 'Noto Sans KR', system-ui, sans-serif; }
    .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
    .msf { font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24; }
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #d0d5d8; border-radius: 999px; }
    .view { display: none; }
    .view.active { display: block; animation: viewFade 0.28s ease; }
    @keyframes viewFade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

    /* Status chips — pill, no border, soft tonal containers
       (a11y: 폰트 13px / padding 7-14, 이전 10px/5-11에서 키움) */
    .chip {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 7px 14px; border-radius: 999px;
      font-size: 13px !important; font-weight: 700; line-height: 1.1;
      letter-spacing: 0.04em; text-transform: uppercase;
      white-space: nowrap;
    }
    .chip-enabled  { background: #d6f5dc; color: #006a26; }
    .chip-enabled::before  { content: ''; width: 8px; height: 8px; border-radius: 999px; background: #006a26; flex-shrink: 0; }
    .chip-warn     { background: #fde9d3; color: #8a4a18; }
    .chip-warn::before     { content: ''; width: 8px; height: 8px; border-radius: 999px; background: #b46a1d; flex-shrink: 0; }
    .chip-critical { background: #ffdad4; color: #9a1f00; }
    .chip-critical::before { content: ''; width: 8px; height: 8px; border-radius: 999px; background: #b02500; animation: pulseDot 1.6s ease-in-out infinite; flex-shrink: 0; }
    .chip-dark     { background: #e5e9eb; color: #2c2f31; }
    .chip-accent   { background: #006a26; color: #ffffff; }
    @keyframes pulseDot { 0%,100% { opacity: 1; } 50% { opacity: 0.45; } }

    .kpi strong { color: #2c2f31; }

    /* Frosted-glass surface — used by sticky header, modals */
    .glass {
      background-color: rgba(245, 247, 249, 0.78);
      backdrop-filter: saturate(180%) blur(20px);
      -webkit-backdrop-filter: saturate(180%) blur(20px);
    }

    /* Mobile drawer overlay — hidden on desktop so the workspace is not dimmed */
    #sidebarBackdrop { display: none; position: fixed; inset: 0; background-color: rgba(15, 23, 27, 0.32); z-index: 40; backdrop-filter: blur(2px); }
    @media (max-width: 1023px) {
      #sidebar { transform: translateX(-100%); transition: transform 0.28s cubic-bezier(.4,0,.2,1); }
      #sidebar.open { transform: translateX(0); }
      #sidebarBackdrop.open { display: block; }
    }
  </style>
</head>
<body class="min-h-screen">
  <aside id="sidebar" class="fixed left-0 top-0 h-screen w-72 flex flex-col bg-surface-low text-ink z-50">
    <div class="px-6 py-7">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-on-primary-container msf">eco</span>
        </div>
        <div class="leading-tight">
          <h1 class="text-[15px] font-extrabold font-headline text-primary tracking-tight">iFarm 통합제어</h1>
          <p class="text-[10px] tracking-[0.14em] uppercase text-muted mt-0.5">Digital Agronomist</p>
        </div>
      </div>
    </div>
    <nav id="sidebarNav" class="flex-1 px-3 py-2 space-y-1 overflow-y-auto custom-scroll">
      <a data-view="overview" class="nav-link active">
        <span class="material-symbols-outlined text-[20px]">dashboard</span>
        <span>대시보드</span>
      </a>
      <a data-view="zones" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">thermostat</span>
        <span>구역 모니터링</span>
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
      <a data-view="automation" class="nav-link">
        <span class="material-symbols-outlined text-[20px]">tune</span>
        <span>환경설정</span>
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
    <div class="px-5 py-5 space-y-3">
      <div class="rounded-2xl bg-surface-lowest p-4 shadow-softer">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] uppercase tracking-[0.12em] font-bold text-muted">운영 모드</span>
          <span id="modeBadge" class="chip chip-enabled">loading</span>
        </div>
        <div id="authContextMini" class="text-[11px] text-muted leading-snug"></div>
        <button onclick="toggleMode()" class="mt-3 w-full bg-primary hover:bg-primary-dim text-white text-[11px] font-bold uppercase tracking-wider rounded-full py-2.5 transition shadow-glow-primary">모드 전환</button>
      </div>
    </div>
  </aside>
  <div id="sidebarBackdrop" onclick="toggleSidebar(false)"></div>

  <header class="lg:ml-72 sticky top-0 min-h-[88px] z-30 glass flex items-center justify-between px-5 md:px-10 py-4">
    <div class="flex items-center gap-3">
      <button onclick="toggleSidebar()" class="lg:hidden text-ink p-2 hover:bg-surface-low rounded-full">
        <span class="material-symbols-outlined">menu</span>
      </button>
      <div>
        <p class="text-[10px] uppercase tracking-[0.14em] text-primary font-bold leading-none">Live Monitoring</p>
        <h2 id="viewTitle" class="text-lg md:text-xl font-extrabold font-headline text-ink mt-1 leading-none">대시보드</h2>
        <p id="viewSub" class="text-[11px] text-muted hidden md:block mt-0.5">전체 운영 현황 요약</p>
      </div>
    </div>
    <div class="flex items-center gap-3 md:gap-5">
      <span id="headerChampionChip" class="chip chip-dark hidden max-w-[220px] truncate" title="champion model">champion: —</span>
      <div class="hidden md:flex items-center gap-2 text-[11px] text-muted font-semibold">
        <span class="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
        <span>System Status: Optimal</span>
      </div>
      <button class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-low transition text-muted">
        <span class="material-symbols-outlined">notifications</span>
      </button>
      <div id="authContext" class="hidden md:block"></div>
    </div>
  </header>

  <main class="lg:ml-72 px-5 md:px-10 py-7 md:py-9 max-w-[1700px]">

    <!-- 대시보드 -->
    <section class="view active" data-view="overview">

      <!-- Hero strip — kicker + headline + actions -->
      <div class="hero-strip mb-6">
        <div>
          <span class="section-kicker">Live Monitoring Active</span>
          <h2 class="text-2xl md:text-3xl font-extrabold font-headline text-ink mt-3 leading-tight">적고추 온실 통합제어</h2>
          <p class="text-[12px] md:text-[13px] text-muted mt-2 max-w-xl leading-relaxed">AI · Validator · Gateway 3-layer safety pipeline · TimescaleDB 실시간 센서 스트림 · runtime gate 기반 자동 제어</p>
        </div>
        <div class="hidden md:flex items-center gap-2">
          <button onclick="showView('shadow')" class="btn-secondary">
            <span class="material-symbols-outlined text-[16px]">history</span>
            <span>Shadow Window</span>
          </button>
          <button onclick="showView('automation')" class="btn-primary">
            <span class="material-symbols-outlined text-[16px]">tune</span>
            <span>Override Controls</span>
          </button>
        </div>
      </div>

      <!-- Metric strip — sensor snapshot -->
      <div class="mb-6">
        <div class="flex items-end justify-between mb-3 px-1">
          <span class="section-kicker">Sensor Snapshot</span>
          <span class="text-[10px] uppercase tracking-[0.12em] text-muted font-bold">Live · Auto-refresh 5s</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" id="metricGrid"></div>
      </div>

      <!-- Hero asymmetric — greenhouse visual + right rail -->
      <div class="hero-grid mb-6">

        <!-- LEFT — greenhouse visual + zone list -->
        <div class="card !p-0 overflow-hidden">
          <div class="greenhouse-visual">
            <!-- Sensor pins (mock positions; live values come from /metrics endpoints) -->
            <div class="sensor-pin" style="top: 28%; left: 22%;"><span class="pin-label">Zone A · 24.5°C</span></div>
            <div class="sensor-pin" style="top: 58%; left: 52%;"><span class="pin-label">Zone B · 62%RH</span></div>
            <div class="sensor-pin" style="top: 36%; left: 78%;"><span class="pin-label">CO₂ 840 ppm</span></div>

            <!-- Hero overlay text -->
            <div class="absolute top-5 left-5 z-10">
              <span class="section-kicker" style="color:#006a26;">Greenhouse Visual</span>
              <h3 class="text-base font-extrabold font-headline text-ink mt-2 leading-none">GH-PEPPER-01</h3>
              <p class="text-[11px] text-muted mt-1">3 zones · 12 nodes online</p>
            </div>

            <!-- Live camera mock -->
            <div class="absolute bottom-5 left-5 z-10 bg-white rounded-2xl shadow-soft p-3 flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-ink flex items-center justify-center relative overflow-hidden">
                <span class="material-symbols-outlined text-white msf">videocam</span>
                <div class="absolute top-1 right-1 flex items-center gap-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-error animate-pulse"></span>
                </div>
              </div>
              <div class="leading-tight">
                <p class="text-[9px] uppercase tracking-[0.12em] text-muted font-bold">Live Feed</p>
                <p class="text-[12px] font-extrabold font-headline text-ink">CAM-01 · Zone A</p>
              </div>
            </div>
          </div>

          <div class="px-6 md:px-7 pt-5 pb-6">
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="section-kicker">Zone Status</span>
                <h3 class="text-base font-extrabold font-headline text-ink mt-1">구역 상태 요약</h3>
              </div>
              <button onclick="showView('zones')" class="text-[11px] uppercase tracking-[0.10em] font-bold text-primary hover:underline">View All ›</button>
            </div>
            <div id="zoneList" class="space-y-3"></div>
          </div>
        </div>

        <!-- RIGHT rail — shadow strategy + schedule -->
        <div class="space-y-5">
          <!-- Shadow window — primary gradient hero card -->
          <div class="card text-white" style="background: linear-gradient(155deg, #006a26 0%, #00833a 55%, #00913a 100%); box-shadow: 0 24px 56px -28px rgba(0,106,38,0.55);">
            <div class="flex items-center justify-between mb-2">
              <p class="text-[10px] tracking-[0.14em] uppercase text-white/75 font-bold">Shadow Window</p>
              <span class="material-symbols-outlined text-white/70 text-[18px]">visibility</span>
            </div>
            <h3 class="text-lg font-extrabold font-headline mb-4 leading-tight">Automation Strategy Review</h3>
            <div id="shadowWindow" class="text-white/90 text-[12px] leading-relaxed"></div>
          </div>

          <!-- Schedule rail (uses commandListOverview as audit timeline) -->
          <div class="card">
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="section-kicker">Audit Trail</span>
                <h3 class="text-base font-extrabold font-headline text-ink mt-1">최근 실행</h3>
              </div>
              <button onclick="showView('system')" class="text-[11px] uppercase tracking-[0.10em] font-bold text-primary hover:underline">Logs ›</button>
            </div>
            <div id="commandListOverview" class="space-y-3"></div>
          </div>
        </div>
      </div>

      <!-- Bottom — alerts wide card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <span class="section-kicker">Active Alerts</span>
            <h3 class="text-base font-extrabold font-headline text-ink mt-1">최근 알림 · validator · risk · policy</h3>
          </div>
          <button onclick="showView('alerts')" class="btn-secondary">
            <span class="material-symbols-outlined text-[16px]">notifications_active</span>
            <span>View All Alerts</span>
          </button>
        </div>
        <div id="alertListOverview" class="space-y-3"></div>
      </div>
    </section>

    <!-- 구역 모니터링 -->
    <section class="view" data-view="zones">
      <div class="card mb-5">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <p class="text-[11px] tracking-wider uppercase text-primary font-bold mb-1">Zone 실시간 시계열</p>
            <h3 class="text-lg font-bold text-ink">Zone Realtime Chart</h3>
            <p class="text-[11px] text-muted mt-1">TimescaleDB / SSE 기반 초단위 실시간 · uPlot canvas 렌더링</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select id="historyZoneId" class="bg-surface-low rounded-xl px-3 py-2 text-xs">
              <option value="gh-01-zone-a">gh-01-zone-a</option>
            </select>
            <select id="historyWindow" class="bg-surface-low rounded-xl px-3 py-2 text-xs">
              <option value="60">최근 60초</option>
              <option value="300" selected>최근 5분</option>
              <option value="1800">최근 30분</option>
              <option value="21600">최근 6시간</option>
              <option value="86400">최근 24시간</option>
            </select>
            <span id="streamStatus" class="chip chip-dark">disconnected</span>
            <button onclick="refreshZoneHistory()" class="bg-primary text-white text-xs font-semibold rounded-lg px-4 py-2 flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">refresh</span>
              <span>Refresh</span>
            </button>
          </div>
        </div>
        <div id="zoneHistoryCharts" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"></div>
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
          <input id="zoneId" value="gh-01-zone-a" class="w-full bg-surface-low rounded-xl px-3 py-2 text-sm" />
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Target Task</label>
          <select id="taskType" class="w-full bg-surface-low rounded-xl px-3 py-2 text-sm">
            <option value="state_judgement">state_judgement</option>
            <option value="action_recommendation">action_recommendation</option>
            <option value="failure_response">failure_response</option>
            <option value="robot_task_prioritization">robot_task_prioritization</option>
            <option value="forbidden_action">forbidden_action</option>
          </select>
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Growth Stage</label>
          <input id="growthStage" value="fruiting" class="w-full bg-surface-low rounded-xl px-3 py-2 text-sm" />
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Current State JSON</label>
          <textarea id="currentState" rows="6" class="w-full bg-surface-low rounded-xl px-3 py-2 text-xs font-mono">{ "air_temp_c": 27.5, "rh_pct": 71.0, "substrate_moisture_pct": 54.0, "co2_ppm": 430, "feed_ph": 5.9 }</textarea>
          <label class="block text-[11px] uppercase tracking-wider font-bold text-muted mb-1 mt-3">Sensor Quality JSON</label>
          <textarea id="sensorQuality" rows="2" class="w-full bg-surface-low rounded-xl px-3 py-2 text-xs font-mono">{ "overall": "good" }</textarea>
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
          <div class="flex items-center justify-between pb-4 border-b border-surface-container">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center shadow-glow-primary">
                <span class="material-symbols-outlined msf text-white text-[22px]">psychology</span>
              </div>
              <div>
                <h3 class="text-sm font-bold text-ink">AI AGRO-SYSTEM</h3>
                <p id="aiAssistantMeta" class="text-[10px] text-muted uppercase tracking-wider">적고추 온실 파인튜닝 모델 연결 중...</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span id="aiAssistantModelChip" class="chip chip-dark hidden">champion: —</span>
              <div class="chip chip-enabled">
                <span class="w-2 h-2 bg-primary rounded-full animate-pulse mr-1"></span>
                활성
              </div>
            </div>
          </div>
          <div id="chatMessages" class="flex-1 overflow-y-auto custom-scroll py-4 space-y-4"></div>
          <div class="border-t border-surface-container pt-4">
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
          <p class="text-[11px] tracking-wider uppercase text-primary font-bold">Grounding Inspector</p>
          <h3 class="text-xl font-bold text-ink mb-4">마지막 응답 근거</h3>
          <div id="groundingInspector" class="bg-primary rounded-2xl p-5 text-white mb-4">
            <p class="text-[10px] uppercase tracking-wider text-white/60">champion</p>
            <h4 class="text-sm font-bold mt-1 mb-2 break-all" id="groundingModelLabel">대기 중</h4>
            <div class="text-[11px] text-white/80 space-y-1">
              <div><span class="text-white/50 uppercase tracking-wider text-[9px] mr-1">provider</span><span id="groundingProvider">—</span></div>
              <div><span class="text-white/50 uppercase tracking-wider text-[9px] mr-1">zone_hint</span><span id="groundingZoneHint">—</span></div>
              <div><span class="text-white/50 uppercase tracking-wider text-[9px] mr-1">grounding_keys</span><span id="groundingKeys">—</span></div>
              <div><span class="text-white/50 uppercase tracking-wider text-[9px] mr-1">attempts</span><span id="groundingAttempts">—</span></div>
            </div>
          </div>
          <div class="mb-4">
            <p class="text-[10px] uppercase tracking-wider text-muted mb-2">최근 dispatch</p>
            <div class="space-y-3 max-h-40 overflow-y-auto custom-scroll" id="chatLiveLogs"></div>
          </div>
          <div class="mt-auto bg-surface-low rounded-xl p-4">
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

    <!-- 환경설정 · 자동화 규칙 -->
    <section class="view" data-view="automation">
      <div class="card mb-5">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div>
            <h3 class="text-sm font-bold text-ink">환경설정 — 사용자 자동화 규칙</h3>
            <p class="text-[10px] text-muted uppercase tracking-wider">sensor threshold → device control (shadow → approval → execute)</p>
          </div>
          <div class="flex items-center gap-2">
            <span id="automationRuntimeChip" class="chip chip-dark">runtime: —</span>
            <button onclick="openAutomationRuleModal()" class="chip chip-enabled hover:opacity-90">
              <span class="material-symbols-outlined text-[14px] mr-1">add</span>새 규칙
            </button>
          </div>
        </div>
        <div class="bg-surface-low rounded-xl p-3 mb-4 text-[11px] text-muted leading-relaxed">
          규칙은 <b>runtime_mode_gate</b> 와 전역 <b>runtime_mode</b> 중 <b>더 엄격한 쪽</b>을 따릅니다. 신규 규칙은 <code class="bg-white px-1 rounded">approval</code> 게이트로 시작해 실측 검증 후 <code class="bg-white px-1 rounded">execute</code>로 승격하세요. 모든 trigger는 <code class="bg-white px-1 rounded">policy_engine.output_validator</code> + <code class="bg-white px-1 rounded">execution_gateway.guards</code>를 거쳐 안전합니다.
        </div>
        <div id="automationRuleList" class="space-y-3"></div>
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-ink">최근 trigger</h3>
          <span class="text-[11px] text-muted">policy_engine + guards 경유 상태</span>
        </div>
        <div id="automationTriggerList" class="space-y-3"></div>
      </div>
    </section>

    <!-- 자동화 규칙 생성/편집 모달 -->
    <div id="automationRuleModal" class="fixed inset-0 bg-black/60 z-50 hidden items-center justify-center p-4 overflow-y-auto">
      <div class="bg-surface w-full max-w-2xl rounded-2xl p-6 my-8">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-ink" id="automationModalTitle">새 자동화 규칙</h3>
          <button onclick="closeAutomationRuleModal()" class="text-muted hover:text-ink">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <form id="automationRuleForm" class="space-y-4 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">rule_id *</span>
              <input type="text" id="ruleField_rule_id" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="rh-rain-close-vent">
            </label>
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">name *</span>
              <input type="text" id="ruleField_name" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="강우 시 천장 닫기">
            </label>
          </div>
          <label class="block">
            <span class="block text-[10px] text-muted uppercase mb-1">description</span>
            <textarea id="ruleField_description" rows="2" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="강우량이 0.5mm/10min를 넘으면 천장 개폐기를 닫는다"></textarea>
          </label>
          <div class="grid grid-cols-3 gap-3">
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">zone_id</span>
              <input type="text" id="ruleField_zone_id" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="(전 구역)">
            </label>
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">priority</span>
              <input type="number" id="ruleField_priority" value="100" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
            </label>
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">cooldown 분</span>
              <input type="number" id="ruleField_cooldown_minutes" value="15" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
            </label>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">sensor_key *</span>
              <select id="ruleField_sensor_key" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
                <optgroup label="외부 기상">
                  <option value="ext_air_temp_c">외부 온도 (℃)</option>
                  <option value="ext_rh_pct">외부 습도 (%)</option>
                  <option value="ext_wind_dir_deg">외부 풍향 (°)</option>
                  <option value="ext_wind_speed_m_s">외부 풍속 (m/s)</option>
                  <option value="ext_rainfall_mm">강우량 (mm)</option>
                </optgroup>
                <optgroup label="내부 기상">
                  <option value="air_temp_c">내부 온도 (℃)</option>
                  <option value="rh_pct">내부 습도 (%)</option>
                  <option value="co2_ppm">CO2 (ppm)</option>
                  <option value="vpd_kpa">VPD (kPa)</option>
                  <option value="par_umol_m2_s">PAR (μmol/m²/s)</option>
                </optgroup>
                <optgroup label="배지 - Grodan Delta">
                  <option value="substrate_delta_temp_c">Delta 슬래브 온도 (℃)</option>
                  <option value="substrate_delta_moisture_pct">Delta 수분 (%)</option>
                  <option value="substrate_delta_ph">Delta pH</option>
                </optgroup>
                <optgroup label="배지 - GT Master">
                  <option value="substrate_gt_master_temp_c">GT Master 슬래브 온도 (℃)</option>
                  <option value="substrate_gt_master_moisture_pct">GT Master 수분 (%)</option>
                  <option value="substrate_gt_master_ph">GT Master pH</option>
                </optgroup>
                <optgroup label="공통 근권">
                  <option value="feed_ec_ds_m">공급 EC (dS/m)</option>
                  <option value="drain_ec_ds_m">배액 EC (dS/m)</option>
                  <option value="feed_ph">공급 pH</option>
                  <option value="drain_ph">배액 pH</option>
                </optgroup>
              </select>
            </label>
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">operator *</span>
              <select id="ruleField_operator" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
                <option value="gt">&gt; (초과)</option>
                <option value="gte">&ge; (이상)</option>
                <option value="lt">&lt; (미만)</option>
                <option value="lte">&le; (이하)</option>
                <option value="eq">= (같음)</option>
                <option value="between">∈ [min, max] (범위)</option>
              </select>
            </label>
            <label class="block col-span-1">
              <span class="block text-[10px] text-muted uppercase mb-1">threshold_value</span>
              <input type="number" step="any" id="ruleField_threshold_value" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
            </label>
          </div>
          <div class="grid grid-cols-2 gap-3" id="ruleFieldBetweenRow" style="display:none;">
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">threshold_min</span>
              <input type="number" step="any" id="ruleField_threshold_min" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
            </label>
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">threshold_max</span>
              <input type="number" step="any" id="ruleField_threshold_max" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
            </label>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">target_device_type *</span>
              <select id="ruleField_target_device_type" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
                <option value="roof_vent">천장 개폐기 (roof_vent)</option>
                <option value="hvac_geothermal">지하수 냉난방기 (hvac_geothermal)</option>
                <option value="humidifier">가습기 (humidifier)</option>
                <option value="fertigation_mixer">양액 비율 (fertigation_mixer)</option>
                <option value="irrigation_pump">관수 펌프 (irrigation_pump)</option>
                <option value="shade_curtain">차광 커튼 (shade_curtain)</option>
                <option value="fan_circulation">순환팬 (fan_circulation)</option>
                <option value="co2_injector">CO2 공급기 (co2_injector)</option>
              </select>
            </label>
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">target_action *</span>
              <input type="text" id="ruleField_target_action" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="adjust_vent">
            </label>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">target_device_id</span>
              <input type="text" id="ruleField_target_device_id" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="(선택)">
            </label>
            <label class="block">
              <span class="block text-[10px] text-muted uppercase mb-1">runtime_mode_gate *</span>
              <select id="ruleField_runtime_mode_gate" required class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30">
                <option value="shadow">shadow (로그만)</option>
                <option value="approval" selected>approval (승인 요청)</option>
                <option value="execute">execute (바로 실행)</option>
              </select>
            </label>
          </div>
          <label class="block">
            <span class="block text-[10px] text-muted uppercase mb-1">action_payload (JSON)</span>
            <textarea id="ruleField_action_payload" rows="2" class="w-full rounded-xl px-3 py-2 bg-surface-low text-ink focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono text-[11px]" placeholder='{"target_position_pct": 0}'></textarea>
          </label>
          <div class="flex items-center justify-between pt-4 border-t border-surface-container">
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" id="ruleField_enabled" checked class="rounded">
              <span>활성화</span>
            </label>
            <div class="flex gap-2">
              <button type="button" onclick="closeAutomationRuleModal()" class="chip chip-dark">취소</button>
              <button type="submit" class="chip chip-enabled">저장</button>
            </div>
          </div>
          <div id="automationRuleFormError" class="text-[11px] text-critical hidden"></div>
        </form>
      </div>
    </div>

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
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <div class="card" id="aiRuntimeCard">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-ink">AI Runtime</h3>
              <p class="text-[10px] text-muted uppercase tracking-wider">champion · retriever · prompt</p>
            </div>
            <span id="aiRuntimeChip" class="chip chip-enabled">활성</span>
          </div>
          <div id="aiRuntimeBody" class="space-y-3 text-sm">
            <div class="placeholder">/ai/config 조회 중...</div>
          </div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-ink">Runtime Mode · Actor</h3>
              <p class="text-[10px] text-muted uppercase tracking-wider">shadow / approval / execute</p>
            </div>
            <span id="runtimeModeChip" class="chip chip-dark">unknown</span>
          </div>
          <div id="runtimeInfo"></div>
        </div>
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-ink">Execution History</h3>
          <span class="text-[11px] text-muted">최근 dispatch</span>
        </div>
        <div id="commandList" class="space-y-3"></div>
      </div>
    </section>

  </main>

  <style>
    /* ─────────────────────────────────────────────────────────────
       Component layer — Stitch v2 surface hierarchy
       L0 background (#f5f7f9) → L1 surface-low (#eef1f3) →
       L2 surface-lowest (#ffffff). No 1px borders for sectioning.
       ───────────────────────────────────────────────────────────── */
    .card {
      background: #ffffff;
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 18px 48px -28px rgba(44,47,49,0.16), 0 2px 6px -2px rgba(44,47,49,0.04);
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .card:hover { box-shadow: 0 24px 56px -28px rgba(44,47,49,0.22), 0 4px 10px -4px rgba(44,47,49,0.06); }
    @media (min-width: 768px) { .card { padding: 30px; } }

    /* Sidebar nav — light surface with primary pill indicator on the left */
    .nav-link {
      position: relative;
      display: flex; align-items: center; gap: 14px;
      padding: 14px 18px; margin: 0 6px;
      border-radius: 14px;
      font-size: 16px; font-weight: 600;
      color: #595c5e;
      cursor: pointer;
      transition: background 0.18s ease, color 0.18s ease;
      white-space: nowrap;
    }
    .nav-link .material-symbols-outlined { font-size: 24px !important; }
    .nav-link:hover { background: #e0e7e2; color: #006a26; }
    .nav-link.active {
      background: #d6f5dc;
      color: #006a26;
      font-weight: 700;
    }
    .nav-link.active::before {
      content: '';
      position: absolute; left: -10px; top: 8px; bottom: 8px;
      width: 4px; border-radius: 999px;
      background: #006a26;
    }
    .nav-link.active .material-symbols-outlined { font-variation-settings: 'FILL' 1, 'wght' 500; }

    /* Decision/list cards — tonal surface, no border */
    .decision-card {
      background: #ffffff;
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 8px 24px -18px rgba(44,47,49,0.14);
    }

    /* Metric cards — Stitch hero metric with bottom accent
       (a11y: label 13px / value 30px, 이전 10/24에서 키움) */
    .metric-card {
      background: #ffffff;
      border-radius: 18px;
      padding: 20px 22px;
      box-shadow: 0 8px 24px -18px rgba(44,47,49,0.14);
      border-bottom: 4px solid #d6f5dc;
      transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
      min-width: 0;
    }
    .metric-card:hover { transform: translateY(-2px); border-bottom-color: #006a26; box-shadow: 0 14px 32px -20px rgba(0,106,38,0.30); }
    .metric-card .label {
      font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.08em;
      color: #595c5e; font-weight: 700;
      font-family: 'Manrope', 'Pretendard', sans-serif;
      line-height: 1.3;
    }
    .metric-card .value {
      font-size: 30px !important; font-weight: 800; color: #2c2f31;
      margin-top: 8px; display: block;
      font-family: 'Manrope', 'Pretendard', sans-serif;
      letter-spacing: -0.02em; line-height: 1.1;
      word-break: keep-all;
    }
    .metric-card.metric-champion {
      background: linear-gradient(135deg, #006a26 0%, #00913a 100%);
      color: #ffffff;
      border-bottom-color: #87ff94;
    }
    .metric-card.metric-champion .label { color: rgba(255,255,255,0.85); }
    .metric-card.metric-champion .value {
      color: #ffffff; font-size: 17px !important;
      line-height: 1.3; word-break: break-word; font-weight: 700;
    }

    /* Zone & alert rows — surface-low with rounded corners, no border */
    .zone-row {
      background: #eef1f3;
      border-radius: 14px;
      padding: 18px 22px;
      display: flex; justify-content: space-between; align-items: center;
      gap: 16px;
      font-size: 16px;
      transition: background 0.18s ease;
      flex-wrap: wrap;
    }
    .zone-row:hover { background: #e5e9eb; }
    .alert-row {
      background: #eef1f3;
      border-radius: 14px;
      padding: 18px 22px;
      font-size: 16px;
      transition: background 0.18s ease;
    }
    .alert-row:hover { background: #e5e9eb; }

    .placeholder { text-align: center; color: #abadaf; padding: 32px; font-size: 16px; }

    /* Chat bubbles — primary gradient for user, surface-lowest for AI
       (a11y: 16px 본문 / line-height 1.6) */
    .chat-bubble-user {
      max-width: 80%;
      background: linear-gradient(135deg, #006a26 0%, #00833a 100%);
      color: #ffffff;
      padding: 16px 22px;
      border-radius: 22px 22px 6px 22px;
      font-size: 16px !important; line-height: 1.6;
      box-shadow: 0 8px 24px -14px rgba(0,106,38,0.45);
    }
    .chat-bubble-ai {
      max-width: 88%;
      background: #ffffff;
      color: #2c2f31;
      padding: 18px 22px;
      border-radius: 22px 22px 22px 6px;
      font-size: 16px !important; line-height: 1.65;
      box-shadow: 0 8px 24px -18px rgba(44,47,49,0.16);
    }
    .chat-bubble-error { background: #ffdad4; color: #9a1f00; }

    /* Primary action button — rounded-full, with subtle glow */
    .btn-primary {
      display: inline-flex; align-items: center; gap: 10px;
      background: #006a26; color: #ffffff;
      padding: 13px 24px; border-radius: 999px;
      font-size: 15px !important; font-weight: 700; letter-spacing: 0.02em;
      box-shadow: 0 8px 24px -12px rgba(0,106,38,0.55);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      white-space: nowrap;
    }
    .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 12px 32px -12px rgba(0,106,38,0.6); }
    .btn-primary:active { transform: translateY(0); }
    .btn-primary .material-symbols-outlined { font-size: 20px !important; }
    .btn-secondary {
      display: inline-flex; align-items: center; gap: 10px;
      background: #eef1f3; color: #2c2f31;
      padding: 13px 22px; border-radius: 999px;
      font-size: 15px !important; font-weight: 700;
      transition: background 0.15s ease;
      white-space: nowrap;
    }
    .btn-secondary:hover { background: #dfe3e6; }
    .btn-secondary .material-symbols-outlined { font-size: 20px !important; }

    /* Form inputs — bigger touch targets and font-size for low vision */
    input[type="text"], input[type="number"], input[type="email"], input[type="password"],
    select, textarea {
      font-size: 16px !important;
      line-height: 1.5;
      padding: 12px 14px !important;
    }
    label { font-size: 14px !important; }

    /* ─────────────────────────────────────────────────────────────
       Layout primitives — Stitch v3 hero & asymmetric grids
       ───────────────────────────────────────────────────────────── */
    .hero-strip {
      position: relative;
      display: flex; align-items: center; justify-content: space-between;
      gap: 24px;
      padding: 32px 36px;
      border-radius: 24px;
      background: linear-gradient(135deg, #ffffff 0%, #eef1f3 100%);
      box-shadow: 0 18px 48px -28px rgba(44,47,49,0.18);
      overflow: hidden;
      flex-wrap: wrap;
    }
    .hero-strip::after {
      content: '';
      position: absolute; right: -60px; top: -60px;
      width: 220px; height: 220px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(0,106,38,0.10) 0%, rgba(0,106,38,0) 70%);
      pointer-events: none;
    }
    .hero-strip > * { position: relative; z-index: 1; }
    .section-kicker {
      display: inline-flex; align-items: center; gap: 8px;
      font-size: 13px !important; font-weight: 800;
      text-transform: uppercase; letter-spacing: 0.14em;
      color: #006a26;
    }
    .section-kicker::before {
      content: ''; width: 6px; height: 6px; border-radius: 999px; background: #006a26;
      box-shadow: 0 0 0 4px rgba(0,106,38,0.15);
    }
    .hero-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
    }
    @media (min-width: 1180px) {
      .hero-grid { grid-template-columns: minmax(0, 1fr) 400px; gap: 24px; }
    }

    /* Greenhouse visual mock — radial gradient + sensor pin overlay */
    .greenhouse-visual {
      position: relative;
      min-height: 260px;
      border-radius: 18px;
      background:
        radial-gradient(circle at 28% 32%, rgba(0,106,38,0.18) 0%, rgba(0,106,38,0) 38%),
        radial-gradient(circle at 72% 64%, rgba(0,101,113,0.16) 0%, rgba(0,101,113,0) 42%),
        linear-gradient(135deg, #eaf3ec 0%, #dfeff2 100%);
      overflow: hidden;
    }
    .greenhouse-visual::before {
      content: '';
      position: absolute; inset: 0;
      background-image:
        linear-gradient(rgba(44,47,49,0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(44,47,49,0.06) 1px, transparent 1px);
      background-size: 32px 32px;
      mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
    }
    .sensor-pin {
      position: absolute; display: inline-flex; align-items: center; justify-content: center;
      width: 14px; height: 14px;
    }
    .sensor-pin::before {
      content: ''; position: absolute; inset: 0; border-radius: 999px;
      background: #006a26; opacity: 0.55;
      animation: pulseRing 1.8s ease-out infinite;
    }
    .sensor-pin::after {
      content: ''; width: 8px; height: 8px; border-radius: 999px;
      background: #006a26; box-shadow: 0 0 0 3px #ffffff;
      position: relative; z-index: 1;
    }
    .sensor-pin .pin-label {
      position: absolute; top: 18px; left: 50%; transform: translateX(-50%);
      background: #ffffff; color: #2c2f31;
      padding: 4px 10px; border-radius: 999px;
      font-size: 10px; font-weight: 700; white-space: nowrap;
      box-shadow: 0 8px 20px -10px rgba(44,47,49,0.30);
    }
    @keyframes pulseRing {
      0% { transform: scale(0.9); opacity: 0.7; }
      80% { transform: scale(2.4); opacity: 0; }
      100% { transform: scale(2.4); opacity: 0; }
    }

    /* Schedule timeline rail */
    .timeline-item {
      position: relative; padding-left: 18px;
      border-left: 2px solid #eef1f3;
      padding-bottom: 14px;
    }
    .timeline-item:last-child { padding-bottom: 0; }
    .timeline-item.is-now { border-left-color: #006a26; }
    .timeline-item::before {
      content: ''; position: absolute; left: -7px; top: 0;
      width: 12px; height: 12px; border-radius: 999px;
      background: #ffffff; border: 3px solid #d0d5d8;
    }
    .timeline-item.is-now::before { border-color: #006a26; box-shadow: 0 0 0 4px rgba(0,106,38,0.18); }
  </style>

  <script>
    const VIEW_TITLES = {
      overview: ['대시보드', '전체 운영 현황 요약'],
      zones: ['구역 모니터링', '구역 시계열 · 최신 스냅샷'],
      decisions: ['결정 / 승인', 'LLM 결정 요청과 승인 흐름'],
      ai_chat: ['AI 어시스턴트', '파인튜닝된 AI와 대화하며 관리'],
      alerts: ['알림', 'validator · risk · policy 알림'],
      robot: ['로봇', 'Robot Tasks 및 Candidate'],
      devices: ['장치 / 제약', '장치 상태와 활성 제약'],
      policies: ['정책 / 이벤트', 'Policy live toggle과 이벤트 로그'],
      automation: ['환경설정', '사용자 임계값 기반 자동 제어 규칙 (센서 → 장치)'],
      shadow: ['Shadow Mode', 'real shadow window 요약'],
      system: ['시스템', 'execution history · runtime'],
    };
    function showView(name) {
      document.getElementById('viewTitle').textContent = (VIEW_TITLES[name] || VIEW_TITLES.overview)[0];
      document.getElementById('viewSub').textContent = (VIEW_TITLES[name] || VIEW_TITLES.overview)[1];
      document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === name));
      document.querySelectorAll('#sidebarNav a').forEach(a => a.classList.toggle('active', a.dataset.view === name));
      if (name === 'zones') refreshZoneHistory();
      if (name === 'ai_chat') { scrollChatToBottom(); renderGroundingInspector(); }
      if (name === 'automation') refreshAutomation();
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
      const ai = dashboardState.aiConfig || {};
      const championLabel = ai.llm_model_family
        ? ai.llm_model_family.replace(' (ds_v11 frozen)', '')
        : '—';
      const championTitle = ai.llm_model_label
        ? `${ai.llm_model_label} · prompt=${ai.llm_prompt_version || 'sft_v10'} · retriever=${ai.retriever_type || 'keyword'}`
        : '/ai/config 조회 중';
      const metrics = [
        ['Champion', championLabel, 'metric-champion', championTitle],
        ['결정 수', summary.decision_count ?? 0, '', ''],
        ['승인 대기', summary.approval_pending_count ?? 0, '', ''],
        ['Shadow 리뷰 대기', summary.shadow_review_pending_count ?? 0, '', ''],
        ['차단된 결정', summary.blocked_action_count ?? 0, '', ''],
        ['Safe Mode 추천', summary.safe_mode_count ?? 0, '', ''],
        ['Operator 불일치', summary.operator_disagreement_count ?? 0, '', ''],
        ['일치율', summary.operator_agreement_rate ?? 'n/a', '', ''],
        ['실행 명령', summary.command_count ?? 0, '', ''],
        ['Policy Event', summary.policy_event_count ?? 0, '', ''],
        ['Policy Block', summary.policy_blocked_count ?? 0, '', ''],
        ['Alerts', summary.alert_count ?? 0, '', ''],
        ['Robot Task', summary.robot_task_count ?? 0, '', ''],
        ['Robot Candidate', summary.robot_candidate_count ?? 0, '', ''],
        ['Policy (enabled/total)', ((summary.policy_count ?? 0) - (summary.policy_disabled_count ?? 0)) + '/' + (summary.policy_count ?? 0), '', ''],
      ];
      document.getElementById('metricGrid').innerHTML = metrics.map(([label, value, extra, title]) => `
        <div class="metric-card ${extra || ''}" ${title ? `title="${escapeHtml(title)}"` : ''}>
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
        const mode = (dashboardState.runtimeMode && dashboardState.runtimeMode.mode) || '—';
        const reason = (dashboardState.runtimeMode && dashboardState.runtimeMode.reason) || '—';
        runtime.innerHTML = `
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-muted">mode</span><span class="font-bold">${mode}</span></div>
            <div class="flex justify-between"><span class="text-muted">reason</span><span class="font-bold text-[11px] text-ink text-right truncate max-w-[60%]">${escapeHtml(reason)}</span></div>
            <div class="flex justify-between pt-2 border-t border-outline/20"><span class="text-muted">actor_id</span><span class="font-bold">${actor.actor_id}</span></div>
            <div class="flex justify-between"><span class="text-muted">role</span><span class="font-bold">${actor.role}</span></div>
            <div class="flex justify-between"><span class="text-muted">auth_mode</span><span class="font-bold">${actor.auth_mode}</span></div>
          </div>
        `;
      }
      const modeChip = document.getElementById('runtimeModeChip');
      if (modeChip) {
        const mode = (dashboardState.runtimeMode && dashboardState.runtimeMode.mode) || 'unknown';
        const cls = mode === 'execute' ? 'chip-critical' : (mode === 'approval' ? 'chip-warn' : 'chip-enabled');
        modeChip.className = `chip ${cls}`;
        modeChip.textContent = mode;
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
      const previousSelection = current || 'gh-01-zone-a';
      select.innerHTML = uniqueIds.map(id => `<option value="${id}">${id}</option>`).join('');
      if (uniqueIds.includes(previousSelection)) select.value = previousSelection;
    }

    // ===== uPlot realtime charts (Phase 4 native renderer) =====
    const TRACKED_METRICS = [
      'air_temp_c', 'rh_pct', 'vpd_kpa', 'substrate_moisture_pct', 'substrate_temp_c',
      'co2_ppm', 'par_umol_m2_s', 'feed_ec_ds_m', 'drain_ec_ds_m', 'feed_ph', 'drain_ph',
    ];
    const realtimeState = {
      zoneId: null,
      windowSeconds: 300,
      charts: new Map(),  // metric -> { plot, data: [xs, ys], lastValue, container }
      eventSource: null,
      reconnectTimer: null,
      reconnectAttempts: 0,
    };
    function nowMs() { return Date.now(); }
    function setStreamStatus(state, label) {
      const chip = document.getElementById('streamStatus');
      if (!chip) return;
      chip.classList.remove('chip-dark', 'chip-warn', 'chip-enabled', 'chip-critical');
      const map = { connected: 'chip-enabled', connecting: 'chip-warn', disconnected: 'chip-dark', error: 'chip-critical' };
      chip.classList.add(map[state] || 'chip-dark');
      chip.textContent = label || state;
    }
    function destroyRealtimeCharts() {
      for (const entry of realtimeState.charts.values()) {
        try { entry.plot.destroy(); } catch (_) {}
      }
      realtimeState.charts.clear();
      const container = document.getElementById('zoneHistoryCharts');
      if (container) container.innerHTML = '';
    }
    function ensureRealtimeChart(metric) {
      if (typeof uPlot === 'undefined') return null;
      if (realtimeState.charts.has(metric)) return realtimeState.charts.get(metric);
      const container = document.getElementById('zoneHistoryCharts');
      if (!container) return null;
      const wrapper = document.createElement('div');
      wrapper.className = 'bg-surface-low rounded-xl p-4';
      wrapper.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] uppercase tracking-wider text-muted font-bold">${metric}</span>
          <span class="text-lg font-bold text-primary" data-role="last">--</span>
        </div>
        <div data-role="plot" style="height:120px;"></div>
        <div class="text-[10px] text-muted mt-2" data-role="meta">stream 대기 중</div>
      `;
      container.appendChild(wrapper);
      const plotMount = wrapper.querySelector('[data-role="plot"]');
      const opts = {
        width: plotMount.clientWidth || 320,
        height: 120,
        scales: { x: { time: true } },
        legend: { show: false },
        cursor: { drag: { x: false, y: false }, points: { show: false } },
        axes: [
          { stroke: '#5b685e', grid: { stroke: 'rgba(193,200,192,0.3)' }, ticks: { show: false }, size: 28 },
          { stroke: '#5b685e', grid: { stroke: 'rgba(193,200,192,0.3)' }, size: 36 },
        ],
        series: [
          {},
          { stroke: '#2d5338', width: 2, fill: 'rgba(45,83,56,0.12)', points: { show: false } },
        ],
      };
      const plot = new uPlot(opts, [[], []], plotMount);
      const entry = { plot, xs: [], ys: [], wrapper, mount: plotMount };
      realtimeState.charts.set(metric, entry);
      window.addEventListener('resize', () => {
        try { plot.setSize({ width: plotMount.clientWidth || 320, height: 120 }); } catch (_) {}
      }, { passive: true });
      return entry;
    }
    function pushPoint(metric, ts, value) {
      const entry = ensureRealtimeChart(metric);
      if (!entry) return;
      entry.xs.push(ts);
      entry.ys.push(value);
      const cutoff = ts - realtimeState.windowSeconds;
      while (entry.xs.length && entry.xs[0] < cutoff) {
        entry.xs.shift();
        entry.ys.shift();
      }
      try {
        entry.plot.setData([entry.xs.slice(), entry.ys.slice()]);
      } catch (_) {}
      const last = entry.wrapper.querySelector('[data-role="last"]');
      if (last) last.textContent = typeof value === 'number' ? value.toFixed(2) : value;
      const meta = entry.wrapper.querySelector('[data-role="meta"]');
      if (meta && entry.ys.length) {
        const min = Math.min.apply(null, entry.ys);
        const max = Math.max.apply(null, entry.ys);
        meta.textContent = `MIN ${min.toFixed(2)} · MAX ${max.toFixed(2)} · points=${entry.ys.length}`;
      }
    }
    function ingestRecord(record) {
      if (!record || !record.metric_name) return;
      const value = record.value_double != null ? record.value_double : record.metric_value_double;
      if (typeof value !== 'number') return;
      const ts = record.measured_at ? Math.floor(new Date(record.measured_at).getTime() / 1000) : Math.floor(nowMs() / 1000);
      pushPoint(record.metric_name, ts, value);
    }
    async function bootstrapTimeseries(zoneId) {
      const windowSeconds = realtimeState.windowSeconds;
      const to = new Date();
      const from = new Date(to.getTime() - windowSeconds * 1000);
      const interval = windowSeconds <= 600 ? 'raw' : windowSeconds <= 21600 ? '1m' : '5m';
      try {
        const body = await apiFetch(
          '/zones/' + encodeURIComponent(zoneId) + '/timeseries?interval=' + interval +
          '&from=' + encodeURIComponent(from.toISOString().replace('Z', '')) +
          '&to=' + encodeURIComponent(to.toISOString().replace('Z', '')) + '&limit=2000'
        );
        const data = body.data || {};
        const series = data.series || {};
        for (const metric of TRACKED_METRICS) {
          const points = series[metric] || [];
          for (const point of points) {
            const ts = point.t ? Math.floor(new Date(point.t).getTime() / 1000) : null;
            const value = point.value != null ? point.value : point.avg;
            if (ts != null && typeof value === 'number') pushPoint(metric, ts, value);
          }
        }
      } catch (err) {
        const container = document.getElementById('zoneHistoryCharts');
        if (container && container.children.length === 0) {
          container.innerHTML = `<div class="placeholder col-span-full">bootstrap 실패: ${err.message}</div>`;
        }
      }
    }
    function closeStream() {
      if (realtimeState.eventSource) {
        try { realtimeState.eventSource.close(); } catch (_) {}
        realtimeState.eventSource = null;
      }
      if (realtimeState.reconnectTimer) {
        clearTimeout(realtimeState.reconnectTimer);
        realtimeState.reconnectTimer = null;
      }
    }
    function openStream(zoneId) {
      closeStream();
      setStreamStatus('connecting', 'connecting');
      const url = '/zones/' + encodeURIComponent(zoneId) + '/stream?bootstrap_seconds=' + Math.min(realtimeState.windowSeconds, 1800);
      let source;
      try { source = new EventSource(url); }
      catch (err) { setStreamStatus('error', 'error'); scheduleReconnect(zoneId); return; }
      realtimeState.eventSource = source;
      source.addEventListener('ready', () => {
        setStreamStatus('connected', 'live');
        realtimeState.reconnectAttempts = 0;
      });
      source.addEventListener('bootstrap', (evt) => {
        try { ingestRecord(JSON.parse(evt.data)); } catch (_) {}
      });
      source.addEventListener('reading', (evt) => {
        try { ingestRecord(JSON.parse(evt.data)); } catch (_) {}
      });
      source.addEventListener('bootstrap_complete', () => {
        setStreamStatus('connected', 'live');
      });
      source.onerror = () => {
        setStreamStatus('error', 'reconnecting');
        scheduleReconnect(zoneId);
      };
    }
    function scheduleReconnect(zoneId) {
      closeStream();
      realtimeState.reconnectAttempts += 1;
      const delay = Math.min(15000, 500 * Math.pow(2, realtimeState.reconnectAttempts));
      realtimeState.reconnectTimer = setTimeout(() => openStream(zoneId), delay);
    }
    async function refreshZoneHistory() {
      const select = document.getElementById('historyZoneId');
      const windowSelect = document.getElementById('historyWindow');
      if (!select) return;
      const zoneId = select.value || 'gh-01-zone-a';
      const windowSeconds = parseInt(windowSelect ? windowSelect.value : '300', 10) || 300;
      realtimeState.zoneId = zoneId;
      realtimeState.windowSeconds = windowSeconds;
      destroyRealtimeCharts();
      // Pre-create chart cards so the layout doesn't jump while bootstrap loads.
      for (const metric of TRACKED_METRICS) ensureRealtimeChart(metric);
      await bootstrapTimeseries(zoneId);
      openStream(zoneId);
    }

    // ===== AI Chat =====
    const chatState = { messages: [], sending: false, lastGrounding: null };
    const dashboardState = { runtimeMode: null, aiConfig: null };
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
          <div class="w-6 h-6 rounded-full bg-primary flex items-center justify-center shadow-glow-primary">
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
        host.innerHTML = `<div class="text-center text-muted text-xs py-6"><span class="chip chip-dark">오늘의 운용 로그 시작</span></div><div class="chat-bubble-ai mx-auto max-w-md">안녕하세요. iFarm 통합제어 AI 어시스턴트입니다. 현재 구역 상태, 정책, 결정을 질문하시면 파인튜닝된 모델이 답변합니다. 하단 빠른 질문 버튼도 활용해보세요.</div>`;
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
    async function loadAiConfig() {
      // Fetches the live LLM/retriever config so operators can always see
      // which fine-tune checkpoint is actually answering across three
      // surfaces: the AI 어시스턴트 card subtitle, the global header
      // champion chip, and the 시스템 > AI Runtime card body. Non-blocking —
      // if the call fails the UI falls back to placeholder copy but the
      // chat path still works.
      const meta = document.getElementById('aiAssistantMeta');
      const chip = document.getElementById('aiAssistantModelChip');
      const headerChip = document.getElementById('headerChampionChip');
      const runtimeBody = document.getElementById('aiRuntimeBody');
      try {
        const res = await apiFetch('/ai/config', { method: 'GET' });
        const d = res?.data || {};
        dashboardState.aiConfig = d;
        const provider = d.llm_provider || 'unknown';
        const family = d.llm_model_family || d.llm_model_id || 'unknown';
        const label = d.llm_model_label || d.llm_model_id || 'unknown';
        const prompt = d.llm_prompt_version || 'sft_v10';
        const retriever = d.retriever_type || 'keyword';
        const systemPrompt = d.chat_system_prompt_id || 'chat_v2';

        if (meta) meta.textContent = `${family} · ${prompt} · retriever=${retriever}`;
        if (chip) {
          chip.textContent = `champion: ${label}`;
          chip.classList.remove('hidden');
        }
        if (headerChip) {
          headerChip.textContent = `champion: ${family}`;
          headerChip.classList.remove('hidden');
          headerChip.title = `${label} · prompt=${prompt} · retriever=${retriever}`;
        }
        if (runtimeBody) {
          runtimeBody.innerHTML = `
            <div class="flex justify-between"><span class="text-muted">provider</span><span class="font-bold">${provider}</span></div>
            <div class="flex justify-between"><span class="text-muted">model_label</span><span class="font-bold text-[11px] truncate max-w-[60%]" title="${label}">${label}</span></div>
            <div class="flex justify-between"><span class="text-muted">model_family</span><span class="font-bold text-[11px] truncate max-w-[60%]">${family}</span></div>
            <div class="flex justify-between"><span class="text-muted">prompt_version</span><span class="font-bold">${prompt}</span></div>
            <div class="flex justify-between"><span class="text-muted">retriever</span><span class="font-bold">${retriever}</span></div>
            <div class="flex justify-between"><span class="text-muted">chat_system_prompt</span><span class="font-bold">${systemPrompt}</span></div>
          `;
        }
      } catch (err) {
        if (meta) meta.textContent = '파인튜닝 모델 구성 조회 실패 — /ai/chat은 그래도 동작합니다.';
        if (runtimeBody) runtimeBody.innerHTML = '<div class="placeholder">/ai/config 조회 실패</div>';
      }
    }
    function renderGroundingInspector() {
      // Surfaces the model_id / provider / zone_hint / grounding_keys from
      // the most recent /ai/chat response so operators can audit what the
      // chat assistant actually grounded on. Non-destructive — when no
      // chat has happened yet it shows the /ai/config champion defaults.
      const labelEl = document.getElementById('groundingModelLabel');
      const provEl  = document.getElementById('groundingProvider');
      const zoneEl  = document.getElementById('groundingZoneHint');
      const keysEl  = document.getElementById('groundingKeys');
      const atmpEl  = document.getElementById('groundingAttempts');
      if (!labelEl) return;
      const g = chatState.lastGrounding;
      if (!g) {
        const ai = dashboardState.aiConfig || {};
        labelEl.textContent = ai.llm_model_label || '대기 중';
        provEl.textContent = ai.llm_provider || '—';
        zoneEl.textContent = '—';
        keysEl.textContent = '아직 대화 없음';
        atmpEl.textContent = '—';
        return;
      }
      const tail = (g.model_id || '').startsWith('ft:')
        ? g.model_id.slice(g.model_id.lastIndexOf(':') + 1)
        : (g.model_id || '—');
      labelEl.textContent = tail;
      labelEl.title = g.model_id || '';
      provEl.textContent = g.provider || '—';
      zoneEl.textContent = g.zone_hint || '—';
      keysEl.textContent = (g.grounding_keys && g.grounding_keys.length)
        ? g.grounding_keys.join(', ')
        : '—';
      atmpEl.textContent = (g.attempts != null) ? String(g.attempts) : '—';
    }
    // ---- Automation rules UI ----
    const automationState = { rules: [], triggers: [], editingRuleId: null };
    async function refreshAutomation() {
      try {
        const [rulesRes, triggersRes] = await Promise.all([
          apiFetch('/automation/rules'),
          apiFetch('/automation/triggers?limit=25'),
        ]);
        automationState.rules = rulesRes?.data?.rules || [];
        automationState.triggers = triggersRes?.data?.triggers || [];
        renderAutomationRules();
        renderAutomationTriggers();
        const chip = document.getElementById('automationRuntimeChip');
        if (chip) {
          const mode = (dashboardState.runtimeMode && dashboardState.runtimeMode.mode) || 'unknown';
          const cls = mode === 'execute' ? 'chip-critical' : (mode === 'approval' ? 'chip-warn' : 'chip-enabled');
          chip.className = `chip ${cls}`;
          chip.textContent = `runtime: ${mode}`;
        }
      } catch (err) {
        console.error('refreshAutomation failed', err);
        const host = document.getElementById('automationRuleList');
        if (host) host.innerHTML = `<div class="placeholder">자동화 규칙 로드 실패: ${escapeHtml(err.message || '')}</div>`;
      }
    }
    function thresholdLabel(rule) {
      const op = rule.operator;
      if (op === 'between') {
        return `${rule.threshold_min ?? '?'} ~ ${rule.threshold_max ?? '?'}`;
      }
      const opMap = { gt: '>', gte: '≥', lt: '<', lte: '≤', eq: '=' };
      return `${opMap[op] || op} ${rule.threshold_value ?? '?'}`;
    }
    function gateChipClass(gate) {
      if (gate === 'execute') return 'chip-critical';
      if (gate === 'approval') return 'chip-warn';
      return 'chip-enabled';
    }
    function renderAutomationRules() {
      const host = document.getElementById('automationRuleList');
      if (!host) return;
      if (!automationState.rules.length) {
        host.innerHTML = '<div class="placeholder">등록된 자동화 규칙이 없습니다. <button onclick="openAutomationRuleModal()" class="text-primary underline ml-1">규칙 추가</button></div>';
        return;
      }
      host.innerHTML = automationState.rules.map(rule => `
        <div class="alert-row">
          <div class="flex items-start justify-between mb-2 gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="text-sm font-bold text-ink">${escapeHtml(rule.name)}</span>
                <span class="chip ${rule.enabled ? 'chip-enabled' : 'chip-warn'}">${rule.enabled ? 'ENABLED' : 'DISABLED'}</span>
                <span class="chip ${gateChipClass(rule.runtime_mode_gate)}">gate: ${rule.runtime_mode_gate}</span>
                <span class="chip chip-dark">prio ${rule.priority}</span>
              </div>
              <div class="text-[10px] text-muted uppercase tracking-wider">${escapeHtml(rule.rule_id)}</div>
            </div>
            <div class="flex items-center gap-1">
              <button onclick="toggleAutomationRule('${escapeHtml(rule.rule_id)}', ${rule.enabled ? 'false' : 'true'})" class="text-[11px] font-semibold ${rule.enabled ? 'text-warn' : 'text-primary'} hover:underline">${rule.enabled ? '비활성화' : '활성화'}</button>
              <button onclick="openAutomationRuleModal('${escapeHtml(rule.rule_id)}')" class="text-[11px] text-primary hover:underline">편집</button>
              <button onclick="deleteAutomationRule('${escapeHtml(rule.rule_id)}')" class="text-[11px] text-critical hover:underline">삭제</button>
            </div>
          </div>
          <div class="text-xs text-ink mb-1">
            IF <b>${escapeHtml(rule.sensor_key)}</b> ${thresholdLabel(rule)}
            THEN <b>${escapeHtml(rule.target_action)}</b> @ <b>${escapeHtml(rule.target_device_type)}</b>${rule.target_device_id ? ' (' + escapeHtml(rule.target_device_id) + ')' : ''}
          </div>
          ${rule.description ? `<div class="text-[11px] text-muted leading-relaxed">${escapeHtml(rule.description)}</div>` : ''}
          <div class="text-[10px] text-muted mt-1">
            zone=${escapeHtml(rule.zone_id || '전 구역')} · cooldown=${rule.cooldown_minutes}분 · owner=${escapeHtml(rule.owner_role)}
          </div>
        </div>
      `).join('');
    }
    function renderAutomationTriggers() {
      const host = document.getElementById('automationTriggerList');
      if (!host) return;
      if (!automationState.triggers.length) {
        host.innerHTML = '<div class="placeholder">trigger 로그가 없습니다.</div>';
        return;
      }
      const statusChip = (st) => {
        if (st === 'dispatched') return 'chip-enabled';
        if (st === 'approval_pending') return 'chip-warn';
        if (st === 'blocked_validator' || st === 'blocked_guard') return 'chip-critical';
        return 'chip-dark';
      };
      host.innerHTML = automationState.triggers.map(t => `
        <div class="alert-row">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] text-muted">#${t.id} · ${escapeHtml(t.triggered_at || '')}</span>
            <span class="chip ${statusChip(t.status)}">${t.status}</span>
          </div>
          <div class="text-xs text-ink">rule_id=${t.rule_id} · sensor=${escapeHtml(t.sensor_key)} = ${t.matched_value}</div>
          <div class="text-[10px] text-muted">runtime=${escapeHtml(t.runtime_mode || '')}${t.note ? ' · ' + escapeHtml(t.note) : ''}</div>
        </div>
      `).join('');
    }
    function openAutomationRuleModal(ruleId = null) {
      automationState.editingRuleId = ruleId;
      const modal = document.getElementById('automationRuleModal');
      if (!modal) return;
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      const title = document.getElementById('automationModalTitle');
      if (title) title.textContent = ruleId ? `규칙 편집: ${ruleId}` : '새 자동화 규칙';
      const form = document.getElementById('automationRuleForm');
      if (form) form.reset();
      const errEl = document.getElementById('automationRuleFormError');
      if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
      document.getElementById('ruleField_priority').value = 100;
      document.getElementById('ruleField_cooldown_minutes').value = 15;
      document.getElementById('ruleField_enabled').checked = true;
      document.getElementById('ruleField_runtime_mode_gate').value = 'approval';
      toggleBetweenRow();
      if (ruleId) {
        const rule = automationState.rules.find(r => r.rule_id === ruleId);
        if (rule) {
          document.getElementById('ruleField_rule_id').value = rule.rule_id;
          document.getElementById('ruleField_rule_id').readOnly = true;
          document.getElementById('ruleField_name').value = rule.name;
          document.getElementById('ruleField_description').value = rule.description || '';
          document.getElementById('ruleField_zone_id').value = rule.zone_id || '';
          document.getElementById('ruleField_priority').value = rule.priority;
          document.getElementById('ruleField_cooldown_minutes').value = rule.cooldown_minutes;
          document.getElementById('ruleField_sensor_key').value = rule.sensor_key;
          document.getElementById('ruleField_operator').value = rule.operator;
          document.getElementById('ruleField_threshold_value').value = rule.threshold_value ?? '';
          document.getElementById('ruleField_threshold_min').value = rule.threshold_min ?? '';
          document.getElementById('ruleField_threshold_max').value = rule.threshold_max ?? '';
          document.getElementById('ruleField_target_device_type').value = rule.target_device_type;
          document.getElementById('ruleField_target_device_id').value = rule.target_device_id || '';
          document.getElementById('ruleField_target_action').value = rule.target_action;
          document.getElementById('ruleField_action_payload').value = rule.action_payload
            ? JSON.stringify(rule.action_payload) : '';
          document.getElementById('ruleField_runtime_mode_gate').value = rule.runtime_mode_gate;
          document.getElementById('ruleField_enabled').checked = !!rule.enabled;
          toggleBetweenRow();
        }
      } else {
        document.getElementById('ruleField_rule_id').readOnly = false;
      }
    }
    function closeAutomationRuleModal() {
      const modal = document.getElementById('automationRuleModal');
      if (!modal) return;
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      automationState.editingRuleId = null;
    }
    function toggleBetweenRow() {
      const op = document.getElementById('ruleField_operator').value;
      const row = document.getElementById('ruleFieldBetweenRow');
      if (!row) return;
      row.style.display = (op === 'between') ? '' : 'none';
    }
    async function toggleAutomationRule(ruleId, enable) {
      try {
        await apiFetch(`/automation/rules/${encodeURIComponent(ruleId)}/toggle`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: enable }),
        });
        refreshAutomation();
      } catch (err) {
        alert('toggle 실패: ' + err.message);
      }
    }
    async function deleteAutomationRule(ruleId) {
      if (!confirm(`자동화 규칙 '${ruleId}'을 삭제하시겠습니까?`)) return;
      try {
        await apiFetch(`/automation/rules/${encodeURIComponent(ruleId)}`, { method: 'DELETE' });
        refreshAutomation();
      } catch (err) {
        alert('삭제 실패: ' + err.message);
      }
    }
    async function submitAutomationRuleForm(event) {
      event.preventDefault();
      const errEl = document.getElementById('automationRuleFormError');
      errEl.classList.add('hidden');
      errEl.textContent = '';
      const getNum = (id) => {
        const v = document.getElementById(id).value;
        return v === '' ? null : Number(v);
      };
      let actionPayload = {};
      const apRaw = document.getElementById('ruleField_action_payload').value.trim();
      if (apRaw) {
        try {
          actionPayload = JSON.parse(apRaw);
        } catch (err) {
          errEl.textContent = 'action_payload JSON 파싱 실패: ' + err.message;
          errEl.classList.remove('hidden');
          return;
        }
      }
      const body = {
        rule_id: document.getElementById('ruleField_rule_id').value.trim(),
        name: document.getElementById('ruleField_name').value.trim(),
        description: document.getElementById('ruleField_description').value,
        zone_id: document.getElementById('ruleField_zone_id').value.trim() || null,
        priority: parseInt(document.getElementById('ruleField_priority').value || 100),
        cooldown_minutes: parseInt(document.getElementById('ruleField_cooldown_minutes').value || 15),
        sensor_key: document.getElementById('ruleField_sensor_key').value,
        operator: document.getElementById('ruleField_operator').value,
        threshold_value: getNum('ruleField_threshold_value'),
        threshold_min: getNum('ruleField_threshold_min'),
        threshold_max: getNum('ruleField_threshold_max'),
        target_device_type: document.getElementById('ruleField_target_device_type').value,
        target_device_id: document.getElementById('ruleField_target_device_id').value.trim() || null,
        target_action: document.getElementById('ruleField_target_action').value.trim(),
        action_payload: actionPayload,
        runtime_mode_gate: document.getElementById('ruleField_runtime_mode_gate').value,
        enabled: document.getElementById('ruleField_enabled').checked,
        owner_role: 'operator',
      };
      try {
        const editing = automationState.editingRuleId;
        if (editing) {
          const { rule_id, owner_role, sensor_key, ...updatable } = body;
          await apiFetch(`/automation/rules/${encodeURIComponent(editing)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatable),
          });
        } else {
          await apiFetch('/automation/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          });
        }
        closeAutomationRuleModal();
        refreshAutomation();
      } catch (err) {
        errEl.textContent = '저장 실패: ' + err.message;
        errEl.classList.remove('hidden');
      }
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
        // Update grounding inspector so operator can see what the model saw
        chatState.lastGrounding = {
          model_id: res?.data?.model_id,
          provider: res?.data?.provider,
          zone_hint: res?.data?.zone_hint,
          grounding_keys: res?.data?.grounding_keys,
          attempts: res?.data?.attempts,
        };
        renderGroundingInspector();
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
        dashboardState.runtimeMode = data.runtime_mode;
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
      const zoneSelect = document.getElementById('historyZoneId');
      if (zoneSelect) {
        zoneSelect.addEventListener('change', () => refreshZoneHistory());
      }
      const windowSelect = document.getElementById('historyWindow');
      if (windowSelect) {
        windowSelect.addEventListener('change', () => refreshZoneHistory());
      }
    }
    setupNav();
    showView('overview');
    renderChat();
    loadAiConfig().then(() => { renderGroundingInspector(); });
    const automationForm = document.getElementById('automationRuleForm');
    if (automationForm) automationForm.addEventListener('submit', submitAutomationRuleForm);
    const operatorSelect = document.getElementById('ruleField_operator');
    if (operatorSelect) operatorSelect.addEventListener('change', toggleBetweenRow);
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
  </script>
</body>
</html>"""
