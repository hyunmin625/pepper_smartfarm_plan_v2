#!/usr/bin/env python3
"""Build a local JSON RAG index from pepper expert seed chunks."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "chunk_id",
    "document_id",
    "source_url",
    "source_type",
    "crop_type",
    "growth_stage",
    "cultivation_type",
    "sensor_tags",
    "risk_tags",
    "operation_tags",
    "chunk_summary",
    "agent_use",
    "citation_required",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            missing = sorted(REQUIRED_FIELDS - row.keys())
            if missing:
                raise ValueError(f"{path}:{line_number}: missing required fields: {', '.join(missing)}")
            rows.append(row)
    return rows


def ensure_unique_chunk_ids(rows: list[dict[str, Any]]) -> None:
    counts = Counter(row["chunk_id"] for row in rows)
    duplicates = sorted(chunk_id for chunk_id, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate chunk_id values: {', '.join(duplicates)}")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_document(row: dict[str, Any]) -> dict[str, Any]:
    text_parts = [
        row["chunk_summary"],
        "growth_stage: " + ", ".join(as_list(row["growth_stage"])),
        "sensor_tags: " + ", ".join(as_list(row["sensor_tags"])),
        "risk_tags: " + ", ".join(as_list(row["risk_tags"])),
        "operation_tags: " + ", ".join(as_list(row["operation_tags"])),
    ]
    metadata_keys = [
        "document_id",
        "source_url",
        "source_type",
        "crop_type",
        "growth_stage",
        "cultivation_type",
        "sensor_tags",
        "risk_tags",
        "operation_tags",
        "agent_use",
        "citation_required",
    ]
    return {
        "id": row["chunk_id"],
        "text": "\n".join(text_parts),
        "metadata": {key: row[key] for key in metadata_keys},
    }


def build_index(rows: list[dict[str, Any]]) -> dict[str, Any]:
    documents = [build_document(row) for row in rows]
    growth_stage_counts: Counter[str] = Counter()
    risk_tag_counts: Counter[str] = Counter()
    sensor_tag_counts: Counter[str] = Counter()

    for row in rows:
        growth_stage_counts.update(str(item) for item in as_list(row["growth_stage"]))
        risk_tag_counts.update(str(item) for item in as_list(row["risk_tags"]))
        sensor_tag_counts.update(str(item) for item in as_list(row["sensor_tags"]))

    return {
        "index_version": "rag_index.v1",
        "document_count": len(documents),
        "documents": documents,
        "stats": {
            "growth_stage_counts": dict(sorted(growth_stage_counts.items())),
            "risk_tag_counts": dict(sorted(risk_tag_counts.items())),
            "sensor_tag_counts": dict(sorted(sensor_tag_counts.items())),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/rag/pepper_expert_seed_chunks.jsonl")
    parser.add_argument("--output", default="artifacts/rag_index/pepper_expert_index.json")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = load_jsonl(input_path)
    ensure_unique_chunk_ids(rows)
    index = build_index(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {index['document_count']} documents to {output_path}")


if __name__ == "__main__":
    main()
