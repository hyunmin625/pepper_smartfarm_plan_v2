#!/usr/bin/env python3
"""Run simple keyword and metadata search over the local RAG index."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from rag_chroma_store import (
    DEFAULT_CHROMA_PATH,
    distance_to_similarity,
    get_default_collection_name,
    get_collection,
)
from rag_local_vector import cosine_similarity, get_local_query_embedding

load_dotenv()

SEARCH_FIELDS = (
    "growth_stage",
    "sensor_tags",
    "risk_tags",
    "operation_tags",
    "causality_tags",
    "visual_tags",
    "agent_use",
    "source_section",
    "region",
    "season",
    "cultivar",
    "greenhouse_type",
)

EMBEDDING_MODEL = "text-embedding-3-small"
TRUST_LEVEL_BONUS = {
    "high": 0.6,
    "medium": 0.3,
    "review_required": -0.2,
}
SOURCE_TYPE_BONUS = {
    "official_master_guideline": 0.4,
    "official_guideline": 0.4,
    "official_research_report": 0.3,
    "research_paper": 0.25,
    "field_case": 0.2,
    "local_extension_news": 0.1,
    "farm_case": -0.15,
}
OFFICIAL_SOURCE_TYPES = {
    "official_master_guideline",
    "official_guideline",
    "official_research_report",
    "research_paper",
}
FARM_CASE_CONTEXT_KEYS = (
    "crop_type",
    "growth_stage",
    "sensor_tags",
    "risk_tags",
    "region",
    "season",
    "cultivar",
    "greenhouse_type",
    "farm_id",
    "zone_id",
)
DEFAULT_SCORE_CONFIG = {
    "text_match_weight": 2.0,
    "metadata_match_weight": 3.0,
    "openai_vector_weight": 10.0,
    "local_vector_weight": 4.0,
    "chroma_vector_weight": 10.0,
    "chroma_local_blend_weight": 4.0,
}
OFFICIAL_PRIORITY_THRESHOLD = 4.0


def load_index(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return [str(value).lower()]


def parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean filter value: {value}")


def matches_filter(metadata: dict[str, Any], key: str, value: str) -> bool:
    if key == "active":
        return bool(metadata.get(key, True)) is parse_bool(value)

    if key == "source_section":
        return value.lower() in str(metadata.get(key, "")).lower()

    meta_value = metadata.get(key)
    if isinstance(meta_value, list):
        return value.lower() in flatten(meta_value)
    return str(meta_value).lower() == value.lower()


def context_match_count(metadata: dict[str, Any], filters: dict[str, str] | None) -> int:
    if not filters:
        return 0
    count = 0
    for key in FARM_CASE_CONTEXT_KEYS:
        value = filters.get(key)
        if value and matches_filter(metadata, key, value):
            count += 1
    return count


def rerank_bonus(metadata: dict[str, Any], filters: dict[str, str] | None = None) -> tuple[float, list[str], int]:
    bonus = 0.0
    reasons: list[str] = []

    trust_level = str(metadata.get("trust_level", "")).lower()
    trust_bonus = TRUST_LEVEL_BONUS.get(trust_level, 0.0)
    if trust_bonus:
        bonus += trust_bonus
        reasons.append(f"trust_level:{trust_level}:{trust_bonus:+.2f}")

    source_type = str(metadata.get("source_type", "")).lower()
    source_bonus = SOURCE_TYPE_BONUS.get(source_type, 0.0)
    if source_bonus:
        bonus += source_bonus
        reasons.append(f"source_type:{source_type}:{source_bonus:+.2f}")

    overlap_count = context_match_count(metadata, filters)
    if overlap_count:
        if source_type == "farm_case":
            overlap_bonus = min(0.12 * overlap_count, 0.36)
            bonus += overlap_bonus
            reasons.append(f"farm_case_context_overlap:{overlap_count}:{overlap_bonus:+.2f}")
        elif source_type in OFFICIAL_SOURCE_TYPES:
            overlap_bonus = min(0.08 * overlap_count, 0.24)
            bonus += overlap_bonus
            reasons.append(f"official_context_overlap:{overlap_count}:{overlap_bonus:+.2f}")

    return bonus, reasons, overlap_count


def get_query_embedding(query: str, client: OpenAI) -> list[float]:
    response = client.embeddings.create(input=[query], model=EMBEDDING_MODEL)
    return response.data[0].embedding


def get_chroma_scores(
    query_embedding: list[float],
    chroma_path: Path,
    collection_name: str,
    candidate_limit: int,
) -> dict[str, float]:
    collection = get_collection(chroma_path, collection_name)
    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=candidate_limit,
        include=["distances"],
    )
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]
    return {
        chunk_id: round(distance_to_similarity(distance), 6)
        for chunk_id, distance in zip(ids, distances)
        if chunk_id
    }


def search(
    index: dict[str, Any],
    query: str,
    limit: int,
    client: OpenAI | None = None,
    filters: dict[str, str] | None = None,
    vector_backend: str = "auto",
    chroma_path: str | None = None,
    chroma_collection_name: str | None = None,
    chroma_embedding_backend: str = "auto",
    score_config: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    query_terms = [term.strip().lower() for term in query.replace(",", " ").split() if term.strip()]
    score_config = {**DEFAULT_SCORE_CONFIG, **(score_config or {})}

    openai_query_embedding = None
    local_query_embedding = None
    chroma_scores: dict[str, float] = {}
    local_vector_model = index.get("local_vector_model") or {}
    vector_mode = "keyword"
    use_chroma_local_blend = False
    selected_chroma_backend = chroma_embedding_backend
    resolved_chroma_collection_name = chroma_collection_name

    if vector_backend in {"auto", "openai"} and client:
        try:
            openai_query_embedding = get_query_embedding(query, client)
            if vector_backend in {"openai", "auto"}:
                vector_mode = "openai"
        except Exception as exc:
            print(f"Warning: Failed to get query embedding: {exc}")

    chroma_query_embedding = None
    if vector_backend == "chroma":
        if selected_chroma_backend == "auto":
            selected_chroma_backend = "openai" if client else "local"
        if not resolved_chroma_collection_name:
            resolved_chroma_collection_name = get_default_collection_name(selected_chroma_backend)
        if selected_chroma_backend == "openai":
            if openai_query_embedding is None and client:
                try:
                    openai_query_embedding = get_query_embedding(query, client)
                except Exception as exc:
                    print(f"Warning: Failed to get OpenAI query embedding for Chroma: {exc}")
            chroma_query_embedding = openai_query_embedding
            if local_vector_model and score_config["chroma_local_blend_weight"] > 0.0:
                local_query_embedding = get_local_query_embedding(query, local_vector_model)
                use_chroma_local_blend = any(local_query_embedding)
        elif selected_chroma_backend == "local" and local_vector_model:
            local_query_embedding = get_local_query_embedding(query, local_vector_model)
            if any(local_query_embedding):
                chroma_query_embedding = local_query_embedding

    if vector_backend == "chroma" and chroma_query_embedding:
        try:
            chroma_scores = get_chroma_scores(
                chroma_query_embedding,
                Path(chroma_path or DEFAULT_CHROMA_PATH),
                resolved_chroma_collection_name or get_default_collection_name(selected_chroma_backend),
                min(max(limit * 10, 25), int(index.get("document_count", len(index.get("documents", []))))),
            )
            if chroma_scores:
                vector_mode = "chroma"
        except Exception as exc:
            print(f"Warning: Failed to query Chroma collection: {exc}")

    if vector_mode == "keyword" and vector_backend in {"auto", "local"} and local_vector_model:
        local_query_embedding = get_local_query_embedding(query, local_vector_model)
        if any(local_query_embedding):
            vector_mode = "local"

    results = []
    for document in index["documents"]:
        metadata = document.get("metadata", {})
        
        # Metadata Hard Filtering
        if filters:
            skip = False
            for key, value in filters.items():
                if value:
                    if not matches_filter(metadata, key, value):
                        skip = True
                        break
            if skip:
                continue

        # Score calculation
        score = 0.0
        matches: list[str] = []

        if vector_mode == "openai" and openai_query_embedding and "embedding" in document:
            sim = cosine_similarity(openai_query_embedding, document["embedding"])
            matches.append(f"vector_sim:{sim:.4f}")
            score += sim * score_config["openai_vector_weight"]

        if vector_mode == "chroma":
            sim = chroma_scores.get(document["id"])
            if sim is not None:
                matches.append(f"chroma_vector_sim:{sim:.4f}")
                score += sim * score_config["chroma_vector_weight"]
            if (
                use_chroma_local_blend
                and local_query_embedding
                and "local_embedding" in document
            ):
                blend_sim = cosine_similarity(local_query_embedding, document["local_embedding"])
                matches.append(f"chroma_local_blend_sim:{blend_sim:.4f}")
                score += blend_sim * score_config["chroma_local_blend_weight"]

        if vector_mode == "local" and local_query_embedding and "local_embedding" in document:
            sim = cosine_similarity(local_query_embedding, document["local_embedding"])
            matches.append(f"local_vector_sim:{sim:.4f}")
            score += sim * score_config["local_vector_weight"]

        # Keyword Search (fallback/complement)
        text = document["text"].lower()
        for term in query_terms:
            if term in text:
                score += score_config["text_match_weight"]
                matches.append(f"text:{term}")
            for field in SEARCH_FIELDS:
                values = flatten(metadata.get(field))
                if term in values:
                    score += score_config["metadata_match_weight"]
                    matches.append(f"{field}:{term}")
        
        if score <= 0:
            continue

        bonus, rerank_reasons, overlap_count = rerank_bonus(metadata, filters)
        final_score = score + bonus
        matches.extend(rerank_reasons)
            
        results.append(
            {
                "id": document["id"],
                "score": round(final_score, 4),
                "base_score": round(score, 4),
                "rerank_bonus": round(bonus, 4),
                "context_match_count": overlap_count,
                "matches": matches,
                "summary": document["text"].splitlines()[0],
                "metadata": metadata,
            }
        )

    official_results_present = any(
        item["base_score"] >= OFFICIAL_PRIORITY_THRESHOLD
        and str(item["metadata"].get("source_type", "")).lower() in OFFICIAL_SOURCE_TYPES
        for item in results
    )
    farm_case_results_present = any(
        item["base_score"] > 0 and str(item["metadata"].get("source_type", "")).lower() == "farm_case"
        for item in results
    )
    if official_results_present:
        for item in results:
            source_type = str(item["metadata"].get("source_type", "")).lower()
            if source_type != "farm_case":
                continue
            penalty = 0.35
            if item["context_match_count"] == 0:
                penalty += 0.25
            item["score"] = round(item["score"] - penalty, 4)
            item["rerank_bonus"] = round(item["rerank_bonus"] - penalty, 4)
            item["matches"].append(f"farm_case_guardrail_penalty:{penalty:+.2f}")

    # Sort by score (desc), then source priority, then id
    def source_priority(item: dict[str, Any]) -> int:
        source_type = str(item["metadata"].get("source_type", "")).lower()
        if source_type in OFFICIAL_SOURCE_TYPES:
            return 0
        if source_type in {"field_case", "internal_sop"}:
            return 1
        if source_type == "farm_case":
            return 2
        return 3

    if official_results_present and farm_case_results_present:
        results.sort(key=lambda item: (source_priority(item), -item["score"], item["id"]))
    else:
        results.sort(key=lambda item: (-item["score"], source_priority(item), item["id"]))
    return results[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query, e.g. 'heat stress in greenhouse'")
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--growth-stage", help="Filter by growth stage, e.g. 'fruiting'")
    parser.add_argument("--crop-type", help="Filter by crop type")
    parser.add_argument("--source-type", help="Filter by source type")
    parser.add_argument("--sensor-tag", help="Filter by sensor tag")
    parser.add_argument("--risk-tag", help="Filter by risk tag")
    parser.add_argument("--source-section", help="Filter by source section substring")
    parser.add_argument("--trust-level", help="Filter by trust level, e.g. high")
    parser.add_argument("--region", help="Filter by region")
    parser.add_argument("--season", help="Filter by season")
    parser.add_argument("--cultivar", help="Filter by cultivar")
    parser.add_argument("--greenhouse-type", help="Filter by greenhouse type")
    parser.add_argument("--farm-id", help="Filter by farm id")
    parser.add_argument("--zone-id", help="Filter by zone id")
    parser.add_argument("--active", help="Filter active chunks: true or false")
    parser.add_argument("--no-vector", action="store_true", help="Disable vector search")
    parser.add_argument(
        "--vector-backend",
        choices=("auto", "openai", "local", "chroma", "none"),
        default="auto",
        help="Select vector scoring backend",
    )
    parser.add_argument("--chroma-path", default=str(DEFAULT_CHROMA_PATH), help="Persistent Chroma DB path")
    parser.add_argument("--collection-name", help="Chroma collection name")
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

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"Error: Index file not found at {index_path}")
        return

    index = load_index(index_path)
    
    api_key = os.environ.get("OPENAI_API_KEY")
    client = None
    vector_backend = "none" if args.no_vector else args.vector_backend
    if vector_backend in {"auto", "openai", "chroma"}:
        if api_key:
            client = OpenAI(api_key=api_key)
        elif vector_backend == "openai":
            print("Warning: OPENAI_API_KEY not found. OpenAI vector search disabled.")
        elif vector_backend == "chroma":
            if args.chroma_embedding_backend == "openai":
                print("Warning: OPENAI_API_KEY not found. OpenAI-backed Chroma vector search disabled.")
            elif args.chroma_embedding_backend == "local":
                pass
            elif args.chroma_embedding_backend == "auto" and index.get("local_vector_model"):
                print("Warning: OPENAI_API_KEY not found. Using local query embedding for Chroma.")
            else:
                print("Warning: OPENAI_API_KEY not found. Chroma vector search disabled.")
        elif vector_backend == "auto":
            if index.get("local_vector_model"):
                print("Warning: OPENAI_API_KEY not found. Falling back to local vector search.")
            else:
                print("Warning: OPENAI_API_KEY not found. Vector search disabled.")

    filters = {
        "growth_stage": args.growth_stage,
        "crop_type": args.crop_type,
        "source_type": args.source_type,
        "sensor_tags": args.sensor_tag,
        "risk_tags": args.risk_tag,
        "source_section": args.source_section,
        "trust_level": args.trust_level,
        "region": args.region,
        "season": args.season,
        "cultivar": args.cultivar,
        "greenhouse_type": args.greenhouse_type,
        "farm_id": args.farm_id,
        "zone_id": args.zone_id,
        "active": args.active,
    }
    score_config = {
        "text_match_weight": args.text_match_weight,
        "metadata_match_weight": args.metadata_match_weight,
        "openai_vector_weight": args.openai_vector_weight,
        "local_vector_weight": args.local_vector_weight,
        "chroma_vector_weight": args.chroma_vector_weight,
        "chroma_local_blend_weight": args.chroma_local_blend_weight,
    }

    results = search(
        index, 
        args.query, 
        args.limit, 
        client=client, 
        filters={k: v for k, v in filters.items() if v},
        vector_backend=vector_backend,
        chroma_path=args.chroma_path,
        chroma_collection_name=args.collection_name,
        chroma_embedding_backend=args.chroma_embedding_backend,
        score_config=score_config,
    )
    
    output = {
        "query": args.query,
        "vector_backend": vector_backend,
        "chroma_embedding_backend": args.chroma_embedding_backend if vector_backend == "chroma" else None,
        "score_config": score_config,
        "filters": {k: v for k, v in filters.items() if v},
        "count": len(results),
        "results": results
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
