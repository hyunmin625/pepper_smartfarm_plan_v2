#!/usr/bin/env python3
"""Run simple keyword and metadata search over the local RAG index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SEARCH_FIELDS = (
    "growth_stage",
    "sensor_tags",
    "risk_tags",
    "operation_tags",
    "agent_use",
)


def load_index(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return [str(value).lower()]


def score_document(document: dict[str, Any], query_terms: list[str]) -> tuple[int, list[str]]:
    text = document["text"].lower()
    metadata = document.get("metadata", {})
    score = 0
    matches: list[str] = []

    for term in query_terms:
        if term in text:
            score += 2
            matches.append(f"text:{term}")
        for field in SEARCH_FIELDS:
            values = flatten(metadata.get(field))
            if term in values:
                score += 3
                matches.append(f"{field}:{term}")
    return score, matches


def search(index: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]:
    query_terms = [term.strip().lower() for term in query.replace(",", " ").split() if term.strip()]
    results = []
    for document in index["documents"]:
        score, matches = score_document(document, query_terms)
        if score <= 0:
            continue
        results.append(
            {
                "id": document["id"],
                "score": score,
                "matches": matches,
                "summary": document["text"].splitlines()[0],
                "metadata": document["metadata"],
            }
        )
    results.sort(key=lambda item: (-item["score"], item["id"]))
    return results[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query, e.g. 'heat_stress temperature flowering'")
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    index = load_index(Path(args.index))
    results = search(index, args.query, args.limit)
    print(json.dumps({"query": args.query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
