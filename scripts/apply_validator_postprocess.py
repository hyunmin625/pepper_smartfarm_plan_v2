#!/usr/bin/env python3
"""Apply policy_engine.output_validator to existing eval result jsonls
and compute validator-후 pass rates for each model path.

Eval cases do not carry explicit ValidatorContext flags (worker_present,
manual_override_active, path_degraded, etc.) — those are runtime-derived
features that exist only in the production zone_state. To approximate
them offline we scan `scenario`, `summary`, and `grading_notes` strings
for a fixed set of Korean/English keywords. This is not perfect but it
is the only way to run OV/HSV rules against the eval corpus without
rebuilding every case with a full zone_state.

Usage:
    python3 scripts/apply_validator_postprocess.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))

from evaluate_fine_tuned_model import (  # noqa: E402
    extract_chunk_ids,
    grade_case,
    parse_response,
    summarize_cases,
)
from policy_engine.output_validator import (  # noqa: E402
    ValidatorContext,
    apply_output_validator,
    load_rule_catalog,
)


EVAL_FILES = [
    "evals/expert_judgement_eval_set.jsonl",
    "evals/action_recommendation_eval_set.jsonl",
    "evals/forbidden_action_eval_set.jsonl",
    "evals/failure_response_eval_set.jsonl",
    "evals/robot_task_eval_set.jsonl",
    "evals/edge_case_eval_set.jsonl",
    "evals/seasonal_eval_set.jsonl",
    "evals/blind_holdout_eval_set.jsonl",
]

RUN_MANIFEST: dict[str, str] = {
    "A_ds_v11_ext200": "artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.jsonl",
    "A_ds_v11_blind50": "artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.jsonl",
    "B_gpt41_ext200": "artifacts/reports/frontier_rag_extended200.jsonl",
    "B_gpt41_blind50": "artifacts/reports/frontier_rag_blind50.jsonl",
    "C_gemini_ext200": "artifacts/reports/frontier_gemini_extended200.jsonl",
    "C_gemini_blind50": "artifacts/reports/frontier_gemini_blind50.jsonl",
    "D_m27_ext200": "artifacts/reports/frontier_minimax_m27_extended200.jsonl",
    "D_m27_blind50": "artifacts/reports/frontier_minimax_m27_blind50.jsonl",
}

OUTPUT_DIR = REPO_ROOT / "artifacts/reports/validator_postprocess"


# Keyword → context flag mapping. Scans are applied against the
# concatenation of scenario + summary + grading_notes, lowercased.
# Both English identifier-style tokens and Korean domain phrases are
# included because eval scenarios use both.
CONTEXT_KEYWORDS: list[tuple[str, str]] = [
    # worker presence
    ("worker_present", "worker_present"),
    ("worker present", "worker_present"),
    ("작업자가 lane", "worker_present"),
    ("작업자가 들어있", "worker_present"),
    ("lane 안에 있는데", "worker_present"),
    # manual override
    ("manual_override", "manual_override_active"),
    ("manual override", "manual_override_active"),
    ("수동 제어", "manual_override_active"),
    # safe mode already on
    ("safe_mode_active", "safe_mode_active"),
    ("safe mode active", "safe_mode_active"),
    # zone clearance uncertain
    ("zone clearance", "zone_clearance_uncertain"),
    ("zone_clearance_uncertain", "zone_clearance_uncertain"),
    ("reentry_pending", "zone_clearance_uncertain"),
    ("reentry pending", "zone_clearance_uncertain"),
    # aisle slip
    ("aisle_slip", "aisle_slip_hazard"),
    ("aisle slip", "aisle_slip_hazard"),
    # irrigation path degraded
    ("irrigation path", "irrigation_path_degraded"),
    ("irrigation_path", "irrigation_path_degraded"),
    ("관수 펌프 통신", "irrigation_path_degraded"),
    ("관수 메인 밸브 readback", "irrigation_path_degraded"),
    ("pump comm loss", "irrigation_path_degraded"),
    ("readback loss", "irrigation_path_degraded"),
    # source water
    ("source_water", "source_water_path_degraded"),
    ("source water", "source_water_path_degraded"),
    ("급액기", "source_water_path_degraded"),
    # dry room
    ("dry_room", "dry_room_path_degraded"),
    ("dry room", "dry_room_path_degraded"),
    ("건조실", "dry_room_path_degraded"),
    # climate control degraded
    ("climate_control_degraded", "climate_control_degraded"),
    ("climate path", "climate_control_degraded"),
    # rootzone sensor conflict
    ("rootzone sensor", "rootzone_sensor_conflict"),
    ("rootzone_sensor_conflict", "rootzone_sensor_conflict"),
    ("근권 센서 충돌", "rootzone_sensor_conflict"),
    ("drain sensor stale", "rootzone_sensor_conflict"),
    ("drain sensor missing", "rootzone_sensor_conflict"),
]


def build_validator_context(case: dict[str, Any]) -> ValidatorContext:
    input_state = case.get("input_state") or {}
    task_type = str(case.get("task_type") or case.get("category") or "unknown_task")
    scenario = str(case.get("scenario") or "")
    summary = str(input_state.get("summary") or "")
    grading_notes = str(case.get("grading_notes") or "")
    haystack = " ".join([scenario, summary, grading_notes]).lower()

    flags: dict[str, bool] = {}
    for keyword, flag in CONTEXT_KEYWORDS:
        if keyword.lower() in haystack:
            flags[flag] = True

    raw_retrieved = case.get("retrieved_context")
    retrieved_tuple: tuple[str, ...]
    if isinstance(raw_retrieved, list):
        retrieved_tuple = tuple(
            item for item in raw_retrieved if isinstance(item, str)
        )
    else:
        retrieved_tuple = ()

    requires_citations = bool(case.get("expected", {}).get("must_include_citations"))

    return ValidatorContext(
        farm_id=str(input_state.get("farm_id") or "demo-farm"),
        zone_id=str(input_state.get("zone_id") or "unknown-zone"),
        task_type=task_type,
        summary=summary,
        requires_citations=requires_citations,
        worker_present=flags.get("worker_present", False),
        manual_override_active=flags.get("manual_override_active", False),
        safe_mode_active=flags.get("safe_mode_active", False),
        zone_clearance_uncertain=flags.get("zone_clearance_uncertain", False),
        aisle_slip_hazard=flags.get("aisle_slip_hazard", False),
        irrigation_path_degraded=flags.get("irrigation_path_degraded", False),
        source_water_path_degraded=flags.get("source_water_path_degraded", False),
        dry_room_path_degraded=flags.get("dry_room_path_degraded", False),
        climate_control_degraded=flags.get("climate_control_degraded", False),
        rootzone_sensor_conflict=flags.get("rootzone_sensor_conflict", False),
        rootzone_control_interpretable=not flags.get("rootzone_sensor_conflict", False),
        core_climate_interpretable=not flags.get("climate_control_degraded", False),
        retrieved_context=retrieved_tuple,
        proposed_action=str(case.get("proposed_action") or ""),
    )


def load_eval_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for ef in EVAL_FILES:
        path = REPO_ROOT / ef
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                c = json.loads(line)
                cases[c["eval_id"]] = c
    return cases


def apply_validator_to_run(
    label: str,
    jsonl_path: Path,
    eval_cases: dict[str, dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if not jsonl_path.exists():
        return None
    with jsonl_path.open("r", encoding="utf-8") as f:
        original_records = [json.loads(line) for line in f]

    raw_records: list[dict[str, Any]] = []
    validated_records: list[dict[str, Any]] = []
    context_flag_counter: dict[str, int] = {}

    for rec in original_records:
        case = eval_cases.get(rec["eval_id"])
        if not case:
            continue

        # Rebuild parse_result from raw_content so the strip_thinking_tags
        # fix is consistently applied.
        raw = (rec.get("response") or {}).get("raw_content") or ""
        parse_result = parse_response(raw) if raw else {
            "strict_json_ok": rec.get("strict_json_ok", False),
            "recovered_json_ok": rec.get("recovered_json_ok", False),
            "json_object_ok": bool((rec.get("response") or {}).get("parsed_output")),
            "parse_error": rec.get("parse_error"),
            "parsed_output": (rec.get("response") or {}).get("parsed_output"),
        }

        # Effective retrieved ids for the citations_in_context check
        user_message = (rec.get("request") or {}).get("user_message")
        effective_ids: list[str] | None = None
        if isinstance(user_message, str):
            try:
                um = json.loads(user_message)
                rc = um.get("input", {}).get("retrieved_context")
                effective_ids = extract_chunk_ids(rc)
            except Exception:
                effective_ids = None

        # Raw grading (no validator)
        raw_graded = grade_case(case, parse_result, effective_retrieved_ids=effective_ids)

        # Build a context approximation
        context = build_validator_context(case)
        for field_name in (
            "worker_present",
            "manual_override_active",
            "safe_mode_active",
            "zone_clearance_uncertain",
            "irrigation_path_degraded",
            "source_water_path_degraded",
            "dry_room_path_degraded",
            "rootzone_sensor_conflict",
            "climate_control_degraded",
        ):
            if getattr(context, field_name):
                context_flag_counter[field_name] = context_flag_counter.get(field_name, 0) + 1

        # Apply validator to parsed_output
        parsed_output = parse_result.get("parsed_output")
        if isinstance(parsed_output, dict):
            validator_input = dict(parsed_output)
            try:
                result = apply_output_validator(validator_input, context, rule_catalog=catalog)
                validated_output = result.output
            except Exception as exc:
                # If the validator rejects the output entirely, treat as no-op
                validated_output = parsed_output
        else:
            validated_output = parsed_output

        # Re-grade with validator-applied output
        validated_parse = dict(parse_result)
        validated_parse["parsed_output"] = validated_output
        validated_graded = grade_case(case, validated_parse, effective_retrieved_ids=effective_ids)

        raw_records.append({
            "eval_id": rec["eval_id"],
            "category": rec.get("category"),
            "task_type": rec.get("task_type"),
            "strict_json_ok": parse_result.get("strict_json_ok", False),
            "recovered_json_ok": parse_result.get("recovered_json_ok", False),
            "parse_error": parse_result.get("parse_error"),
            "passed": raw_graded["passed"],
            "passed_checks": raw_graded["passed_checks"],
            "failed_checks": raw_graded["failed_checks"],
            "optional_failures": raw_graded["optional_failures"],
            "action_types": raw_graded["action_types"],
            "robot_task_types": raw_graded["robot_task_types"],
            "citation_ids": raw_graded["citation_ids"],
            "confidence": raw_graded["confidence"],
            "request_error": rec.get("request_error", False),
        })
        validated_records.append({
            "eval_id": rec["eval_id"],
            "category": rec.get("category"),
            "task_type": rec.get("task_type"),
            "strict_json_ok": parse_result.get("strict_json_ok", False),
            "recovered_json_ok": parse_result.get("recovered_json_ok", False),
            "parse_error": parse_result.get("parse_error"),
            "passed": validated_graded["passed"],
            "passed_checks": validated_graded["passed_checks"],
            "failed_checks": validated_graded["failed_checks"],
            "optional_failures": validated_graded["optional_failures"],
            "action_types": validated_graded["action_types"],
            "robot_task_types": validated_graded["robot_task_types"],
            "citation_ids": validated_graded["citation_ids"],
            "confidence": validated_graded["confidence"],
            "request_error": rec.get("request_error", False),
        })

    raw_summary = summarize_cases(raw_records)
    validated_summary = summarize_cases(validated_records)
    return {
        "label": label,
        "source": jsonl_path.as_posix(),
        "n_cases": len(raw_records),
        "context_flag_counts": context_flag_counter,
        "raw_summary": raw_summary,
        "validated_summary": validated_summary,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    eval_cases = load_eval_cases()
    print(f"loaded {len(eval_cases)} eval cases")
    catalog = load_rule_catalog()
    print(f"loaded {len(catalog)} validator rules")
    print()

    rows: list[dict[str, Any]] = []
    for label, src in RUN_MANIFEST.items():
        path = REPO_ROOT / src
        r = apply_validator_to_run(label, path, eval_cases, catalog)
        if r is None:
            print(f"[skip] {label}: {src} missing")
            continue
        raw = r["raw_summary"]
        val = r["validated_summary"]
        print(
            f"[{label}] raw={raw['pass_rate']:.3f}  "
            f"validator={val['pass_rate']:.3f}  "
            f"Δ={val['pass_rate']-raw['pass_rate']:+.3f}  "
            f"hs_raw={raw['hard_safety_violation_cases']}→{val['hard_safety_violation_cases']}  "
            f"crit_raw={len(raw['category_floors']['critical'])}→{len(val['category_floors']['critical'])}"
        )
        rows.append(r)
        out_path = OUTPUT_DIR / f"{label}.json"
        out_path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    (OUTPUT_DIR / "validator_postprocess_index.json").write_text(
        json.dumps({"runs": rows}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print()
    print(f"wrote {len(rows)} validator-postprocess summaries to {OUTPUT_DIR.as_posix()}/")


if __name__ == "__main__":
    main()
