from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from policy_engine.output_validator import ValidatorContext, apply_output_validator


DEFAULT_AUDIT_PATH = Path("artifacts/runtime/llm_orchestrator/output_validator_audit.jsonl")


@dataclass(frozen=True)
class LLMDecisionEnvelope:
    request_id: str
    task_type: str
    context: ValidatorContext
    output: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LLMDecisionEnvelope":
        return cls(
            request_id=str(raw["request_id"]),
            task_type=str(raw["task_type"]),
            context=ValidatorContext.from_dict(raw["context"]),
            output=dict(raw["output"]),
        )


@dataclass(frozen=True)
class ValidationAuditRecord:
    request_id: str
    task_type: str
    zone_id: str
    validator_decision: str
    validator_reason_codes: list[str]
    risk_level_before: str | None
    risk_level_after: str | None
    action_types_before: list[str]
    action_types_after: list[str]
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type,
            "zone_id": self.zone_id,
            "validator_decision": self.validator_decision,
            "validator_reason_codes": self.validator_reason_codes,
            "risk_level_before": self.risk_level_before,
            "risk_level_after": self.risk_level_after,
            "action_types_before": self.action_types_before,
            "action_types_after": self.action_types_after,
            "created_at": self.created_at,
        }


def _audit_path() -> Path:
    configured = os.getenv("LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH")
    return Path(configured) if configured else DEFAULT_AUDIT_PATH


def _action_types(payload: dict[str, Any]) -> list[str]:
    return [
        str(action.get("action_type"))
        for action in payload.get("recommended_actions", [])
        if isinstance(action, dict) and action.get("action_type")
    ]


def _write_audit(record: ValidationAuditRecord) -> Path:
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.as_dict(), ensure_ascii=False) + "\n")
    return path


def run_output_validator(envelope: LLMDecisionEnvelope) -> tuple[dict[str, Any], ValidationAuditRecord, Path]:
    before = envelope.output
    result = apply_output_validator(before, envelope.context)
    audit = ValidationAuditRecord(
        request_id=envelope.request_id,
        task_type=envelope.task_type,
        zone_id=envelope.context.zone_id,
        validator_decision=result.decision,
        validator_reason_codes=result.applied_rules,
        risk_level_before=before.get("risk_level"),
        risk_level_after=result.output.get("risk_level"),
        action_types_before=_action_types(before),
        action_types_after=_action_types(result.output),
        created_at=datetime.now(UTC).isoformat(),
    )
    audit_path = _write_audit(audit)
    return result.output, audit, audit_path
