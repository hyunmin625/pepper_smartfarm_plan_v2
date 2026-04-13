from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import PolicyRecord


def _loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def policy_row_to_rule(row: PolicyRecord) -> dict[str, Any]:
    """Serialize a PolicyRecord to the rule dict shape consumed by precheck.

    The shape mirrors ``data/examples/policy_output_validator_rules_seed.json``
    so precheck and output_validator logic does not need to know which
    source loaded the rules.
    """
    return {
        "rule_id": row.policy_id,
        "stage": row.policy_stage,
        "severity": row.severity,
        "enabled": bool(row.enabled),
        "description": row.description,
        "trigger_flags": _loads(row.trigger_flags_json, []),
        "enforcement": _loads(row.enforcement_json, {}),
        "source_version": row.source_version,
    }


class DbPolicySource:
    """Live, DB-backed PolicySource used by ops-api at runtime.

    Each call opens a short-lived Session so operator edits made through
    the PATCH /policies/{id} endpoint are reflected on the very next
    precheck evaluation.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_enabled_rules(self, stages: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        stmt = (
            select(PolicyRecord)
            .where(PolicyRecord.enabled.is_(True))
            .order_by(PolicyRecord.policy_stage, PolicyRecord.policy_id)
        )
        if stages:
            stmt = stmt.where(PolicyRecord.policy_stage.in_(stages))
        session = self._session_factory()
        try:
            rows = session.execute(stmt).scalars().all()
        finally:
            session.close()
        return [policy_row_to_rule(row) for row in rows]
