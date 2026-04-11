#!/usr/bin/env python3
"""Build a local JSON RAG index from pepper expert seed chunks."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from rag_local_vector import build_local_vector_model

load_dotenv()

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
    "causality_tags",
    "visual_tags",
    "chunk_summary",
    "agent_use",
    "citation_required",
}

OPTIONAL_METADATA_KEYS = [
    "causality_tags",
    "visual_tags",
    "source_pages",
    "source_page",
    "source_section",
    "trust_level",
    "version",
    "effective_date",
    "active",
    "region",
    "season",
    "cultivar",
    "greenhouse_type",
    "farm_id",
    "zone_id",
    "outcome",
]

EMBEDDING_MODEL = "text-embedding-3-small"


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
        "causality_tags: " + ", ".join(as_list(row.get("causality_tags"))),
        "visual_tags: " + ", ".join(as_list(row.get("visual_tags"))),
    ]
    if row.get("source_section"):
        text_parts.append("source_section: " + str(row["source_section"]))
    for key in ("region", "season", "cultivar", "greenhouse_type"):
        if row.get(key):
            text_parts.append(f"{key}: " + ", ".join(as_list(row[key])))
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
        "causality_tags",
        "visual_tags",
        "agent_use",
        "citation_required",
    ]
    metadata_keys.extend(key for key in OPTIONAL_METADATA_KEYS if key in row)
    return {
        "id": row["chunk_id"],
        "text": "\n".join(text_parts),
        "chunk_summary": row["chunk_summary"],
        "metadata": {key: row[key] for key in metadata_keys},
    }


def get_embeddings(texts: list[str], client: OpenAI) -> list[list[float]]:
    """Get embeddings for a list of texts using OpenAI API with batching."""
    if not texts:
        return []
    
    # OpenAI supports batching by passing a list of strings
    response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    # Sort by index to ensure order is preserved (though OpenAI usually preserves it)
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]


def build_index(rows: list[dict[str, Any]], client: OpenAI | None = None) -> dict[str, Any]:
    documents = [build_document(row) for row in rows]
    local_vector_model, local_embeddings = build_local_vector_model([doc["text"] for doc in documents])
    for document, embedding in zip(documents, local_embeddings):
        document["local_embedding"] = embedding
    
    if client:
        print(f"Generating embeddings for {len(documents)} documents...")
        summaries = [doc["chunk_summary"] for doc in documents]
        
        # Batch processing (OpenAI allows up to 2048 inputs per request for embeddings)
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(summaries), batch_size):
            batch = summaries[i : i + batch_size]
            print(f"  Processing batch {i//batch_size + 1} ({len(batch)} items)...")
            all_embeddings.extend(get_embeddings(batch, client))
        
        for doc, embedding in zip(documents, all_embeddings):
            doc["embedding"] = embedding

    growth_stage_counts: Counter[str] = Counter()
    risk_tag_counts: Counter[str] = Counter()
    sensor_tag_counts: Counter[str] = Counter()

    for row in rows:
        growth_stage_counts.update(str(item) for item in as_list(row["growth_stage"]))
        risk_tag_counts.update(str(item) for item in as_list(row["risk_tags"]))
        sensor_tag_counts.update(str(item) for item in as_list(row["sensor_tags"]))

    return {
        "index_version": "rag_index.v2",
        "embedding_model": EMBEDDING_MODEL,
        "local_vector_model": local_vector_model,
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
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding generation")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    
    api_key = os.environ.get("OPENAI_API_KEY")
    client = None
    if not args.skip_embeddings:
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Skipping embeddings.")
        else:
            client = OpenAI(api_key=api_key)

    rows = load_jsonl(input_path)
    ensure_unique_chunk_ids(rows)
    index = build_index(rows, client)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {index['document_count']} documents to {output_path}")


if __name__ == "__main__":
    main()
