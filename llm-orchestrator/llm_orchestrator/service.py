from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .client import CompletionClient, ModelConfig, create_completion_client
from .prompt_catalog import get_system_prompt
from .response_parser import ParsedResponse, build_safe_fallback_output, parse_response
from .retriever import KeywordRagRetriever, RetrievedChunk
from policy_engine.output_validator import ValidatorContext

from .runtime import LLMDecisionEnvelope, ShadowModeMetadata, ShadowModeObservedOutcome, run_output_validator, run_shadow_mode_capture


@dataclass(frozen=True)
class OrchestratorRequest:
    request_id: str
    zone_id: str
    task_type: str
    zone_state: dict[str, Any]
    prompt_version: str = "sft_v10"
    retrieval_limit: int = 5
    mode: str = "shadow"
    farm_id: str = "demo-farm"
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "OrchestratorRequest":
        return cls(
            request_id=str(raw["request_id"]),
            zone_id=str(raw["zone_id"]),
            task_type=str(raw["task_type"]),
            zone_state=dict(raw.get("zone_state") or {}),
            prompt_version=str(raw.get("prompt_version") or "sft_v10"),
            retrieval_limit=int(raw.get("retrieval_limit") or 5),
            mode=str(raw.get("mode") or "shadow"),
            farm_id=str(raw.get("farm_id") or "demo-farm"),
            metadata=dict(raw.get("metadata") or {}),
        )


@dataclass(frozen=True)
class OrchestratorResult:
    request: OrchestratorRequest
    model_id: str
    provider: str
    raw_text: str
    parse_result: ParsedResponse
    parsed_output: dict[str, Any]
    validated_output: dict[str, Any]
    retrieval_chunks: list[RetrievedChunk]
    audit_path: str
    validator_reason_codes: list[str]
    used_repair_prompt: bool
    fallback_used: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request.request_id,
            "zone_id": self.request.zone_id,
            "task_type": self.request.task_type,
            "model_id": self.model_id,
            "provider": self.provider,
            "raw_text": self.raw_text,
            "parse_result": {
                "strict_json_ok": self.parse_result.strict_json_ok,
                "recovered_json_ok": self.parse_result.recovered_json_ok,
                "json_object_ok": self.parse_result.json_object_ok,
                "parse_error": self.parse_result.parse_error,
            },
            "parsed_output": self.parsed_output,
            "validated_output": self.validated_output,
            "retrieval_chunks": [chunk.as_prompt_dict() for chunk in self.retrieval_chunks],
            "audit_path": self.audit_path,
            "validator_reason_codes": self.validator_reason_codes,
            "used_repair_prompt": self.used_repair_prompt,
            "fallback_used": self.fallback_used,
        }


