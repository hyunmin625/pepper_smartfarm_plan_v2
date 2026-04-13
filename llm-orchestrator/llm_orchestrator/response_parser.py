from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedResponse:
    strict_json_ok: bool
    recovered_json_ok: bool
    json_object_ok: bool
    parse_error: str | None
    parsed_output: dict[str, Any] | None


def strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_response(raw_content: str) -> ParsedResponse:
    try:
        parsed = json.loads(raw_content)
        if isinstance(parsed, dict):
            return ParsedResponse(True, True, True, None, parsed)
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    else:
        return ParsedResponse(False, False, False, "response_is_not_json_object", None)

    recovered_candidates = [strip_markdown_fence(raw_content)]
    stripped = recovered_candidates[0]
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        recovered_candidates.append(stripped[first_brace : last_brace + 1])

    for candidate in recovered_candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return ParsedResponse(False, True, True, parse_error, parsed)

    return ParsedResponse(False, False, False, parse_error, None)


def build_safe_fallback_output(
    *,
    task_type: str,
    zone_id: str,
    citations: list[dict[str, Any]],
    retrieval_coverage: str,
    parse_error: str | None = None,
) -> dict[str, Any]:
    common = {
        "risk_level": "unknown",
        "confidence": 0.22,
        "retrieval_coverage": retrieval_coverage,
        "citations": citations,
        "follow_up": [
            {
                "type": "manual_review",
                "note": "LLM output recovery fallback was used; operator review is required.",
            }
        ],
        "required_follow_up": [
            {
                "type": "manual_review",
                "zone_id": zone_id,
                "reason": parse_error or "llm_output_parse_failure",
            }
        ],
    }
    if task_type == "forbidden_action":
        return {
            **common,
            "decision": "approval_required",
            "blocked_action_type": "adjust_fertigation",
            "reason": parse_error or "llm_output_parse_failure",
        }
    if task_type == "robot_task_prioritization":
        return {
            **common,
            "robot_tasks": [
                {
                    "task_type": "manual_review",
                    "candidate_id": f"{zone_id}-manual-review",
                    "target": zone_id,
                    "reason": parse_error or "llm_output_parse_failure",
                }
            ],
        }
    return {
        **common,
        "recommended_actions": [
            {
                "action_type": "pause_automation",
                "approval_required": True,
                "reason": "llm_output_parse_failure",
            },
            {
                "action_type": "request_human_check",
                "approval_required": True,
                "reason": "llm_output_parse_failure",
            },
        ],
    }
