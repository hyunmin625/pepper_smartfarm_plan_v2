from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

SMART_CHARACTER_MAP = str.maketrans(
    {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "，": ",",
        "：": ":",
    }
)


@dataclass(frozen=True)
class ParsedResponse:
    strict_json_ok: bool
    recovered_json_ok: bool
    json_object_ok: bool
    parse_error: str | None
    parsed_output: dict[str, Any] | None


def strip_markdown_fence(content: str) -> str:
    stripped = normalize_json_like_text(content)
    if not stripped.startswith("```"):
        return stripped
    stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def normalize_json_like_text(content: str) -> str:
    normalized = content.replace("\ufeff", "").translate(SMART_CHARACTER_MAP)
    normalized = normalized.replace("\u00a0", " ")
    return normalized.strip()


def extract_balanced_json_object(content: str) -> str | None:
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(content)):
        char = content[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]
    return None


def remove_trailing_commas(content: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", content)


def parse_response(raw_content: str) -> ParsedResponse:
    try:
        parsed = json.loads(raw_content)
        if isinstance(parsed, dict):
            return ParsedResponse(True, True, True, None, parsed)
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    else:
        return ParsedResponse(False, False, False, "response_is_not_json_object", None)

    normalized = normalize_json_like_text(raw_content)
    recovered_candidates: list[str] = [strip_markdown_fence(normalized)]
    balanced = extract_balanced_json_object(recovered_candidates[0])
    if balanced:
        recovered_candidates.append(balanced)
    recovered_candidates.extend(remove_trailing_commas(candidate) for candidate in list(recovered_candidates))

    seen: set[str] = set()
    for candidate in recovered_candidates:
        cleaned = candidate.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        try:
            parsed = json.loads(cleaned)
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
