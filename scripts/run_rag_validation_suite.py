#!/usr/bin/env python3
"""Run the common and stage-specific RAG retrieval validation suites together."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evaluate_rag_retrieval import evaluate, load_eval_cases
from search_rag_index import load_index


def build_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# RAG Validation Suite Summary",
        "",
        "## Scope",
        "",
        f"- index: `{summary['index']}`",
        f"- fail_under: `{summary['fail_under']}`",
        f"- suites: `{', '.join(summary['suite_order'])}`",
        f"- modes: `{', '.join(summary['mode_order'])}`",
        "",
        "## Results",
        "",
        "| Suite | Mode | Cases | Hit Rate | MRR | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for suite_name in summary["suite_order"]:
        suite = summary["suites"][suite_name]
        for mode in summary["mode_order"]:
            result = suite["modes"][mode]
            status = "PASS" if result["hit_rate"] >= summary["fail_under"] else "FAIL"
            lines.append(
                f"| {suite_name} | {mode} | {result['case_count']} | "
                f"{result['hit_rate']:.4f} | {result['mrr']:.4f} | {status} |"
            )

    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            "| Mode | Cases | Hit Rate | MRR |",
            "|---|---:|---:|---:|",
        ]
    )

    for mode in summary["mode_order"]:
        aggregate = summary["aggregates"][mode]
        lines.append(
            f"| {mode} | {aggregate['case_count']} | {aggregate['hit_rate']:.4f} | {aggregate['mrr']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Eval Sets",
            "",
            f"- common: `{summary['suites']['common']['eval_set']}`",
            f"- stage: `{summary['suites']['stage']['eval_set']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def aggregate_mode_results(reports: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = sum(report["case_count"] for report in reports)
    total_hits = sum(report["hit_count"] for report in reports)
    weighted_mrr = sum(report["mrr"] * report["case_count"] for report in reports)
    return {
        "case_count": total_cases,
        "hit_count": total_hits,
        "hit_rate": round(total_hits / total_cases, 4) if total_cases else 0.0,
        "mrr": round(weighted_mrr / total_cases, 4) if total_cases else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--common-eval-set", default="evals/rag_retrieval_eval_set.jsonl")
    parser.add_argument("--stage-eval-set", default="evals/rag_stage_retrieval_eval_set.jsonl")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--modes",
        default="keyword,local",
        help="Comma-separated retrieval modes to run. Supported: keyword,local",
    )
    parser.add_argument("--fail-under", type=float, default=1.0)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    requested_modes = [mode.strip() for mode in args.modes.split(",") if mode.strip()]
    invalid_modes = sorted(set(requested_modes) - {"keyword", "local"})
    if invalid_modes:
        raise SystemExit(f"unsupported modes: {', '.join(invalid_modes)}")
    if not requested_modes:
        raise SystemExit("at least one mode is required")

    index = load_index(Path(args.index))
    if "local" in requested_modes and not index.get("local_vector_model"):
        raise SystemExit("index has no local vector model; cannot run local mode")

    suite_paths = {
        "common": args.common_eval_set,
        "stage": args.stage_eval_set,
    }
    suites: dict[str, Any] = {}
    mode_reports: dict[str, list[dict[str, Any]]] = {mode: [] for mode in requested_modes}
    failures: list[str] = []

    for suite_name, eval_path in suite_paths.items():
        cases = load_eval_cases(Path(eval_path))
        suite_record = {
            "eval_set": eval_path,
            "case_count": len(cases),
            "modes": {},
        }
        for mode in requested_modes:
            report = evaluate(
                index=index,
                cases=cases,
                default_top_k=args.top_k,
                client=None,
                vector_backend=mode,
                score_config=None,
            )
            report["mode"] = mode
            report["suite"] = suite_name
            report["eval_set"] = eval_path
            suite_record["modes"][mode] = report
            mode_reports[mode].append(report)
            if report["hit_rate"] < args.fail_under:
                failures.append(f"{suite_name}:{mode}={report['hit_rate']}")
        suites[suite_name] = suite_record

    summary = {
        "index": args.index,
        "fail_under": args.fail_under,
        "suite_order": list(suite_paths.keys()),
        "mode_order": requested_modes,
        "suites": suites,
        "aggregates": {mode: aggregate_mode_results(reports) for mode, reports in mode_reports.items()},
    }

    json_payload = json.dumps(summary, ensure_ascii=False, indent=2)
    print(json_payload)

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json_payload + "\n", encoding="utf-8")

    if args.output_md:
        output_md = Path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown_report(summary), encoding="utf-8")

    if failures:
        print("validation suite failed: " + ", ".join(failures), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
