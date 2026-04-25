#!/usr/bin/env python3
"""Benchmark retriever backends against the production retriever factory.

Runs the same recall@k / MRR / any_hit@k metrics that Phase F measured, but
uses the production retriever factory in
``llm_orchestrator.retriever_vector.create_retriever`` so the numbers reflect
what ``ops-api`` actually instantiates at runtime.

Eval corpus (default):

- ``evals/rag_retrieval_eval_set.jsonl``         (110 cases)
- ``evals/rag_stage_retrieval_eval_set.jsonl``   ( 16 cases)

Each case carries ``query``, ``expected_chunk_ids``, optional ``top_k``
(default 5) and optional ``category``. We score every chunk id in the
expected set as a hit and compute:

- recall@k:   |hits ∩ expected| / |expected|
- any_hit@k:  1 if any expected id appears in top-k else 0
- MRR:        1 / rank of first expected hit (0 if none)

The default retriever set is zero-cost and does not issue OpenAI embedding
queries. Include ``openai`` or ``hybrid`` explicitly and set
``OPENAI_LIVE_RETRIEVER_SMOKE=1`` when a live API-backed benchmark is intended.

Writes a markdown + JSON report to ``artifacts/reports/``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from llm_orchestrator.retriever_vector import create_retriever  # noqa: E402


LIVE_OPENAI_RETRIEVER_TYPES = {"openai", "hybrid"}


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def load_cases(paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if "query" not in row or "expected_chunk_ids" not in row:
                    raise ValueError(
                        f"{path}:{line_number} missing query/expected_chunk_ids"
                    )
                row.setdefault("case_id", f"{path.stem}-{line_number}")
                row.setdefault("category", "uncategorized")
                row.setdefault("top_k", 5)
                row["_source"] = path.name
                cases.append(row)
    return cases


def reciprocal_rank(result_ids: list[str], expected_ids: set[str]) -> float:
    for index, result_id in enumerate(result_ids, start=1):
        if result_id in expected_ids:
            return 1.0 / index
    return 0.0


def evaluate_retriever(
    name: str,
    retriever: Any,
    cases: list[dict[str, Any]],
    *,
    k: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_recall = 0.0
    total_any = 0
    total_mrr = 0.0
    per_category: dict[str, dict[str, float]] = defaultdict(
        lambda: {"recall_sum": 0.0, "any_sum": 0, "mrr_sum": 0.0, "count": 0}
    )
    started = time.monotonic()

    for case in cases:
        expected_ids = set(case["expected_chunk_ids"])
        if not expected_ids:
            continue
        top_k = max(k, int(case.get("top_k", k)))
        try:
            hits = retriever.search(
                query=str(case["query"]),
                task_type=str(case.get("category", "")),
                limit=top_k,
            )
        except Exception as exc:  # pragma: no cover - surfaces backend failures
            hits = []
            case_note = f"retrieval_error: {exc}"
        else:
            case_note = ""

        top = hits[:k]
        result_ids = [h.chunk_id for h in top]
        overlap = expected_ids.intersection(result_ids)
        recall = len(overlap) / len(expected_ids)
        any_hit = 1 if overlap else 0
        rr = reciprocal_rank(result_ids, expected_ids)

        total_recall += recall
        total_any += any_hit
        total_mrr += rr
        cat = str(case.get("category", "uncategorized"))
        per_category[cat]["recall_sum"] += recall
        per_category[cat]["any_sum"] += any_hit
        per_category[cat]["mrr_sum"] += rr
        per_category[cat]["count"] += 1

        rows.append(
            {
                "case_id": case.get("case_id"),
                "category": cat,
                "expected_count": len(expected_ids),
                "top_ids": result_ids,
                "recall@k": round(recall, 4),
                "any_hit": any_hit,
                "rr": round(rr, 4),
                "note": case_note,
            }
        )

    elapsed = time.monotonic() - started
    case_count = sum(1 for c in cases if c["expected_chunk_ids"])

    categories_out: dict[str, dict[str, float]] = {}
    for cat, agg in per_category.items():
        n = agg["count"]
        if n == 0:
            continue
        categories_out[cat] = {
            "count": n,
            "recall@k": round(agg["recall_sum"] / n, 4),
            "any_hit@k": round(agg["any_sum"] / n, 4),
            "MRR": round(agg["mrr_sum"] / n, 4),
        }

    return {
        "name": name,
        "k": k,
        "case_count": case_count,
        "elapsed_sec": round(elapsed, 2),
        "avg_recall@k": round(total_recall / case_count, 4) if case_count else 0.0,
        "avg_any_hit@k": round(total_any / case_count, 4) if case_count else 0.0,
        "MRR": round(total_mrr / case_count, 4) if case_count else 0.0,
        "categories": categories_out,
        "per_case": rows,
    }


def render_markdown(results: list[dict[str, Any]], *, k: int, case_count: int) -> str:
    lines: list[str] = []
    lines.append("# Retriever benchmark")
    lines.append("")
    lines.append(f"- eval case count: **{case_count}**")
    lines.append(f"- top-k: **{k}**")
    lines.append(f"- retrievers: {', '.join(r['name'] for r in results)}")
    lines.append("")

    lines.append("## Aggregate")
    lines.append("")
    lines.append("| retriever | case_count | recall@k | any_hit@k | MRR | elapsed_sec |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in results:
        lines.append(
            f"| **{r['name']}** | {r['case_count']} | "
            f"{r['avg_recall@k']:.4f} | {r['avg_any_hit@k']:.4f} | "
            f"{r['MRR']:.4f} | {r['elapsed_sec']:.2f} |"
        )
    lines.append("")

    if results:
        names = {str(r["name"]) for r in results}
        best = max(
            results,
            key=lambda r: (
                float(r["avg_recall@k"]),
                float(r["MRR"]),
                float(r["avg_any_hit@k"]),
            ),
        )
        lines.append("## Interpretation")
        lines.append("")
        lines.append(
            f"- Best aggregate recall@{k}: **{best['name']}** "
            f"({best['avg_recall@k']:.4f}, MRR {best['MRR']:.4f})."
        )
        if "openai" not in names and "hybrid" not in names:
            lines.append(
                "- This run did not instantiate OpenAI-backed retrievers, "
                "so it makes no live embedding query and spends no API quota."
            )
        lines.append(
            "- This 126-case RAG eval is token-rich and corpus-oriented; "
            "use it as a runtime retriever regression check, not as the sole "
            "replacement for the Phase F decision-eval retrieval benchmark."
        )
        if str(best["name"]) == "keyword":
            lines.append(
                "- Cost-free runtime default should remain `keyword` until a "
                "local semantic or hybrid candidate beats it on both this "
                "suite and the safety-oriented decision-eval slices."
            )
        elif str(best["name"]) in {"local_embed", "local_hybrid", "tfidf"}:
            lines.append(
                "- The best backend in this run has zero API cost, so it is a "
                "candidate for runtime default after ops-api smoke validation."
            )
        else:
            lines.append(
                "- The best backend in this run may use a live external query; "
                "keep it explicit opt-in when API cost or quota is a concern."
            )
        lines.append("")

    categories = sorted(
        {cat for r in results for cat in r["categories"].keys()}
    )
    if categories:
        lines.append("## Per-category recall@k")
        lines.append("")
        header = "| category | n |"
        divider = "|---|---:|"
        for r in results:
            header += f" {r['name']} |"
            divider += "---:|"
        lines.append(header)
        lines.append(divider)
        for cat in categories:
            counts = [
                r["categories"].get(cat, {}).get("count", 0) for r in results
            ]
            n = max(counts) if counts else 0
            row = f"| {cat} | {n} |"
            for r in results:
                cell = r["categories"].get(cat)
                if cell is None:
                    row += " — |"
                else:
                    row += f" {cell['recall@k']:.3f} |"
            lines.append(row)
        lines.append("")

    # Winner analysis
    if len(results) >= 2:
        lines.append("## Head-to-head winners (by category)")
        lines.append("")
        lines.append("| category | n | best retriever | recall@k | runner-up | recall@k |")
        lines.append("|---|---:|---|---:|---|---:|")
        for cat in categories:
            scored = []
            for r in results:
                cell = r["categories"].get(cat)
                if cell:
                    scored.append((r["name"], cell["recall@k"], cell["count"]))
            if len(scored) < 2:
                continue
            scored.sort(key=lambda x: -x[1])
            best = scored[0]
            runner = scored[1]
            lines.append(
                f"| {cat} | {best[2]} | **{best[0]}** | {best[1]:.3f} | "
                f"{runner[0]} | {runner[1]:.3f} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-files",
        nargs="+",
        default=[
            "evals/rag_retrieval_eval_set.jsonl",
            "evals/rag_stage_retrieval_eval_set.jsonl",
        ],
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--retrievers",
        nargs="+",
        default=["keyword", "tfidf", "local_embed", "local_hybrid"],
        choices=[
            "keyword",
            "tfidf",
            "local_embed",
            "local_hybrid",
            "openai",
            "hybrid",
        ],
    )
    parser.add_argument(
        "--rag-index-path",
        default="artifacts/rag_index/pepper_expert_with_farm_case_index.json",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/reports/hybrid_retriever_benchmark.json",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/reports/hybrid_retriever_benchmark.md",
    )
    args = parser.parse_args()

    eval_paths = [REPO_ROOT / p for p in args.eval_files]
    for path in eval_paths:
        if not path.exists():
            print(f"[benchmark] missing eval file: {path}", file=sys.stderr)
            return 2

    cases = load_cases(eval_paths)
    case_count = len(cases)
    print(f"[benchmark] loaded {case_count} cases from {len(eval_paths)} file(s)")

    live_openai_requested = any(
        rtype in LIVE_OPENAI_RETRIEVER_TYPES for rtype in args.retrievers
    )
    if live_openai_requested and not _env_truthy("OPENAI_LIVE_RETRIEVER_SMOKE"):
        print(
            "[benchmark] refusing OpenAI-backed live query; set "
            "OPENAI_LIVE_RETRIEVER_SMOKE=1 to run openai/hybrid retrievers",
            file=sys.stderr,
        )
        return 2

    retriever_objs: list[tuple[str, Any]] = []
    for rtype in args.retrievers:
        print(f"[benchmark] instantiating retriever: {rtype}")
        started = time.monotonic()
        retriever = create_retriever(rtype, rag_index_path=args.rag_index_path)
        print(
            f"[benchmark]   ready in {time.monotonic() - started:.2f}s; "
            f"rows={len(getattr(retriever, 'rows', []) or [])}"
        )
        retriever_objs.append((rtype, retriever))

    results: list[dict[str, Any]] = []
    for name, retriever in retriever_objs:
        print(f"[benchmark] evaluating {name} ...")
        result = evaluate_retriever(name, retriever, cases, k=args.top_k)
        print(
            f"[benchmark]   recall@{args.top_k}={result['avg_recall@k']:.4f} "
            f"any_hit@{args.top_k}={result['avg_any_hit@k']:.4f} "
            f"MRR={result['MRR']:.4f} ({result['elapsed_sec']:.1f}s)"
        )
        results.append(result)

    out_json = REPO_ROOT / args.output_json
    out_md = REPO_ROOT / args.output_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "k": args.top_k,
        "case_count": case_count,
        "eval_files": [str(p.relative_to(REPO_ROOT)) for p in eval_paths],
        "retrievers": args.retrievers,
        "rag_index_path": args.rag_index_path,
        "results": results,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    out_md.write_text(
        render_markdown(results, k=args.top_k, case_count=case_count)
    )
    print(f"[benchmark] wrote {out_json.relative_to(REPO_ROOT)}")
    print(f"[benchmark] wrote {out_md.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
