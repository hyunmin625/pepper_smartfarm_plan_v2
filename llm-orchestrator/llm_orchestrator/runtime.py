from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from policy_engine.output_validator import ValidatorContext, apply_output_validator


DEFAULT_AUDIT_PATH = Path("artifacts/runtime/llm_orchestrator/output_validator_audit.jsonl")
DEFAULT_SHADOW_AUDIT_PATH = Path("artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl")
HIGH_APPROVAL_ACTIONS = {"adjust_fertigation", "adjust_heating", "adjust_co2", "create_robot_task"}


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


@dataclass(frozen=True)
class ShadowModeMetadata:
    model_id: str
    prompt_id: str
    dataset_id: str
    eval_set_id: str
    retrieval_profile_id: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ShadowModeMetadata":
        return cls(
            model_id=str(raw.get("model_id") or "unknown-model"),
            prompt_id=str(raw.get("prompt_id") or "unknown-prompt"),
            dataset_id=str(raw.get("dataset_id") or "unknown-dataset"),
            eval_set_id=str(raw.get("eval_set_id") or "shadow-runtime"),
            retrieval_profile_id=str(raw.get("retrieval_profile_id") or "unknown-retrieval-profile"),
        )


@dataclass(frozen=True)
class ShadowModeObservedOutcome:
    operator_action_types: list[str]
    operator_agreement: bool | None = None
    operator_decision: str | None = None
    operator_blocked_action_type: str | None = None
    critical_disagreement: bool = False
    manual_override_used: bool = False
    growth_stage: str = "unknown"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ShadowModeObservedOutcome":
        operator_action_types = [
            str(action_type)
            for action_type in raw.get("operator_action_types", [])
            if isinstance(action_type, str) and action_type.strip()
        ]
        operator_agreement_raw = raw.get("operator_agreement")
        return cls(
            operator_action_types=operator_action_types,
            operator_agreement=operator_agreement_raw if isinstance(operator_agreement_raw, bool) else None,
            operator_decision=str(raw.get("operator_decision") or "").strip() or None,
            operator_blocked_action_type=str(raw.get("operator_blocked_action_type") or "").strip() or None,
            critical_disagreement=bool(raw.get("critical_disagreement")),
            manual_override_used=bool(raw.get("manual_override_used")),
            growth_stage=str(raw.get("growth_stage") or "unknown"),
        )


@dataclass(frozen=True)
class ShadowModeAuditRecord:
    request_id: str
    model_id: str
    prompt_id: str
    dataset_id: str
    eval_set_id: str
    retrieval_profile_id: str
    task_type: str
    zone_id: str
    growth_stage: str
    schema_pass: bool
    citation_required: bool
    citation_present: bool
    retrieval_hit: bool
    retrieval_coverage: str | None
    validator_decision: str
    validator_reason_codes: list[str]
    ai_action_types_before: list[str]
    ai_action_types_after: list[str]
    ai_decision_after: str | None
    ai_blocked_action_type_after: str | None
    operator_action_types: list[str]
    operator_decision: str | None
    operator_blocked_action_type: str | None
    operator_agreement: bool
    critical_disagreement: bool
    manual_override_used: bool
    blocked_action_recommendation_count: int
    approval_missing_count: int
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "prompt_id": self.prompt_id,
            "dataset_id": self.dataset_id,
            "eval_set_id": self.eval_set_id,
            "retrieval_profile_id": self.retrieval_profile_id,
            "task_type": self.task_type,
            "zone_id": self.zone_id,
            "growth_stage": self.growth_stage,
            "schema_pass": self.schema_pass,
            "citation_required": self.citation_required,
            "citation_present": self.citation_present,
            "retrieval_hit": self.retrieval_hit,
            "retrieval_coverage": self.retrieval_coverage,
            "validator_decision": self.validator_decision,
            "validator_reason_codes": self.validator_reason_codes,
            "ai_action_types_before": self.ai_action_types_before,
            "ai_action_types_after": self.ai_action_types_after,
            "ai_decision_after": self.ai_decision_after,
            "ai_blocked_action_type_after": self.ai_blocked_action_type_after,
            "operator_action_types": self.operator_action_types,
            "operator_decision": self.operator_decision,
            "operator_blocked_action_type": self.operator_blocked_action_type,
            "operator_agreement": self.operator_agreement,
            "critical_disagreement": self.critical_disagreement,
            "manual_override_used": self.manual_override_used,
            "blocked_action_recommendation_count": self.blocked_action_recommendation_count,
            "approval_missing_count": self.approval_missing_count,
            "created_at": self.created_at,
        }


def _audit_path() -> Path:
    configured = os.getenv("LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH")
    return Path(configured) if configured else DEFAULT_AUDIT_PATH


def _shadow_audit_path() -> Path:
    configured = os.getenv("LLM_OUTPUT_VALIDATOR_SHADOW_LOG_PATH")
    return Path(configured) if configured else DEFAULT_SHADOW_AUDIT_PATH


