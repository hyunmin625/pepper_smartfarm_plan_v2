from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL_REGISTRY_PATH = Path("artifacts/runtime/llm_orchestrator/model_registry.json")

DEFAULT_MODEL_REGISTRY = {
    "models": {
        "pepper-ops-local-stub": {
            "provider_hint": "stub",
            "resolved_model_id": "pepper-ops-local-stub",
            "prompt_version": "sft_v10",
            "status": "local_stub",
            "notes": "Local deterministic stub path for integration validation.",
        },
        "champion": {
            "provider_hint": "openai",
            "resolved_model_id": "ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3",
            "prompt_version": "sft_v5",
            "status": "production_candidate",
            "notes": "Current frozen baseline champion for runtime evaluation.",
        },
        "ds_v11_champion": {
            "provider_hint": "openai",
            "resolved_model_id": "ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3",
            "prompt_version": "sft_v5",
            "status": "production_candidate",
            "notes": "Same model as champion; kept as explicit historical alias.",
        },
        "ds_v14_rejected": {
            "provider_hint": "openai",
            "resolved_model_id": "ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz",
            "prompt_version": "sft_v10",
            "status": "rejected_challenger",
            "notes": "Historical rejected challenger kept for replay and regression comparison.",
        },
    }
}


@dataclass(frozen=True)
class ResolvedModelReference:
    requested_model_id: str
    resolved_model_id: str
    model_alias: str | None
    prompt_version: str | None
    provider_hint: str | None
    status: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested_model_id": self.requested_model_id,
            "resolved_model_id": self.resolved_model_id,
            "model_alias": self.model_alias,
            "prompt_version": self.prompt_version,
            "provider_hint": self.provider_hint,
            "status": self.status,
            "notes": self.notes,
        }


def load_model_registry(path: Path | None = None) -> dict[str, Any]:
    resolved_path = path or DEFAULT_MODEL_REGISTRY_PATH
    if resolved_path.exists():
        with resolved_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict) and isinstance(loaded.get("models"), dict):
            return loaded
    return DEFAULT_MODEL_REGISTRY


def resolve_model_reference(model_id: str, *, path: Path | None = None) -> ResolvedModelReference:
    registry = load_model_registry(path)
    models = registry.get("models", {})
    row = models.get(model_id)
    if not isinstance(row, dict):
        return ResolvedModelReference(
            requested_model_id=model_id,
            resolved_model_id=model_id,
            model_alias=None,
            prompt_version=None,
            provider_hint=None,
            status=None,
            notes=None,
        )
    return ResolvedModelReference(
        requested_model_id=model_id,
        resolved_model_id=str(row.get("resolved_model_id") or model_id),
        model_alias=model_id,
        prompt_version=str(row.get("prompt_version") or "") or None,
        provider_hint=str(row.get("provider_hint") or "") or None,
        status=str(row.get("status") or "") or None,
        notes=str(row.get("notes") or "") or None,
    )
