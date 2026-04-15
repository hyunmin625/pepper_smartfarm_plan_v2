#!/usr/bin/env python3
"""Regrade existing eval result jsonl files with the fixed grader + new aggregates.

Rebuilds case-level `passed/failed_checks` from the raw model outputs captured in
each record's `request.user_message` and `response.raw_content`, then runs the
expanded `summarize_cases` to produce per-check pass rates, hard-safety
violation counts, and category floor flags.

This is used when a grader change (e.g. the live-rag citations_in_context fix)
needs to be retroactively applied to runs that have already burned API budget.
Does not call any upstream model; purely offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluate_fine_tuned_model import (
    extract_chunk_ids,
    grade_case,
    parse_response,
    summarize_cases,
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

# run_label: input_jsonl
RUN_MANIFEST: dict[str, str] = {
    # A ds_v11 frozen fine-tune (static retrieval)
    "A_ds_v11_ext200": "artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.jsonl",
    "A_ds_v11_blind50": "artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.jsonl",
    # B gpt-4.1 frontier+RAG (static retrieval with chunk_lookup inline)
    "B_gpt41_ext200": "artifacts/reports/frontier_rag_extended200.jsonl",
    "B_gpt41_blind50": "artifacts/reports/frontier_rag_blind50.jsonl",
    # C gemini-2.5-flash (static retrieval with chunk_lookup inline)
    "C_gemini_ext200": "artifacts/reports/frontier_gemini_extended200.jsonl",
    "C_gemini_blind50": "artifacts/reports/frontier_gemini_blind50.jsonl",
    # D MiniMax-M2.7 (static retrieval with chunk_lookup inline)
    "D_m27_ext200": "artifacts/reports/frontier_minimax_m27_extended200.jsonl",
    "D_m27_blind50": "artifacts/reports/frontier_minimax_m27_blind50.jsonl",
    # C gemini live-rag
    "C_gemini_liverag_ext200": "artifacts/reports/frontier_gemini_liverag_extended200.jsonl",
    "C_gemini_liverag_blind50": "artifacts/reports/frontier_gemini_liverag_blind50.jsonl",
    # D m2.7 live-rag (blind50 중단됨 — 따로 처리)
    "D_m27_liverag_ext200": "artifacts/reports/frontier_minimax_m27_liverag_extended200.jsonl",
}

OUTPUT_DIR = Path("artifacts/reports/regrade")


def load_eval_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for ef in EVAL_FILES:
        path = Path(ef)
        if not path.exists():
            print(f"  [warn] eval file missing: {ef}")
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                c = json.loads(line)
                cases[c["eval_id"]] = c
    return cases


def regrade_run(label: str, jsonl_path: Path, eval_cases: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not jsonl_path.exists():
        return None
    with jsonl_path.open("r", encoding="utf-8") as f:
        original_records = [json.loads(line) for line in f]

    new_records: list[dict[str, Any]] = []
    unresolved = 0
    for rec in original_records:
        case = eval_cases.get(rec["eval_id"])
        if not case:
            unresolved += 1
            continue

        # Determine effective retrieved ids
        effective_ids: list[str] | None = None
        user_message = (rec.get("request") or {}).get("user_message")
        if isinstance(user_message, str):
            try:
                um = json.loads(user_message)
                rc = um.get("input", {}).get("retrieved_context")
                effective_ids = extract_chunk_ids(rc)
            except Exception:
                effective_ids = None

        # Reconstruct parse_result from raw_content. Prefer re-parsing so the
        # strip_thinking_tags fix also applies to the stored M2.7 outputs.
        raw = (rec.get("response") or {}).get("raw_content") or ""
        parse_result = parse_response(raw) if raw else {
            "strict_json_ok": rec.get("strict_json_ok", False),
            "recovered_json_ok": rec.get("recovered_json_ok", False),
            "json_object_ok": bool((rec.get("response") or {}).get("parsed_output")),
            "parse_error": rec.get("parse_error"),
            "parsed_output": (rec.get("response") or {}).get("parsed_output"),
        }

        graded = grade_case(
            case,
            parse_result,
            effective_retrieved_ids=effective_ids,
        )

        new_records.append({
            "eval_id": rec["eval_id"],
            "category": rec.get("category"),
            "task_type": rec.get("task_type"),
            "prompt_index": rec.get("prompt_index"),
            "strict_json_ok": parse_result.get("strict_json_ok", False),
            "recovered_json_ok": parse_result.get("recovered_json_ok", False),
            "parse_error": parse_result.get("parse_error"),
            "passed": graded["passed"],
            "passed_checks": graded["passed_checks"],
            "failed_checks": graded["failed_checks"],
            "optional_failures": graded["optional_failures"],
            "action_types": graded["action_types"],
            "robot_task_types": graded["robot_task_types"],
            "citation_ids": graded["citation_ids"],
            "confidence": graded["confidence"],
            "effective_retrieved_ids": effective_ids,
            "request_error": rec.get("request_error", False),
        })

    summary = summarize_cases(new_records)
    return {
        "label": label,
        "source": jsonl_path.as_posix(),
        "unresolved_eval_ids": unresolved,
        "summary": summary,
        "n_regraded": len(new_records),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    eval_cases = load_eval_cases()
    print(f"Loaded {len(eval_cases)} eval cases")
    print()

    results: dict[str, dict[str, Any]] = {}
    for label, src in RUN_MANIFEST.items():
        path = Path(src)
        result = regrade_run(label, path, eval_cases)
        if result is None:
            print(f"[skip] {label}: source missing ({src})")
            continue
        summary = result["summary"]
        print(
            f"[{label}] pass={summary['pass_rate']:.3f}"
            f" ({summary['passed_cases']}/{summary['total_cases']}) "
            f"strict_json={summary['strict_json_rate']:.3f} "
            f"hard_safety_viol={summary['hard_safety_violation_cases']} "
            f"floors_crit={len(summary['category_floors']['critical'])} "
            f"warn={len(summary['category_floors']['warn'])}"
        )
        results[label] = result

        # Write per-run summary
        out_path = OUTPUT_DIR / f"{label}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write combined index
    combined = {
        "schema_version": "regrade.v1",
        "runs": {k: v for k, v in results.items()},
    }
    (OUTPUT_DIR / "regrade_index.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print()
    print(f"Wrote {len(results)} regrade summaries to {OUTPUT_DIR.as_posix()}/")


if __name__ == "__main__":
    main()
