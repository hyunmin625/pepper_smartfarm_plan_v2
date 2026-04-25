#!/usr/bin/env python3
"""Validate zero-cost retriever recall against the frozen local eval suite."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark_hybrid_retriever import (  # noqa: E402
    LIVE_OPENAI_RETRIEVER_TYPES,
    evaluate_retriever,
    load_cases,
    render_markdown,
)
from llm_orchestrator.retriever_vector import create_retriever  # noqa: E402


DEFAULT_EVAL_FILES = [
    "evals/rag_retrieval_eval_set.jsonl",
    "evals/rag_stage_retrieval_eval_set.jsonl",
]
DEFAULT_THRESHOLDS = {
    "keyword": 0.90,
    "local_hybrid": 0.85,
}


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-file", action="append", default=None)
    parser.add_argument("--retriever", action="append", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rag-index-path", default="artifacts/rag_index/pepper_expert_with_farm_case_index.json")
    parser.add_argument("--min-keyword-recall", type=float, default=DEFAULT_THRESHOLDS["keyword"])
    parser.add_argument("--min-local-hybrid-recall", type=float, default=DEFAULT_THRESHOLDS["local_hybrid"])
    parser.add_argument("--output-json", default="artifacts/reports/zero_cost_retriever_regression.json")
    parser.add_argument("--output-md", default="artifacts/reports/zero_cost_retriever_regression.md")
    args = parser.parse_args()

    eval_files = args.eval_file or DEFAULT_EVAL_FILES
    retriever_names = args.retriever or ["keyword", "local_hybrid"]
    live_requested = any(name in LIVE_OPENAI_RETRIEVER_TYPES for name in retriever_names)
    if live_requested and not _env_truthy("OPENAI_LIVE_RETRIEVER_SMOKE"):
        print(
            "ERROR refusing OpenAI-backed live retriever query; set OPENAI_LIVE_RETRIEVER_SMOKE=1 to opt in",
            file=sys.stderr,
        )
        return 2

    eval_paths = [REPO_ROOT / path for path in eval_files]
    cases = load_cases(eval_paths)
    thresholds = {
        "keyword": args.min_keyword_recall,
        "local_hybrid": args.min_local_hybrid_recall,
    }
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    started = time.monotonic()

    for retriever_name in retriever_names:
        print(f"[retriever-regression] evaluating {retriever_name}")
        retriever = create_retriever(retriever_name, rag_index_path=args.rag_index_path)
        result = evaluate_retriever(retriever_name, retriever, cases, k=args.top_k)
        threshold = thresholds.get(retriever_name)
        if threshold is not None and result["avg_recall@k"] < threshold:
            failures.append(
                f"{retriever_name} recall@{args.top_k} {result['avg_recall@k']:.4f} < {threshold:.4f}"
            )
        results.append(result)
        print(
            f"[retriever-regression] {retriever_name} recall@{args.top_k}="
            f"{result['avg_recall@k']:.4f}"
        )

    payload = {
        "status": "ok" if not failures else "failed",
        "elapsed_sec": round(time.monotonic() - started, 3),
        "case_count": len(cases),
        "top_k": args.top_k,
        "retrievers": retriever_names,
        "thresholds": thresholds,
        "failures": failures,
        "results": results,
        "openai_live_opt_in": _env_truthy("OPENAI_LIVE_RETRIEVER_SMOKE"),
    }
    output_json = REPO_ROOT / args.output_json
    output_md = REPO_ROOT / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(results, k=args.top_k, case_count=len(cases)), encoding="utf-8")

    print(json.dumps({"status": payload["status"], "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
