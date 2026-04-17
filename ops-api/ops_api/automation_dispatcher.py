"""Dispatch approved automation triggers (Phase Q).

Phase P-3 only moves an ``approval_pending`` trigger to ``approved`` —
the actual device command is still unsent. Phase Q closes the loop: for
each ``status=approved`` row, synthesize a :class:`DecisionRecord`,
link it back to the trigger via ``AutomationRuleTriggerRecord.decision_id``
and hand a :class:`DeviceCommandRequest` to the same
``ExecutionDispatcher`` used by LLM decisions.

Using a synthetic DecisionRecord keeps the DeviceCommandRecord FK
schema unchanged (``decision_id`` stays non-nullable). The synthetic
row is tagged ``task_type='automation_rule'`` and ``model_id='automation_runner'``
so analytics can filter it out of LLM evaluation dashboards.

Called once per ``AutomationRunner`` tick after ``evaluate_rules``, so
the cadence matches the polling tick interval. The function is also
side-effect-safe to call directly from tests / smoke scripts.
"""

from __future__ import annotations

import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    DecisionRecord,
    DeviceCommandRecord,
    utc_now,
)


if TYPE_CHECKING:  # pragma: no cover
    from execution_gateway.dispatch import ExecutionDispatcher


logger = logging.getLogger(__name__)


@dataclass
class DispatchSummary:
    trigger_id: int
    rule_id: int
    status: str
    decision_id: int | None
    reasons: list[str]


def dispatch_approved_triggers(
    session: Session,
    dispatcher: "ExecutionDispatcher",
    *,
    limit: int = 50,
    now: datetime | None = None,
) -> list[DispatchSummary]:
    """Flush every ``status='approved'`` trigger through the dispatcher.

    Each approved row is claimed one-by-one; failures are isolated so a
    malformed rule or adapter fault doesn't stall the rest of the batch.
    Returns a per-trigger summary list so callers can log / expose it.
    """

    from execution_gateway.contracts import DeviceCommandRequest  # local to avoid heavy import at startup

    approved = session.scalars(
        select(AutomationRuleTriggerRecord)
        .where(AutomationRuleTriggerRecord.status == "approved")
        .order_by(AutomationRuleTriggerRecord.reviewed_at.asc().nullslast())
        .limit(limit)
    ).all()
    summaries: list[DispatchSummary] = []
    for trigger in approved:
        rule = session.get(AutomationRuleRecord, trigger.rule_id)
        if rule is None:
            trigger.status = "dispatch_fault"
            trigger.note = "rule row missing at dispatch time"
            session.commit()
            summaries.append(
                DispatchSummary(
                    trigger_id=trigger.id,
                    rule_id=trigger.rule_id,
                    status="dispatch_fault",
                    decision_id=None,
                    reasons=["rule_missing"],
                )
            )
            continue

        summary = _dispatch_single(
            session=session,
            trigger=trigger,
            rule=rule,
            dispatcher=dispatcher,
            now=now or utc_now(),
        )
        summaries.append(summary)
    return summaries


def _dispatch_single(
    *,
    session: Session,
    trigger: AutomationRuleTriggerRecord,
    rule: AutomationRuleRecord,
    dispatcher: "ExecutionDispatcher",
    now: datetime,
) -> DispatchSummary:
    from execution_gateway.contracts import DeviceCommandRequest

    try:
        proposed = json.loads(trigger.proposed_action_json or "{}")
    except json.JSONDecodeError:
        proposed = {}

    device_id = rule.target_device_id or _fallback_device_id(rule, trigger)
    request_id = f"automation-{trigger.id}-{secrets.token_hex(4)}"
    zone_id = trigger.zone_id or rule.zone_id or "farm-wide"
    action_type = str(proposed.get("action_type") or rule.target_action)
    parameters = proposed.get("payload") if isinstance(proposed.get("payload"), dict) else {}

    command_payload: dict[str, Any] = {
        "request_id": request_id,
        "device_id": device_id,
        "action_type": action_type,
        "parameters": parameters,
        "approval_required": bool(proposed.get("approval_required", True)),
        "approval_context": {
            "approval_status": "approved",
            "approver_id": trigger.reviewed_by or "operator",
            "approved_at": (trigger.reviewed_at or now).isoformat(),
        },
        "policy_snapshot": {
            "policy_result": "pass",
            "policy_ids": ["automation_rule"],
        },
        "operator_context": {
            "operator_present": False,
            "manual_override": False,
        },
        "sensor_quality": {"overall": "good"},
    }

    decision = DecisionRecord(
        request_id=request_id,
        zone_id=zone_id,
        task_type="automation_rule",
        runtime_mode=trigger.runtime_mode or "approval",
        status="approved_executed",
        model_id="automation_runner",
        prompt_version="automation_runner_v1",
        raw_output_json="{}",
        parsed_output_json=json.dumps({"recommended_actions": [proposed]}, ensure_ascii=False),
        validated_output_json=json.dumps({"recommended_actions": [proposed]}, ensure_ascii=False),
        zone_state_json="{}",
        citations_json="[]",
        retrieval_context_json="{}",
        audit_path="",
        validator_reason_codes_json="[]",
    )
    session.add(decision)
    session.flush()
    trigger.decision_id = decision.id

    try:
        request = DeviceCommandRequest.from_dict(command_payload)
        dispatch_result = dispatcher.dispatch_device_command(request)
    except Exception as exc:  # defensive — adapter bugs shouldn't poison the batch
        logger.exception("automation dispatch failed trigger_id=%s", trigger.id)
        trigger.status = "dispatch_fault"
        trigger.note = f"dispatcher_error: {exc}"[:500]
        session.commit()
        return DispatchSummary(
            trigger_id=trigger.id,
            rule_id=trigger.rule_id,
            status="dispatch_fault",
            decision_id=decision.id,
            reasons=["dispatcher_error"],
        )

    result_dict = dispatch_result.as_dict()
    session.add(
        DeviceCommandRecord(
            decision_id=decision.id,
            command_kind="device_command",
            target_id=device_id,
            action_type=action_type,
            status=str(result_dict.get("status") or "logged_only"),
            payload_json=json.dumps(command_payload, ensure_ascii=False),
            adapter_result_json=json.dumps(result_dict, ensure_ascii=False),
        )
    )

    allow_dispatch = bool(result_dict.get("allow_dispatch"))
    reasons = list(result_dict.get("reasons") or [])
    dispatch_status = str(result_dict.get("status") or "")

    if not allow_dispatch:
        trigger.status = "blocked_guard"
    elif dispatch_status == "acknowledged":
        trigger.status = "dispatched"
    else:
        trigger.status = "dispatch_fault"

    trigger.note = ",".join(reasons)[:500]
    session.commit()
    return DispatchSummary(
        trigger_id=trigger.id,
        rule_id=trigger.rule_id,
        status=trigger.status,
        decision_id=decision.id,
        reasons=reasons,
    )


def _fallback_device_id(
    rule: AutomationRuleRecord, trigger: AutomationRuleTriggerRecord
) -> str:
    """Synthesize a deterministic device_id when the rule omits one.

    Automation rules may target an entire device type per zone without
    pinning a specific device. The dispatcher requires a concrete
    device_id for its catalog lookup, so we fall back to
    ``{zone_id}/{device_type}`` which adapters can route on. Real
    deployments should set ``target_device_id`` explicitly; this path
    exists so zone-wide rules still flow rather than erroring out.
    """

    zone = trigger.zone_id or rule.zone_id or "farm-wide"
    return f"{zone}/{rule.target_device_type}"
