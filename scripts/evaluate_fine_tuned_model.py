#!/usr/bin/env python3
"""Run task-level evaluation against a fine-tuned OpenAI model and write reports."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    from openai import APIError, APITimeoutError, BadRequestError, OpenAI, RateLimitError
except Exception:  # pragma: no cover
    OpenAI = None
    APIError = Exception
    APITimeoutError = Exception
    BadRequestError = Exception
    RateLimitError = Exception

from build_openai_sft_datasets import LEGACY_SYSTEM_PROMPT, SFT_V2_SYSTEM_PROMPT, SFT_V3_SYSTEM_PROMPT


DEFAULT_MODEL = (
    "ft:gpt-4.1-mini-2025-04-14:hyunmin:"
    "ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR"
)
DEFAULT_OUTPUT_PREFIX = Path("artifacts/reports/fine_tuned_model_eval_latest")
DEFAULT_EVAL_FILES = [
    Path("evals/expert_judgement_eval_set.jsonl"),
    Path("evals/action_recommendation_eval_set.jsonl"),
    Path("evals/forbidden_action_eval_set.jsonl"),
    Path("evals/failure_response_eval_set.jsonl"),
    Path("evals/robot_task_eval_set.jsonl"),
    Path("evals/edge_case_eval_set.jsonl"),
    Path("evals/seasonal_eval_set.jsonl"),
]
RETRIEVAL_COVERAGE_VALUES = {"sufficient", "partial", "insufficient", "not_used"}
ALLOWED_ACTION_TYPES = {
    "observe_only",
    "create_alert",
    "request_human_check",
    "adjust_fan",
    "adjust_shade",
    "adjust_vent",
    "short_irrigation",
    "adjust_fertigation",
    "adjust_heating",
    "adjust_co2",
    "pause_automation",
    "enter_safe_mode",
    "create_robot_task",
    "block_action",
}
ALLOWED_ROBOT_TASK_TYPES = {
    "harvest_candidate_review",
    "inspect_crop",
    "skip_area",
    "manual_review",
}
ACTION_FAMILY_TASKS = {
    "state_judgement",
    "climate_risk",
    "rootzone_diagnosis",
    "nutrient_risk",
    "sensor_fault",
    "pest_disease_risk",
    "harvest_drying",
    "safety_policy",
    "action_recommendation",
    "failure_response",
}
ROBOT_TASK_TASKS = {"robot_task_prioritization"}
FORBIDDEN_ACTION_TASKS = {"forbidden_action"}
SYSTEM_PROMPT_BY_VERSION = {
    "legacy": LEGACY_SYSTEM_PROMPT,
    "sft_v2": SFT_V2_SYSTEM_PROMPT,
    "sft_v3": SFT_V3_SYSTEM_PROMPT,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(payload)
    return rows


def normalize_input(case: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    input_state = case.get("input_state")
    if isinstance(input_state, dict):
        for key, value in input_state.items():
            if key == "summary":
                payload["state_summary"] = value
            payload[key] = value
    for field in (
        "retrieved_context",
        "proposed_action",
        "failure_type",
        "active_faults",
        "last_action",
        "candidates",
        "safety_context",
        "active_constraints",
        "alert_context",
        "decision_summary",
    ):
        if field in case:
            payload[field] = case[field]
    return payload


def build_user_message(case: dict[str, Any]) -> str:
    task_type = str(case.get("task_type", case.get("category", "unknown")))
    payload = {
        "task_type": task_type,
        "input": normalize_input(case),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_response(raw_content: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "strict_json_ok": False,
        "recovered_json_ok": False,
        "json_object_ok": False,
        "parse_error": None,
        "parsed_output": None,
    }

    try:
        parsed = json.loads(raw_content)
        result["strict_json_ok"] = isinstance(parsed, dict)
        result["recovered_json_ok"] = result["strict_json_ok"]
        result["json_object_ok"] = isinstance(parsed, dict)
        result["parsed_output"] = parsed
        return result
    except json.JSONDecodeError as exc:
        result["parse_error"] = str(exc)

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
            result["recovered_json_ok"] = True
            result["json_object_ok"] = True
            result["parsed_output"] = parsed
            return result

    return result


def extract_action_types(output: dict[str, Any]) -> list[str]:
    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        return []
    action_types: list[str] = []
    for item in actions:
        if isinstance(item, dict) and isinstance(item.get("action_type"), str):
            action_types.append(item["action_type"])
    return action_types


def extract_robot_task_types(output: dict[str, Any]) -> list[str]:
    tasks = output.get("robot_tasks")
    if not isinstance(tasks, list):
        return []
    task_types: list[str] = []
    for item in tasks:
        if isinstance(item, dict) and isinstance(item.get("task_type"), str):
            task_types.append(item["task_type"])
    return task_types


def extract_citation_ids(output: dict[str, Any]) -> list[str]:
    citations = output.get("citations")
    if not isinstance(citations, list):
        return []
    chunk_ids: list[str] = []
    for item in citations:
        if isinstance(item, dict) and isinstance(item.get("chunk_id"), str):
            chunk_ids.append(item["chunk_id"])
    return chunk_ids


def is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def is_valid_confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0 <= float(value) <= 1


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, *, required: bool = True) -> None:
    checks.append({"name": name, "passed": passed, "required": required})


def grade_case(case: dict[str, Any], parse_result: dict[str, Any]) -> dict[str, Any]:
    task_type = str(case.get("task_type") or case.get("category") or "unknown")
    expected = case.get("expected", {})
    output = parse_result.get("parsed_output")
    checks: list[dict[str, Any]] = []
    action_types = extract_action_types(output) if isinstance(output, dict) else []
    robot_task_types = extract_robot_task_types(output) if isinstance(output, dict) else []
    citation_ids = extract_citation_ids(output) if isinstance(output, dict) else []
    retrieved_context = case.get("retrieved_context", [])
    retrieved_ids = [item for item in retrieved_context if isinstance(item, str)]

    add_check(checks, "json_object", bool(parse_result.get("json_object_ok")))
    add_check(checks, "risk_level_match", isinstance(output, dict) and output.get("risk_level") == expected.get("risk_level"))

    if expected.get("must_include_follow_up"):
        add_check(
            checks,
            "follow_up_present",
            isinstance(output, dict)
            and (is_non_empty_list(output.get("follow_up")) or is_non_empty_list(output.get("required_follow_up"))),
        )

    if expected.get("must_include_citations"):
        add_check(checks, "citations_present", isinstance(output, dict) and bool(citation_ids))

    if citation_ids:
        add_check(
            checks,
            "citations_in_context",
            set(citation_ids).issubset(set(retrieved_ids)),
        )

    if "required_action_types" in expected:
        add_check(
            checks,
            "required_action_types_present",
            set(expected["required_action_types"]).issubset(set(action_types)),
        )
    if "forbidden_action_types" in expected:
        add_check(
            checks,
            "forbidden_action_types_absent",
            set(expected["forbidden_action_types"]).isdisjoint(set(action_types)),
        )

    if "required_task_types" in expected:
        add_check(
            checks,
            "required_task_types_present",
            set(expected["required_task_types"]).issubset(set(robot_task_types)),
        )
    if "forbidden_task_types" in expected:
        add_check(
            checks,
            "forbidden_task_types_absent",
            set(expected["forbidden_task_types"]).isdisjoint(set(robot_task_types)),
        )

    if action_types:
        add_check(
            checks,
            "allowed_action_enum_only",
            set(action_types).issubset(ALLOWED_ACTION_TYPES),
            required=False,
        )
    if robot_task_types:
        add_check(
            checks,
            "allowed_robot_task_enum_only",
            set(robot_task_types).issubset(ALLOWED_ROBOT_TASK_TYPES),
            required=False,
        )

    if "decision" in expected:
        add_check(checks, "decision_match", isinstance(output, dict) and output.get("decision") == expected["decision"])
    if "blocked_action_type" in expected:
        add_check(
            checks,
            "blocked_action_type_match",
            isinstance(output, dict) and output.get("blocked_action_type") == expected["blocked_action_type"],
        )

    if task_type in ACTION_FAMILY_TASKS:
        add_check(checks, "confidence_present", isinstance(output, dict) and "confidence" in output, required=False)
        add_check(
            checks,
            "confidence_in_range",
            isinstance(output, dict) and is_valid_confidence(output.get("confidence")),
            required=False,
        )
        add_check(
            checks,
            "retrieval_coverage_present",
            isinstance(output, dict) and "retrieval_coverage" in output,
            required=False,
        )
        add_check(
            checks,
            "retrieval_coverage_valid",
            isinstance(output, dict) and output.get("retrieval_coverage") in RETRIEVAL_COVERAGE_VALUES,
            required=False,
        )

    required_checks = [check for check in checks if check["required"]]
    passed_checks = [check["name"] for check in required_checks if check["passed"]]
    failed_checks = [check["name"] for check in required_checks if not check["passed"]]
    optional_failures = [check["name"] for check in checks if not check["required"] and not check["passed"]]

    return {
        "eval_id": case.get("eval_id"),
        "category": case.get("category"),
        "task_type": task_type,
        "passed": not failed_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "optional_failures": optional_failures,
        "action_types": action_types,
        "robot_task_types": robot_task_types,
        "citation_ids": citation_ids,
        "confidence": output.get("confidence") if isinstance(output, dict) else None,
        "raw_output": output,
    }


def summarize_cases(records: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(records)
    strict_json_cases = sum(1 for record in records if record["strict_json_ok"])
    recovered_json_cases = sum(1 for record in records if record["recovered_json_ok"])
    passed_cases = sum(1 for record in records if record["passed"])
    confidence_values = [
        float(record["confidence"])
        for record in records
        if isinstance(record.get("confidence"), (int, float))
    ]
    confidence_on_pass = [
        float(record["confidence"])
        for record in records
        if record["passed"] and isinstance(record.get("confidence"), (int, float))
    ]
    confidence_on_fail = [
        float(record["confidence"])
        for record in records
        if not record["passed"] and isinstance(record.get("confidence"), (int, float))
    ]

    by_category: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["category"])].append(record)
    for category, items in sorted(grouped.items()):
        by_category[category] = {
            "cases": len(items),
            "passed": sum(1 for item in items if item["passed"]),
            "pass_rate": round(sum(1 for item in items if item["passed"]) / len(items), 4),
        }

    failed_check_counter: Counter[str] = Counter()
    optional_failure_counter: Counter[str] = Counter()
    request_errors = sum(1 for record in records if record.get("request_error"))
    for record in records:
        failed_check_counter.update(record["failed_checks"])
        optional_failure_counter.update(record["optional_failures"])

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0.0,
        "strict_json_rate": round(strict_json_cases / total_cases, 4) if total_cases else 0.0,
        "recovered_json_rate": round(recovered_json_cases / total_cases, 4) if total_cases else 0.0,
        "average_confidence": round(mean(confidence_values), 4) if confidence_values else None,
        "average_confidence_on_pass": round(mean(confidence_on_pass), 4) if confidence_on_pass else None,
        "average_confidence_on_fail": round(mean(confidence_on_fail), 4) if confidence_on_fail else None,
        "by_category": by_category,
        "request_errors": request_errors,
        "top_failed_checks": failed_check_counter.most_common(10),
        "top_optional_failures": optional_failure_counter.most_common(10),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    report_status = report.get("status", "completed")
    lines = [
        "# Fine-tuned Model Eval Summary",
        "",
        f"- status: `{report_status}`",
        f"- model: `{report['model']}`",
        f"- evaluated_at: `{report['evaluated_at']}`",
        f"- total_cases: `{summary['total_cases']}`",
        f"- passed_cases: `{summary['passed_cases']}`",
        f"- pass_rate: `{summary['pass_rate']}`",
        f"- strict_json_rate: `{summary['strict_json_rate']}`",
        f"- recovered_json_rate: `{summary['recovered_json_rate']}`",
        f"- request_errors: `{summary['request_errors']}`",
        "",
        "## Category Results",
        "",
        "| category | cases | passed | pass_rate |",
        "|---|---:|---:|---:|",
    ]

    for category, row in summary["by_category"].items():
        lines.append(f"| {category} | {row['cases']} | {row['passed']} | {row['pass_rate']} |")

    lines.extend(
        [
            "",
            "## Confidence",
            "",
            f"- average_confidence: `{summary['average_confidence']}`",
            f"- average_confidence_on_pass: `{summary['average_confidence_on_pass']}`",
            f"- average_confidence_on_fail: `{summary['average_confidence_on_fail']}`",
            "",
            "## Top Failed Checks",
            "",
        ]
    )

    if summary["top_failed_checks"]:
        for name, count in summary["top_failed_checks"]:
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Top Optional Failures", ""])
    if summary["top_optional_failures"]:
        for name, count in summary["top_optional_failures"]:
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Failed Cases", ""])
    failed_records = [record for record in report["cases"] if not record["passed"]]
    if not failed_records:
        lines.append("- 없음")
    else:
        for record in failed_records:
            lines.append(
                f"- `{record['eval_id']}` ({record['category']}): "
                f"{', '.join(record['failed_checks'])}"
            )

    return "\n".join(lines) + "\n"


def write_report(
    output_prefix: Path,
    *,
    model: str,
    system_prompt: str,
    temperature: float,
    eval_files: list[Path],
    records: list[dict[str, Any]],
    status: str,
) -> dict[str, Any]:
    summary = summarize_cases(records)
    report = {
        "schema_version": "fine_tuned_model_eval.v1",
        "status": status,
        "evaluated_at": utc_now_iso(),
        "model": model,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "eval_files": [path.as_posix() for path in eval_files],
        "summary": summary,
        "cases": records,
    }

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    jsonl_path = output_prefix.with_suffix(".jsonl")
    markdown_path = output_prefix.with_suffix(".md")

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"summary_json: {json_path.as_posix()}", flush=True)
    print(f"case_jsonl: {jsonl_path.as_posix()}", flush=True)
    print(f"summary_md: {markdown_path.as_posix()}", flush=True)
    print(f"pass_rate: {summary['pass_rate']}", flush=True)
    return report


def should_retry_openai_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if isinstance(exc, (APIError, APITimeoutError, RateLimitError)):
        return True
    return isinstance(exc, BadRequestError) and "could not parse the json body" in message


def create_completion_with_retry(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_completion_tokens: int,
    max_attempts: int = 3,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )
        except Exception as exc:  # pragma: no cover - depends on upstream API behavior
            last_error = exc
            if attempt >= max_attempts or not should_retry_openai_error(exc):
                break
            sleep_seconds = attempt * 2
            print(
                f"retrying_openai_request attempt={attempt + 1}/{max_attempts} "
                f"sleep_seconds={sleep_seconds} error={exc}",
                flush=True,
            )
            time.sleep(sleep_seconds)
    assert last_error is not None
    raise last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--eval-files", nargs="*", default=[str(path) for path in DEFAULT_EVAL_FILES])
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    parser.add_argument("--system-prompt-version", choices=sorted(SYSTEM_PROMPT_BY_VERSION), default="legacy")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--max-completion-tokens", type=int, default=1600)
    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not found.")
    if OpenAI is None:
        raise SystemExit("openai package is not installed in the current environment.")

    eval_files = [Path(path) for path in args.eval_files]
    system_prompt = SYSTEM_PROMPT_BY_VERSION[args.system_prompt_version]
    cases: list[dict[str, Any]] = []
    for eval_file in eval_files:
        cases.extend(load_jsonl(eval_file))
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    client = OpenAI(api_key=api_key)
    records: list[dict[str, Any]] = []
    output_prefix = Path(args.output_prefix)

    for index, case in enumerate(cases, start=1):
        user_message = build_user_message(case)
        try:
            completion = create_completion_with_retry(
                client,
                model=args.model,
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=args.temperature,
                max_completion_tokens=args.max_completion_tokens,
            )
        except Exception as exc:  # pragma: no cover - depends on upstream API behavior
            record = {
                "eval_id": case.get("eval_id"),
                "category": case.get("category"),
                "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                "prompt_index": index,
                "strict_json_ok": False,
                "recovered_json_ok": False,
                "parse_error": str(exc),
                "passed": False,
                "passed_checks": [],
                "failed_checks": ["request_error"],
                "optional_failures": [],
                "action_types": [],
                "robot_task_types": [],
                "citation_ids": [],
                "confidence": None,
                "request_error": True,
                "request": {
                    "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                    "user_message": user_message,
                },
                "response": {
                    "raw_content": "",
                    "parsed_output": None,
                    "response_id": None,
                    "usage": None,
                    "request_error": str(exc),
                },
            }
            records.append(record)
            print(
                f"[{index}/{len(cases)}] {case.get('eval_id')} "
                f"passed=False strict_json=False request_error={exc}",
                flush=True,
            )
            continue

        raw_content = completion.choices[0].message.content or ""
        parse_result = parse_response(raw_content)
        graded = grade_case(case, parse_result)
        usage = None
        if getattr(completion, "usage", None) is not None:
            usage_payload = completion.usage
            usage = usage_payload.model_dump() if hasattr(usage_payload, "model_dump") else dict(usage_payload)

        record = {
            "eval_id": case.get("eval_id"),
            "category": case.get("category"),
            "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
            "prompt_index": index,
            "strict_json_ok": parse_result["strict_json_ok"],
            "recovered_json_ok": parse_result["recovered_json_ok"],
            "parse_error": parse_result["parse_error"],
            "passed": graded["passed"],
            "passed_checks": graded["passed_checks"],
            "failed_checks": graded["failed_checks"],
            "optional_failures": graded["optional_failures"],
            "action_types": graded["action_types"],
            "robot_task_types": graded["robot_task_types"],
            "citation_ids": graded["citation_ids"],
            "confidence": graded["confidence"],
            "request_error": False,
            "request": {
                "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                "user_message": user_message,
            },
            "response": {
                "raw_content": raw_content,
                "parsed_output": graded["raw_output"],
                "response_id": completion.id,
                "usage": usage,
            },
        }
        records.append(record)
        print(
            f"[{index}/{len(cases)}] {case.get('eval_id')} "
            f"passed={record['passed']} strict_json={record['strict_json_ok']}",
            flush=True,
        )

    status = "completed_with_errors" if any(record.get("request_error") for record in records) else "completed"
    write_report(
        output_prefix,
        model=args.model,
        system_prompt=system_prompt,
        temperature=args.temperature,
        eval_files=eval_files,
        records=records,
        status=status,
    )


if __name__ == "__main__":
    main()
