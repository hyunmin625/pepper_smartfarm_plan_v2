#!/usr/bin/env python3
"""Verify expected chunks are returned by local RAG search queries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from search_rag_index import load_index, search


SMOKE_TESTS = [
    ("heat_stress temperature flowering", "pepper-climate-001"),
    ("overwet root_damage soil_moisture", "pepper-rootzone-001"),
    ("feed_ec drain_ec drain_rate", "pepper-hydroponic-001"),
    ("thrips anthracnose vision_symptom", "pepper-pest-001"),
    ("nursery transplanting temperature", "pepper-lifecycle-001"),
    ("decision_support approval audit", "pepper-agent-001"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    index = load_index(Path(args.index))
    failures = []
    for query, expected_id in SMOKE_TESTS:
        results = search(index, query, args.limit)
        result_ids = [item["id"] for item in results]
        if expected_id not in result_ids:
            failures.append((query, expected_id, result_ids))
            print(f"FAIL {query!r}: expected {expected_id}, got {result_ids}")
        else:
            print(f"PASS {query!r}: found {expected_id}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
