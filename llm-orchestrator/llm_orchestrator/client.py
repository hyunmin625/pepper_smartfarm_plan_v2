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

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except Exception:  # pragma: no cover
    google_genai = None
    google_genai_types = None

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
            "follow_up": [
                {
                    "type": "trend_review",
                    "zone_id": zone_id,
                    "description": "Review the recent climate and rootzone trend before any manual override.",
                }
            ],
            "required_follow_up": [
                {
                    "type": "operator_review",
                    "zone_id": zone_id,
                    "description": "Operator should confirm the suggested action against current greenhouse conditions.",
                }
            ],
        }
        if task_type == "chat":
            # Chat mode: the fine-tuned pepper greenhouse expert should
            # reply in natural Korean grounded in the supplied context.
            # The stub here approximates that behavior so dev/test
            # environments do not need a live OpenAI key to exercise the
            # AI 어시스턴트 view. Production uses the same orchestrator
            # model path as decision requests and switches behavior via
            # task_type plus grounding context.
            latest_user = str(payload.get("input", {}).get("latest_user_message") or "")
            context = payload.get("input", {}).get("context") or {}
            zone_snapshot = context.get("zone_snapshot") or {}
            current_state = zone_snapshot.get("current_state") or {}
            risk_level = zone_snapshot.get("risk_level") or "정상 범위"
            summary_parts: list[str] = []
            summary_parts.append(f"[stub 응답] 방금 '{latest_user[:80]}' 질문을 받았습니다.")
            if zone_id and zone_id != "unknown-zone":
                summary_parts.append(f"{zone_id} 최근 risk_level은 {risk_level}입니다.")
            if current_state:
                metric_line = ", ".join(
                    f"{k}={v}" for k, v in list(current_state.items())[:4] if isinstance(v, (int, float))
                )
                if metric_line:
                    summary_parts.append(f"최근 센서 스냅샷: {metric_line}.")
            summary_parts.append(
                "실제 파인튜닝된 적고추 온실 전문가 모델이 연결되면 도메인 근거에 기반한 한국어 답변이 제공됩니다."
            )
            reply_text = " ".join(summary_parts)
            output = {
                "reply": reply_text,
                "zone_id": zone_id,
                "context_keys": sorted(list(context.keys())),
                "mode": "chat_stub",
            }
        elif task_type == "forbidden_action":
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
                        "target": {"target_type": "zone", "target_id": zone_id},
                        "priority": "high",
                        "approval_required": True,
                        "reason": "Inspect the crop candidate before any harvest or skip-area decision.",
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


class GeminiCompletionClient:
    def __init__(self, config: ModelConfig) -> None:
        if google_genai is None:
            raise RuntimeError("google-genai package is not available")
        api_key = os.getenv(config.api_key_env)
        if not api_key and config.api_key_env == "OPENAI_API_KEY":
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                f"{config.api_key_env} is not set and neither GEMINI_API_KEY nor GOOGLE_API_KEY is available"
            )
        self.config = config
        self.model_ref = resolve_model_reference(config.model_id)
        self.client = google_genai.Client(api_key=api_key)

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
                raw_text = self._call_gemini(system_prompt=system_prompt, user_message=user_message)
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
                if not _should_retry_gemini_error(exc) or attempt >= self.config.max_retries:
                    break
                time.sleep(min(2 * attempt, 6))
        raise RuntimeError(f"Gemini invocation failed after {attempt} attempts: {last_error}") from last_error

    def _call_gemini(self, *, system_prompt: str, user_message: str) -> str:
        if google_genai_types is None:
            raise RuntimeError("google-genai package is not available")
        config_kwargs: dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": self.config.temperature,
            "max_output_tokens": 1600,
            "response_mime_type": "application/json",
        }
        try:
            config_kwargs["thinking_config"] = google_genai_types.ThinkingConfig(thinking_budget=0)
        except Exception:
            pass
        response = self.client.models.generate_content(
            model=self.model_ref.resolved_model_id,
            contents=[user_message],
            config=google_genai_types.GenerateContentConfig(**config_kwargs),
        )
        raw_text = getattr(response, "text", None) or ""
        if raw_text:
            return raw_text
        parts: list[str] = []
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", None) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        return "".join(parts)


def create_completion_client(config: ModelConfig) -> CompletionClient:
    if config.provider == "stub":
        return StubCompletionClient(config)
    if config.provider == "openai":
        return OpenAICompletionClient(config)
    if config.provider == "gemini":
        return GeminiCompletionClient(config)
    raise ValueError(f"unsupported provider: {config.provider}")


def _should_retry_openai_error(exc: Exception) -> bool:
    return isinstance(exc, (RateLimitError, APITimeoutError, APIError))


def _should_retry_gemini_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(token in message for token in ("rate", "timeout", "unavailable", "503", "500", "deadline", "quota"))


def get_resolved_model_reference(model_id: str) -> ResolvedModelReference:
    return resolve_model_reference(model_id)
