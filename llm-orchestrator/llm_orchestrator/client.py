from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

try:
    from openai import APIError, APITimeoutError, OpenAI, RateLimitError
except Exception:  # pragma: no cover
    OpenAI = None
    APIError = Exception
    APITimeoutError = Exception
    RateLimitError = Exception

from .model_registry import ResolvedModelReference, resolve_model_reference


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_id: str
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    repair_retries: int = 1
    temperature: float = 0.1


@dataclass(frozen=True)
class ModelInvocation:
    raw_text: str
    model_id: str
    provider: str
    attempts: int
    used_repair_prompt: bool = False
    model_alias: str | None = None


class CompletionClient(Protocol):
    def complete(self, *, system_prompt: str, user_message: str) -> ModelInvocation: ...
    def repair_json(self, *, original_output: str, task_type: str) -> ModelInvocation: ...


class StubCompletionClient:
    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.model_ref = resolve_model_reference(config.model_id)

    def complete(self, *, system_prompt: str, user_message: str) -> ModelInvocation:
        payload = json.loads(user_message)
        task_type = str(payload.get("task_type") or "state_judgement")
        zone_id = str(payload.get("input", {}).get("zone_id") or payload.get("input", {}).get("zone_state", {}).get("zone_id") or "unknown-zone")
        retrieval_context = payload.get("input", {}).get("retrieved_context") or []
        citations = []
        if isinstance(retrieval_context, list):
            for item in retrieval_context[:2]:
                if isinstance(item, dict) and item.get("chunk_id"):
                    citations.append(
                        {
                            "chunk_id": item["chunk_id"],
                            "document_id": item.get("document_id"),
                        }
                    )
        common = {
            "risk_level": "medium",
            "confidence": 0.55,
            "retrieval_coverage": "sufficient" if citations else "not_used",
            "citations": citations,
            "follow_up": [{"type": "trend_review", "zone_id": zone_id}],
            "required_follow_up": [{"type": "operator_review", "zone_id": zone_id}],
        }
        if task_type == "forbidden_action":
            output = {
                **common,
                "decision": "approval_required",
                "blocked_action_type": "adjust_fertigation",
            }
        elif task_type == "robot_task_prioritization":
            output = {
                **common,
                "risk_level": "high",
                "robot_tasks": [
                    {
                        "task_type": "inspect_crop",
                        "candidate_id": f"{zone_id}-candidate-001",
                        "target": zone_id,
                        "priority": "high",
                    }
                ],
            }
        else:
            output = {
                **common,
                "recommended_actions": [
                    {"action_type": "create_alert", "approval_required": False},
                    {"action_type": "request_human_check", "approval_required": True},
                ],
            }
        return ModelInvocation(
            raw_text=json.dumps(output, ensure_ascii=False),
            model_id=self.model_ref.resolved_model_id,
            provider="stub",
            attempts=1,
            model_alias=self.model_ref.model_alias,
        )

    def repair_json(self, *, original_output: str, task_type: str) -> ModelInvocation:
        return ModelInvocation(
            raw_text=original_output,
            model_id=self.model_ref.resolved_model_id,
            provider="stub",
            attempts=1,
            used_repair_prompt=True,
            model_alias=self.model_ref.model_alias,
        )


class OpenAICompletionClient:
    def __init__(self, config: ModelConfig) -> None:
        if OpenAI is None:
            raise RuntimeError("openai package is not available")
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise RuntimeError(f"{config.api_key_env} is not set")
        self.config = config
        self.model_ref = resolve_model_reference(config.model_id)
        self.client = OpenAI(api_key=api_key, timeout=config.timeout_seconds)

    def complete(self, *, system_prompt: str, user_message: str) -> ModelInvocation:
        return self._invoke(system_prompt=system_prompt, user_message=user_message, used_repair_prompt=False)

    def repair_json(self, *, original_output: str, task_type: str) -> ModelInvocation:
        repair_system = (
            "You repair malformed assistant outputs. "
            "Return valid JSON only. Preserve original fields when possible. "
            "Do not add markdown fences or explanations."
        )
        repair_user = json.dumps(
            {
                "task_type": task_type,
                "malformed_output": original_output,
            },
            ensure_ascii=False,
        )
        return self._invoke(system_prompt=repair_system, user_message=repair_user, used_repair_prompt=True)

    def _invoke(self, *, system_prompt: str, user_message: str, used_repair_prompt: bool) -> ModelInvocation:
        attempt = 0
        last_error: Exception | None = None
        while attempt < self.config.max_retries:
            attempt += 1
            try:
                raw_text = self._call_openai(system_prompt=system_prompt, user_message=user_message)
                return ModelInvocation(
                    raw_text=raw_text,
                    model_id=self.model_ref.resolved_model_id,
                    provider=self.config.provider,
                    attempts=attempt,
                    used_repair_prompt=used_repair_prompt,
                    model_alias=self.model_ref.model_alias,
                )
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if not _should_retry_openai_error(exc) or attempt >= self.config.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 4))
        raise RuntimeError(f"OpenAI invocation failed after {attempt} attempts: {last_error}") from last_error

    def _call_openai(self, *, system_prompt: str, user_message: str) -> str:
        if hasattr(self.client, "responses"):
            try:
                response = self.client.responses.create(
                    model=self.model_ref.resolved_model_id,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=self.config.temperature,
                )
                output_text = getattr(response, "output_text", None)
                if isinstance(output_text, str) and output_text.strip():
                    return output_text
            except Exception:
                pass

        response = self.client.chat.completions.create(
            model=self.model_ref.resolved_model_id,
            temperature=self.config.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return str(response.choices[0].message.content or "")


def create_completion_client(config: ModelConfig) -> CompletionClient:
    if config.provider == "stub":
        return StubCompletionClient(config)
    if config.provider == "openai":
        return OpenAICompletionClient(config)
    raise ValueError(f"unsupported provider: {config.provider}")


def _should_retry_openai_error(exc: Exception) -> bool:
    return isinstance(exc, (RateLimitError, APITimeoutError, APIError))


def get_resolved_model_reference(model_id: str) -> ResolvedModelReference:
    return resolve_model_reference(model_id)