def _action_types(task_type: str, payload: dict[str, Any]) -> list[str]:
    if task_type == "forbidden_action":
        decision = str(payload.get("decision") or "")
        if decision == "block":
            return ["block_action"]
        if decision == "approval_required":
            return ["request_human_check"]
        return []
    return [
        str(action.get("action_type"))
        for action in payload.get("recommended_actions", [])
        if isinstance(action, dict) and action.get("action_type")
    ]


def _schema_pass(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if not payload.get("risk_level"):
        return False
    actions = payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    return all(isinstance(action, dict) and action.get("action_type") for action in actions)


def _citation_present(payload: dict[str, Any]) -> bool:
    citations = payload.get("citations")
    return isinstance(citations, list) and bool(citations)


def _retrieval_hit(payload: dict[str, Any]) -> bool:
    coverage = payload.get("retrieval_coverage")
    return coverage in {"sufficient", "partial"}


def _operator_agreement(
    task_type: str,
    payload: dict[str, Any],
    ai_action_types: list[str],
    observed: ShadowModeObservedOutcome,
) -> bool:
    if observed.operator_agreement is not None:
        return observed.operator_agreement
    if task_type == "forbidden_action" and observed.operator_decision:
        if str(payload.get("decision") or "") != observed.operator_decision:
            return False
        if observed.operator_decision == "block" and observed.operator_blocked_action_type:
            return str(payload.get("blocked_action_type") or "") == observed.operator_blocked_action_type
        return True
    return sorted(ai_action_types) == sorted(observed.operator_action_types)


def _blocked_action_recommendation_count(ai_action_types: list[str]) -> int:
    return sum(1 for action_type in ai_action_types if action_type == "block_action")


def _approval_missing_count(payload: dict[str, Any]) -> int:
    count = 0
    for action in payload.get("recommended_actions", []):
        if not isinstance(action, dict):
            continue
        if action.get("action_type") in HIGH_APPROVAL_ACTIONS and action.get("approval_required") is not True:
            count += 1
    return count


def _write_audit(record: ValidationAuditRecord) -> Path:
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.as_dict(), ensure_ascii=False) + "\n")
    return path


def _write_shadow_audit(record: ShadowModeAuditRecord) -> Path:
    path = _shadow_audit_path()
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
        action_types_before=_action_types(envelope.task_type, before),
        action_types_after=_action_types(envelope.task_type, result.output),
        created_at=datetime.now(UTC).isoformat(),
    )
    audit_path = _write_audit(audit)
    return result.output, audit, audit_path


def run_shadow_mode_capture(
    envelope: LLMDecisionEnvelope,
    metadata: ShadowModeMetadata,
    observed: ShadowModeObservedOutcome,
) -> tuple[dict[str, Any], ValidationAuditRecord, ShadowModeAuditRecord, Path]:
    validated_output, validator_audit, _ = run_output_validator(envelope)
    ai_action_types_after = _action_types(envelope.task_type, validated_output)
    shadow_record = ShadowModeAuditRecord(
        request_id=envelope.request_id,
        model_id=metadata.model_id,
        prompt_id=metadata.prompt_id,
        dataset_id=metadata.dataset_id,
        eval_set_id=metadata.eval_set_id,
        retrieval_profile_id=metadata.retrieval_profile_id,
        task_type=envelope.task_type,
        zone_id=envelope.context.zone_id,
        growth_stage=observed.growth_stage,
        schema_pass=_schema_pass(validated_output),
        citation_required=envelope.context.requires_citations,
        citation_present=_citation_present(validated_output),
        retrieval_hit=_retrieval_hit(validated_output),
        retrieval_coverage=validated_output.get("retrieval_coverage"),
        validator_decision=validator_audit.validator_decision,
        validator_reason_codes=validator_audit.validator_reason_codes,
        ai_action_types_before=validator_audit.action_types_before,
        ai_action_types_after=ai_action_types_after,
        ai_decision_after=str(validated_output.get("decision") or "").strip() or None,
        ai_blocked_action_type_after=str(validated_output.get("blocked_action_type") or "").strip() or None,
        operator_action_types=observed.operator_action_types,
        operator_decision=observed.operator_decision,
        operator_blocked_action_type=observed.operator_blocked_action_type,
        operator_agreement=_operator_agreement(envelope.task_type, validated_output, ai_action_types_after, observed),
        critical_disagreement=observed.critical_disagreement,
        manual_override_used=observed.manual_override_used,
        blocked_action_recommendation_count=_blocked_action_recommendation_count(ai_action_types_after),
        approval_missing_count=_approval_missing_count(validated_output),
        created_at=datetime.now(UTC).isoformat(),
    )
    shadow_path = _write_shadow_audit(shadow_record)
    return validated_output, validator_audit, shadow_record, shadow_path
