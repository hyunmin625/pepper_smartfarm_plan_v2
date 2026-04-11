#!/usr/bin/env python3
"""Compare keyword retrieval against a candidate retrieval backend."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI

from evaluate_rag_retrieval import evaluate, load_eval_cases
from search_rag_index import DEFAULT_SCORE_CONFIG, load_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--eval-set", default="evals/rag_retrieval_eval_set.jsonl")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--candidate-backend",
        choices=("local", "chroma"),
        default="local",
        help="Candidate backend to compare against keyword retrieval",
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
    args = parser.parse_args()

    index = load_index(Path(args.index))
    cases = load_eval_cases(Path(args.eval_set))
    score_config = {
        "text_match_weight": args.text_match_weight,
        "metadata_match_weight": args.metadata_match_weight,
        "openai_vector_weight": args.openai_vector_weight,
        "local_vector_weight": args.local_vector_weight,
        "chroma_vector_weight": args.chroma_vector_weight,
        "chroma_local_blend_weight": args.chroma_local_blend_weight,
    }

    baseline = evaluate(index, cases, args.top_k, client=None, vector_backend="keyword", score_config=score_config)
    candidate_client = None
    if args.candidate_backend == "chroma":
        chroma_embedding_backend = args.chroma_embedding_backend
        if chroma_embedding_backend == "auto":
            chroma_embedding_backend = "openai" if os.environ.get("OPENAI_API_KEY") else "local"
        if chroma_embedding_backend == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                raise SystemExit("OPENAI_API_KEY not found. OpenAI-backed Chroma comparison requires query embeddings.")
            candidate_client = OpenAI()
    candidate = evaluate(
        index,
        cases,
        args.top_k,
        client=candidate_client,
        vector_backend=args.candidate_backend,
        chroma_path=args.chroma_path,
        chroma_collection_name=args.collection_name,
        chroma_embedding_backend=args.chroma_embedding_backend,
        score_config=score_config,
    )

    baseline_rows = {row["case_id"]: row for row in baseline["cases"]}
    candidate_rows = {row["case_id"]: row for row in candidate["cases"]}

    changed_cases = []
    for case_id in sorted(baseline_rows):
        base_row = baseline_rows[case_id]
        candidate_row = candidate_rows[case_id]
        if (
            base_row["result_ids"] != candidate_row["result_ids"]
            or base_row["reciprocal_rank"] != candidate_row["reciprocal_rank"]
        ):
            changed_cases.append(
                {
                    "case_id": case_id,
                    "baseline_result_ids": base_row["result_ids"],
                    "candidate_result_ids": candidate_row["result_ids"],
                    "baseline_rr": base_row["reciprocal_rank"],
                    "candidate_rr": candidate_row["reciprocal_rank"],
                }
            )

    report = {
        "baseline_mode": "keyword",
        "candidate_mode": args.candidate_backend,
        "baseline_hit_rate": baseline["hit_rate"],
        "candidate_hit_rate": candidate["hit_rate"],
        "baseline_mrr": baseline["mrr"],
        "candidate_mrr": candidate["mrr"],
        "delta_hit_rate": round(candidate["hit_rate"] - baseline["hit_rate"], 4),
        "delta_mrr": round(candidate["mrr"] - baseline["mrr"], 4),
        "score_config": score_config,
        "changed_case_count": len(changed_cases),
        "changed_cases": changed_cases,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))



if __name__ == "__main__":
    main()
