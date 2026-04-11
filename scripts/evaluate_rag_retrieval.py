#!/usr/bin/env python3
"""Evaluate local RAG retrieval hit rate against a JSONL eval set."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI

from search_rag_index import DEFAULT_SCORE_CONFIG, load_index, search


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
            required = {"case_id", "query", "expected_chunk_ids"}
            missing = sorted(required - set(case))
            if missing:
                raise ValueError(f"line {line_number}: missing required fields {missing}")
            cases.append(case)
    return cases


def reciprocal_rank(result_ids: list[str], expected_ids: set[str]) -> float:
    for index, result_id in enumerate(result_ids, start=1):
        if result_id in expected_ids:
            return 1.0 / index
    return 0.0


def evaluate(
    index: dict[str, Any],
    cases: list[dict[str, Any]],
    default_top_k: int,
    client: OpenAI | None,
    vector_backend: str,
    chroma_path: str | None = None,
    chroma_collection_name: str | None = None,
    chroma_embedding_backend: str = "auto",
    score_config: dict[str, float] | None = None,
) -> dict[str, Any]:
    rows = []
    hits = 0
    mrr_total = 0.0

    for case in cases:
        top_k = int(case.get("top_k", default_top_k))
        filters = case.get("filters") or {}
        expected_ids = set(case["expected_chunk_ids"])
        results = search(
            index,
            case["query"],
            top_k,
            client=client,
            filters=filters,
            vector_backend=vector_backend,
            chroma_path=chroma_path,
            chroma_collection_name=chroma_collection_name,
            chroma_embedding_backend=chroma_embedding_backend,
            score_config=score_config,
        )
        result_ids = [item["id"] for item in results]
        hit = any(result_id in expected_ids for result_id in result_ids)
        rr = reciprocal_rank(result_ids, expected_ids)
        hits += int(hit)
        mrr_total += rr
        rows.append(
            {
                "case_id": case["case_id"],
                "category": case.get("category", ""),
                "hit": hit,
                "reciprocal_rank": round(rr, 4),
                "expected_chunk_ids": sorted(expected_ids),
                "result_ids": result_ids,
                "filters": filters,
            }
        )

    case_count = len(cases)
    return {
        "case_count": case_count,
        "hit_count": hits,
        "hit_rate": round(hits / case_count, 4) if case_count else 0.0,
        "mrr": round(mrr_total / case_count, 4) if case_count else 0.0,
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--eval-set", default="evals/rag_retrieval_eval_set.jsonl")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--use-vector", action="store_true", help="Use OpenAI embeddings if the index has document embeddings")
    parser.add_argument(
        "--vector-backend",
        choices=("keyword", "auto", "openai", "local", "chroma"),
        default="keyword",
        help="Retrieval mode for evaluation",
    )
    parser.add_argument("--chroma-path", default="artifacts/chroma_db/pepper_expert")
    parser.add_argument("--collection-name")
    parser.add_argument(
        "--chroma-embedding-backend",
        choices=("auto", "openai", "local"),
        default="auto",
        help="Embedding backend used by the Chroma collection",
    )
    parser.add_argument("--text-match-weight", type=float, default=DEFAULT_SCORE_CONFIG["text_match_weight"])
    parser.add_argument("--metadata-match-weight", type=float, default=DEFAULT_SCORE_CONFIG["metadata_match_weight"])
    parser.add_argument("--openai-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["openai_vector_weight"])
    parser.add_argument("--local-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["local_vector_weight"])
    parser.add_argument("--chroma-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["chroma_vector_weight"])
    parser.add_argument("--chroma-local-blend-weight", type=float, default=DEFAULT_SCORE_CONFIG["chroma_local_blend_weight"])
    parser.add_argument("--fail-under", type=float, default=1.0, help="Exit non-zero if hit_rate is below this value")
    args = parser.parse_args()

    index = load_index(Path(args.index))
    cases = load_eval_cases(Path(args.eval_set))

    client = None
    vector_backend = args.vector_backend
    if args.use_vector and vector_backend == "keyword":
        vector_backend = "auto"

    mode = "keyword"
    if vector_backend == "chroma":
        chroma_embedding_backend = args.chroma_embedding_backend
        if chroma_embedding_backend == "auto":
            chroma_embedding_backend = "openai" if os.environ.get("OPENAI_API_KEY") else "local"
        if chroma_embedding_backend == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                print("WARN OPENAI_API_KEY not found; cannot run OpenAI-backed Chroma evaluation", file=sys.stderr)
                sys.exit(1)
            client = OpenAI()
            mode = "chroma_openai_vector_keyword"
        else:
            if not index.get("local_vector_model"):
                print("WARN index has no local vector model; cannot run local-backed Chroma evaluation", file=sys.stderr)
                sys.exit(1)
            mode = "chroma_local_vector_keyword"
    elif vector_backend in {"auto", "openai"}:
        if not os.environ.get("OPENAI_API_KEY"):
            if vector_backend == "openai":
                print("WARN OPENAI_API_KEY not found; cannot run openai vector evaluation", file=sys.stderr)
                sys.exit(1)
            vector_backend = "local" if index.get("local_vector_model") else "keyword"
        elif not any("embedding" in document for document in index.get("documents", [])):
            if vector_backend == "openai":
                print("WARN index has no document embeddings; cannot run openai vector evaluation", file=sys.stderr)
                sys.exit(1)
            vector_backend = "local" if index.get("local_vector_model") else "keyword"
        else:
            client = OpenAI()
            mode = "openai_vector_keyword"

    if vector_backend == "local":
        if index.get("local_vector_model"):
            mode = "local_vector_keyword"
        else:
            print("WARN index has no local vector model; running keyword-only evaluation", file=sys.stderr)
            vector_backend = "keyword"
    score_config = {
        "text_match_weight": args.text_match_weight,
        "metadata_match_weight": args.metadata_match_weight,
        "openai_vector_weight": args.openai_vector_weight,
        "local_vector_weight": args.local_vector_weight,
        "chroma_vector_weight": args.chroma_vector_weight,
        "chroma_local_blend_weight": args.chroma_local_blend_weight,
    }

    report = evaluate(
        index,
        cases,
        args.top_k,
        client,
        vector_backend,
        chroma_path=args.chroma_path,
        chroma_collection_name=args.collection_name,
        chroma_embedding_backend=args.chroma_embedding_backend,
        score_config=score_config,
    )
    report["mode"] = mode
    report["index"] = args.index
    report["eval_set"] = args.eval_set
    report["score_config"] = score_config
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["hit_rate"] < args.fail_under:
        sys.exit(1)


if __name__ == "__main__":
    main()
