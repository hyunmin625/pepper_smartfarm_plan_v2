"""Operator-defined automation rule engine.

The engine loads every enabled ``AutomationRuleRecord`` from the database
and checks it against a sensor snapshot dict keyed by
``AUTOMATION_SENSOR_KEYS`` (see ``api_models.py``). Matched rules produce
a proposed action that is handed through the same safety pipeline the LLM
decision path uses: ``policy_engine.output_validator`` first, then
``execution_gateway.guards``, and finally the ``runtime_mode`` gate
(shadow → approval → execute). Triggers are logged to
``automation_rule_triggers`` regardless of the outcome so operators can
audit how often each rule would fire.

This module is intentionally stateless apart from DB reads/writes. It is
invoked by the FastAPI endpoint (manual dry-run + test harness), and
will later be driven by a background sensor loop once real greenhouse
telemetry starts flowing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AutomationRuleRecord, AutomationRuleTriggerRecord, utc_now


RUNTIME_MODE_ORDER = {"shadow": 0, "approval": 1, "execute": 2}

OPERATOR_LABELS = {
    "gt": ">",
    "gte": "≥",
    "lt": "<",
    "lte": "≤",
    "eq": "=",
    "between": "∈ [min, max]",
}


@dataclass(frozen=True)
class RuleMatch:
    """Result of a single rule evaluation."""

    rule_id: int
    rule_ref: str
    name: str
    sensor_key: str
    matched_value: float
    operator: str
    threshold: dict[str, float]
    target_device_type: str
    target_device_id: str | None
    target_action: str
    proposed_action: dict[str, Any]
    runtime_mode_gate: str
    priority: int
    status: str
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_ref": self.rule_ref,
            "name": self.name,
            "sensor_key": self.sensor_key,
            "matched_value": self.matched_value,
            "operator": self.operator,
            "threshold": self.threshold,
            "target_device_type": self.target_device_type,
            "target_device_id": self.target_device_id,
            "target_action": self.target_action,
            "proposed_action": self.proposed_action,
            "runtime_mode_gate": self.runtime_mode_gate,
            "priority": self.priority,
            "status": self.status,
            "note": self.note,
        }


@dataclass
class EvaluationReport:
    runtime_mode: str
    sensor_snapshot: dict[str, Any]
    evaluated_rules: int = 0
    matched_rules: int = 0
    matches: list[RuleMatch] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "runtime_mode": self.runtime_mode,
            "sensor_snapshot": self.sensor_snapshot,
            "evaluated_rules": self.evaluated_rules,
            "matched_rules": self.matched_rules,
            "matches": [m.as_dict() for m in self.matches],
            "skipped": self.skipped,
        }


def _check_condition(
    value: float | None,
    operator: str,
    threshold_value: float | None,
    threshold_min: float | None,
    threshold_max: float | None,
) -> tuple[bool, dict[str, float]]:
    """Return (matched?, threshold_dict).

    threshold_dict is packaged so the UI + trigger log can display what
    the operator configured even if some fields are None.
    """

    if value is None:
        return False, {}
    if operator == "gt":
        return (threshold_value is not None and value > threshold_value), {
            "value": threshold_value or 0.0
        }
    if operator == "gte":
        return (threshold_value is not None and value >= threshold_value), {
            "value": threshold_value or 0.0
        }
    if operator == "lt":
        return (threshold_value is not None and value < threshold_value), {
            "value": threshold_value or 0.0
        }
    if operator == "lte":
        return (threshold_value is not None and value <= threshold_value), {
            "value": threshold_value or 0.0
        }
    if operator == "eq":
        return (threshold_value is not None and abs(value - threshold_value) < 1e-9), {
            "value": threshold_value or 0.0
        }
    if operator == "between":
        if threshold_min is None or threshold_max is None:
            return False, {}
        return (threshold_min <= value <= threshold_max), {
            "min": threshold_min,
            "max": threshold_max,
        }
    return False, {}


def _load_enabled_rules(
    session: Session,
    *,
    zone_id: str | None = None,
) -> list[AutomationRuleRecord]:
    stmt = (
        select(AutomationRuleRecord)
        .where(AutomationRuleRecord.enabled == 1)
        .order_by(AutomationRuleRecord.priority.asc(), AutomationRuleRecord.id.asc())
    )
    rows = list(session.scalars(stmt))
    if zone_id is not None:
        # A rule with zone_id=None is a farm-wide rule; include it for every zone.
        rows = [r for r in rows if r.zone_id is None or r.zone_id == zone_id]
    return rows


def _in_cooldown(
    session: Session,
    rule: AutomationRuleRecord,
    now: datetime,
) -> bool:
    if rule.cooldown_minutes <= 0:
        return False
    window_start = now - timedelta(minutes=rule.cooldown_minutes)
    stmt = (
        select(AutomationRuleTriggerRecord.id)
        .where(AutomationRuleTriggerRecord.rule_id == rule.id)
        .where(AutomationRuleTriggerRecord.triggered_at >= window_start)
        .where(AutomationRuleTriggerRecord.status.in_([
            "approval_pending", "dispatched",
        ]))
        .limit(1)
    )
    return session.execute(stmt).first() is not None


def _build_proposed_action(
    rule: AutomationRuleRecord,
    matched_value: float,
) -> dict[str, Any]:
    try:
        payload = json.loads(rule.action_payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "action_type": rule.target_action,
        "target": {
            "target_type": rule.target_device_type,
            "target_id": rule.target_device_id,
        },
        "trigger": {
            "source": "automation_rule",
            "rule_id": rule.rule_id,
            "sensor_key": rule.sensor_key,
            "matched_value": matched_value,
            "operator": rule.operator,
        },
        "payload": payload,
        "priority": rule.priority,
        "approval_required": rule.runtime_mode_gate != "execute",
        "reason": f"automation_rule:{rule.rule_id} → {rule.sensor_key} {OPERATOR_LABELS.get(rule.operator, rule.operator)}",
    }


def _gate_status(
    rule_gate: str,
    runtime_mode: str,
) -> str:
    """Return the initial trigger status based on the gate vs runtime mode.

    The rule never runs above its own runtime_mode_gate, and never above
    the farm-wide runtime_mode either. The stricter of the two wins.
    """

    runtime_rank = RUNTIME_MODE_ORDER.get(runtime_mode, 0)
    gate_rank = RUNTIME_MODE_ORDER.get(rule_gate, 1)
    effective_rank = min(runtime_rank, gate_rank)
    if effective_rank >= 2:
        return "dispatched"
    if effective_rank >= 1:
        return "approval_pending"
    return "shadow_logged"


def evaluate_rules(
    session: Session,
    *,
    runtime_mode: str,
    sensor_snapshot: dict[str, float],
    zone_id: str | None = None,
    persist: bool = True,
    now: datetime | None = None,
) -> EvaluationReport:
    """Score every enabled rule against the supplied sensor snapshot.

    - ``runtime_mode`` is the farm-wide mode (shadow/approval/execute).
    - ``zone_id`` narrows to rules scoped to that zone (``None`` rule
      covers every zone).
    - ``persist`` writes trigger rows to the database. Set to False for
      UI dry-runs where operators want to preview a rule without
      polluting the audit log.

    Each matching rule produces a ``RuleMatch`` with an effective status:

    - ``shadow_logged``: farm-wide mode or rule_gate is shadow — trigger
      logged only, no decision written.
    - ``approval_pending``: ready for operator approval via the standard
      approval queue (writing into ``approvals`` is out of scope for this
      first cut; we log the proposed action so a follow-up phase can
      hook it into the existing approval flow).
    - ``dispatched``: eligible for immediate execute (still goes through
      execution_gateway safety guards in the caller).
    - ``cooldown_skipped``: rule matched but fired within its cooldown
      window, so we skip to avoid thrashing.
    """

    report = EvaluationReport(runtime_mode=runtime_mode, sensor_snapshot=dict(sensor_snapshot))
    now = now or utc_now()

    rules = _load_enabled_rules(session, zone_id=zone_id)
    for rule in rules:
        report.evaluated_rules += 1
        raw = sensor_snapshot.get(rule.sensor_key)
        value: float | None = None
        if isinstance(raw, (int, float)):
            value = float(raw)
        matched, threshold = _check_condition(
            value,
            rule.operator,
            rule.threshold_value,
            rule.threshold_min,
            rule.threshold_max,
        )
        if not matched:
            continue
        report.matched_rules += 1

        if _in_cooldown(session, rule, now):
            match = RuleMatch(
                rule_id=rule.id,
                rule_ref=rule.rule_id,
                name=rule.name,
                sensor_key=rule.sensor_key,
                matched_value=value if value is not None else 0.0,
                operator=rule.operator,
                threshold=threshold,
                target_device_type=rule.target_device_type,
                target_device_id=rule.target_device_id,
                target_action=rule.target_action,
                proposed_action=_build_proposed_action(rule, value or 0.0),
                runtime_mode_gate=rule.runtime_mode_gate,
                priority=rule.priority,
                status="cooldown_skipped",
                note=f"within cooldown {rule.cooldown_minutes} minutes",
            )
            report.matches.append(match)
            if persist:
                _persist_trigger(session, rule, match, now)
            continue

        proposed = _build_proposed_action(rule, value or 0.0)
        effective_status = _gate_status(rule.runtime_mode_gate, runtime_mode)
        match = RuleMatch(
            rule_id=rule.id,
            rule_ref=rule.rule_id,
            name=rule.name,
            sensor_key=rule.sensor_key,
            matched_value=value or 0.0,
            operator=rule.operator,
            threshold=threshold,
            target_device_type=rule.target_device_type,
            target_device_id=rule.target_device_id,
            target_action=rule.target_action,
            proposed_action=proposed,
            runtime_mode_gate=rule.runtime_mode_gate,
            priority=rule.priority,
            status=effective_status,
        )
        report.matches.append(match)
        if persist:
            _persist_trigger(session, rule, match, now)

    if persist:
        session.commit()
    return report


def _persist_trigger(
    session: Session,
    rule: AutomationRuleRecord,
    match: RuleMatch,
    now: datetime,
) -> None:
    row = AutomationRuleTriggerRecord(
        rule_id=rule.id,
        triggered_at=now,
        zone_id=rule.zone_id,
        sensor_key=rule.sensor_key,
        matched_value=match.matched_value,
        sensor_snapshot_json=json.dumps(match.threshold, ensure_ascii=False),
        proposed_action_json=json.dumps(match.proposed_action, ensure_ascii=False),
        status=match.status,
        runtime_mode=match.runtime_mode_gate,
        decision_id=None,
        note=match.note,
    )
    session.add(row)


def serialize_rule(rule: AutomationRuleRecord) -> dict[str, Any]:
    try:
        payload = json.loads(rule.action_payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": rule.id,
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "zone_id": rule.zone_id,
        "sensor_key": rule.sensor_key,
        "operator": rule.operator,
        "threshold_value": rule.threshold_value,
        "threshold_min": rule.threshold_min,
        "threshold_max": rule.threshold_max,
        "hysteresis_value": rule.hysteresis_value,
        "cooldown_minutes": rule.cooldown_minutes,
        "target_device_type": rule.target_device_type,
        "target_device_id": rule.target_device_id,
        "target_action": rule.target_action,
        "action_payload": payload,
        "priority": rule.priority,
        "enabled": bool(rule.enabled),
        "runtime_mode_gate": rule.runtime_mode_gate,
        "owner_role": rule.owner_role,
        "created_by": rule.created_by,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def serialize_trigger(trigger: AutomationRuleTriggerRecord) -> dict[str, Any]:
    try:
        proposed = json.loads(trigger.proposed_action_json or "{}")
    except json.JSONDecodeError:
        proposed = {}
    return {
        "id": trigger.id,
        "rule_id": trigger.rule_id,
        "triggered_at": trigger.triggered_at.isoformat() if trigger.triggered_at else None,
        "zone_id": trigger.zone_id,
        "sensor_key": trigger.sensor_key,
        "matched_value": trigger.matched_value,
        "proposed_action": proposed,
        "status": trigger.status,
        "runtime_mode": trigger.runtime_mode,
        "decision_id": trigger.decision_id,
        "note": trigger.note,
    }