class LLMOrchestratorService:
    def __init__(
        self,
        *,
        client: CompletionClient,
        retriever: KeywordRagRetriever | None = None,
    ) -> None:
        self.client = client
        self.retriever = retriever or KeywordRagRetriever()

    @classmethod
    def from_model_config(cls, config: ModelConfig, *, retriever: KeywordRagRetriever | None = None) -> "LLMOrchestratorService":
        return cls(client=create_completion_client(config), retriever=retriever)

    def evaluate(self, request: OrchestratorRequest) -> OrchestratorResult:
        prompt = get_system_prompt(request.prompt_version)
        retrieval_chunks = self._retrieve_context(request)
        user_message = self._build_user_message(request, retrieval_chunks)

        invocation = self.client.complete(system_prompt=prompt, user_message=user_message)
        parse_result = parse_response(invocation.raw_text)
        fallback_used = False
        repaired = False
        parsed_output = parse_result.parsed_output

        if parsed_output is None:
            repair_invocation = self.client.repair_json(original_output=invocation.raw_text, task_type=request.task_type)
            repaired = repair_invocation.used_repair_prompt
            invocation = repair_invocation
            parse_result = parse_response(repair_invocation.raw_text)
            parsed_output = parse_result.parsed_output

        if parsed_output is None:
            fallback_used = True
            parsed_output = build_safe_fallback_output(
                task_type=request.task_type,
                zone_id=request.zone_id,
                citations=[chunk.as_citation_dict() for chunk in retrieval_chunks[:2]],
                retrieval_coverage="sufficient" if retrieval_chunks else "not_used",
                parse_error=parse_result.parse_error,
            )

        parsed_output = self._ensure_citations(parsed_output, retrieval_chunks)
        envelope = LLMDecisionEnvelope(
            request_id=request.request_id,
            task_type=request.task_type,
            context=ValidatorContext.from_dict(self._validator_context(request)),
            output=parsed_output,
        )
        validated_output, audit, audit_path = run_output_validator(envelope)
        return OrchestratorResult(
            request=request,
            model_id=invocation.model_id,
            provider=invocation.provider,
            raw_text=invocation.raw_text,
            parse_result=parse_result,
            parsed_output=parsed_output,
            validated_output=validated_output,
            retrieval_chunks=retrieval_chunks,
            audit_path=str(audit_path),
            validator_reason_codes=audit.validator_reason_codes,
            used_repair_prompt=repaired,
            fallback_used=fallback_used,
        )

    def capture_shadow(
        self,
        request: OrchestratorRequest,
        observed: ShadowModeObservedOutcome,
        *,
        metadata: ShadowModeMetadata,
    ) -> dict[str, Any]:
        prompt = get_system_prompt(request.prompt_version)
        retrieval_chunks = self._retrieve_context(request)
        user_message = self._build_user_message(request, retrieval_chunks)
        invocation = self.client.complete(system_prompt=prompt, user_message=user_message)
        parse_result = parse_response(invocation.raw_text)
        parsed_output = parse_result.parsed_output or build_safe_fallback_output(
            task_type=request.task_type,
            zone_id=request.zone_id,
            citations=[chunk.as_citation_dict() for chunk in retrieval_chunks[:2]],
            retrieval_coverage="sufficient" if retrieval_chunks else "not_used",
            parse_error=parse_result.parse_error,
        )
        parsed_output = self._ensure_citations(parsed_output, retrieval_chunks)
        envelope = LLMDecisionEnvelope(
            request_id=request.request_id,
            task_type=request.task_type,
            context=ValidatorContext.from_dict(self._validator_context(request)),
            output=parsed_output,
        )
        validated_output, validator_audit, shadow_record, shadow_path = run_shadow_mode_capture(
            envelope,
            metadata=metadata,
            observed=observed,
        )
        return {
            "validated_output": validated_output,
            "validator_reason_codes": validator_audit.validator_reason_codes,
            "shadow_audit_path": str(shadow_path),
            "shadow_record": shadow_record.as_dict(),
        }

    def _retrieve_context(self, request: OrchestratorRequest) -> list[RetrievedChunk]:
        zone_state = request.zone_state
        feature_snapshot = zone_state.get("derived_features", {})
        climate = feature_snapshot.get("climate", {})
        rootzone = feature_snapshot.get("rootzone", {})
        query_parts = [
            request.task_type,
            str(zone_state.get("growth_stage") or ""),
            str(zone_state.get("current_state", {}).get("summary") or ""),
            str(climate.get("heat_stress_risk", {}).get("level") or ""),
            str(rootzone.get("rootzone_stress_risk", {}).get("level") or ""),
        ]
        return self.retriever.search(
            query=" ".join(part for part in query_parts if part),
            task_type=request.task_type,
            zone_id=request.zone_id,
            growth_stage=str(zone_state.get("growth_stage") or "unknown"),
            limit=request.retrieval_limit,
        )

    def _build_user_message(self, request: OrchestratorRequest, retrieval_chunks: list[RetrievedChunk]) -> str:
        payload = {
            "task_type": request.task_type,
            "input": {
                "farm_id": request.farm_id,
                "zone_id": request.zone_id,
                "zone_state": request.zone_state,
                "retrieved_context": [chunk.as_prompt_dict() for chunk in retrieval_chunks],
                "active_constraints": request.zone_state.get("constraints", {}),
                "weather_context": request.zone_state.get("weather_context", {}),
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)

    def _validator_context(self, request: OrchestratorRequest) -> dict[str, Any]:
        zone_state = request.zone_state
        current_state = zone_state.get("current_state", {})
        sensor_quality = zone_state.get("sensor_quality", {})
        climate = zone_state.get("derived_features", {}).get("climate", {})
        rootzone = zone_state.get("derived_features", {}).get("rootzone", {})
        action_snapshot = zone_state.get("active_constraints", {})
        return {
            "farm_id": request.farm_id,
            "zone_id": request.zone_id,
            "task_type": request.task_type,
            "summary": str(current_state.get("summary") or ""),
            "requires_citations": True,
            "worker_present": bool(current_state.get("worker_present") or current_state.get("operator_present")),
            "manual_override_active": bool(current_state.get("manual_override")),
            "safe_mode_active": bool(current_state.get("safe_mode")),
            "climate_control_degraded": climate.get("heat_stress_risk", {}).get("level") in {"high", "critical"} and str(sensor_quality.get("overall") or "") != "good",
            "irrigation_path_degraded": bool(action_snapshot.get("irrigation_path_degraded") or action_snapshot.get("core_water_path_degraded")),
            "source_water_path_degraded": bool(action_snapshot.get("source_water_path_degraded")),
            "dry_room_path_degraded": bool(action_snapshot.get("dry_room_path_degraded")),
            "rootzone_sensor_conflict": rootzone.get("rootzone_stress_risk", {}).get("level") == "unknown",
            "rootzone_control_interpretable": rootzone.get("rootzone_stress_risk", {}).get("level") != "unknown",
            "core_climate_interpretable": str(sensor_quality.get("overall") or "") == "good",
            "zone_clearance_uncertain": bool(action_snapshot.get("zone_clearance_uncertain")),
            "aisle_slip_hazard": bool(action_snapshot.get("aisle_slip_hazard")),
        }

    @staticmethod
    def _ensure_citations(parsed_output: dict[str, Any], retrieval_chunks: list[RetrievedChunk]) -> dict[str, Any]:
        if parsed_output.get("citations"):
            return parsed_output
        if not retrieval_chunks:
            parsed_output["retrieval_coverage"] = parsed_output.get("retrieval_coverage") or "not_used"
            parsed_output["citations"] = []
            return parsed_output
        parsed_output["retrieval_coverage"] = parsed_output.get("retrieval_coverage") or "sufficient"
        parsed_output["citations"] = [chunk.as_citation_dict() for chunk in retrieval_chunks[:2]]
        return parsed_output
