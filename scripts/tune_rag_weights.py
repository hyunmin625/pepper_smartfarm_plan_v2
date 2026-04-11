#!/usr/bin/env python3
"""Grid-search retrieval weights for a selected backend."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI

from evaluate_rag_retrieval import evaluate, load_eval_cases
from search_rag_index import DEFAULT_SCORE_CONFIG, load_index


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--eval-set", default="evals/rag_retrieval_eval_set.jsonl")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--vector-backend", choices=("local", "chroma"), default="chroma")
    parser.add_argument("--chroma-path", default="artifacts/chroma_db/pepper_expert")
    parser.add_argument("--collection-name")
    parser.add_argument("--chroma-embedding-backend", choices=("auto", "openai", "local"), default="openai")
    parser.add_argument("--vector-weights", default="8,10,12,14,16")
    parser.add_argument("--chroma-local-blend-weights", default="0,2,4,6")
    parser.add_argument("--text-match-weight", type=float, default=DEFAULT_SCORE_CONFIG["text_match_weight"])
    parser.add_argument("--metadata-match-weight", type=float, default=DEFAULT_SCORE_CONFIG["metadata_match_weight"])
    parser.add_argument("--openai-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["openai_vector_weight"])
    parser.add_argument("--local-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["local_vector_weight"])
    parser.add_argument("--chroma-vector-weight", type=float, default=DEFAULT_SCORE_CONFIG["chroma_vector_weight"])
    parser.add_argument("--chroma-local-blend-weight", type=float, default=DEFAULT_SCORE_CONFIG["chroma_local_blend_weight"])
    args = parser.parse_args()

    index = load_index(Path(args.index))
    cases = load_eval_cases(Path(args.eval_set))

    client = None
    if args.vector_backend == "chroma" and args.chroma_embedding_backend == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY not found. OpenAI-backed Chroma tuning requires query embeddings.")
        client = OpenAI()

    rows = []
    best = None
    blend_weights = parse_float_list(args.chroma_local_blend_weights)
    for vector_weight in parse_float_list(args.vector_weights):
        active_blend_weights = [args.chroma_local_blend_weight]
        if args.vector_backend == "chroma":
            active_blend_weights = blend_weights
        for blend_weight in active_blend_weights:
            score_config = {
                "text_match_weight": args.text_match_weight,
                "metadata_match_weight": args.metadata_match_weight,
                "openai_vector_weight": args.openai_vector_weight,
                "local_vector_weight": args.local_vector_weight,
                "chroma_vector_weight": args.chroma_vector_weight,
                "chroma_local_blend_weight": args.chroma_local_blend_weight,
            }
            if args.vector_backend == "local":
                score_config["local_vector_weight"] = vector_weight
            else:
                score_config["chroma_vector_weight"] = vector_weight
                score_config["chroma_local_blend_weight"] = blend_weight

            report = evaluate(
                index,
                cases,
                args.top_k,
                client=client,
                vector_backend=args.vector_backend,
                chroma_path=args.chroma_path,
                chroma_collection_name=args.collection_name,
                chroma_embedding_backend=args.chroma_embedding_backend,
                score_config=score_config,
            )
            row = {
                "vector_weight": vector_weight,
                "chroma_local_blend_weight": blend_weight if args.vector_backend == "chroma" else None,
                "hit_rate": report["hit_rate"],
                "mrr": report["mrr"],
            }
            rows.append(row)
            if best is None or row["mrr"] > best["mrr"] or (
                row["mrr"] == best["mrr"] and row["vector_weight"] < best["vector_weight"]
            ):
                best = row

    print(
        json.dumps(
            {
                "vector_backend": args.vector_backend,
                "chroma_embedding_backend": args.chroma_embedding_backend if args.vector_backend == "chroma" else None,
                "collection_name": args.collection_name if args.vector_backend == "chroma" else None,
                "base_score_config": {
                    "text_match_weight": args.text_match_weight,
                    "metadata_match_weight": args.metadata_match_weight,
                    "openai_vector_weight": args.openai_vector_weight,
                    "local_vector_weight": args.local_vector_weight,
                    "chroma_vector_weight": args.chroma_vector_weight,
                },
                "trials": rows,
                "best": best,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
