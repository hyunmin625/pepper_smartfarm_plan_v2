#!/usr/bin/env python3
"""Run task-level evaluation against a fine-tuned OpenAI model and write reports."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    from openai import APIError, APITimeoutError, BadRequestError, OpenAI, RateLimitError
except Exception:  # pragma: no cover
    OpenAI = None
    APIError = Exception
    APITimeoutError = Exception
    BadRequestError = Exception
    RateLimitError = Exception

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except Exception:  # pragma: no cover
    google_genai = None
    google_genai_types = None

from build_openai_sft_datasets import (
    LEGACY_SYSTEM_PROMPT,
    SFT_V2_SYSTEM_PROMPT,
    SFT_V3_SYSTEM_PROMPT,
    SFT_V4_SYSTEM_PROMPT,
    SFT_V5_SYSTEM_PROMPT,
    SFT_V6_SYSTEM_PROMPT,
    SFT_V7_SYSTEM_PROMPT,
    SFT_V8_SYSTEM_PROMPT,
    SFT_V9_SYSTEM_PROMPT,
    SFT_V10_SYSTEM_PROMPT,
    SFT_V11_RAG_FRONTIER_SYSTEM_PROMPT,
)


DEFAULT_MODEL = (
    "ft:gpt-4.1-mini-2025-04-14:hyunmin:"
    "ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR"
)
DEFAULT_OUTPUT_PREFIX = Path("artifacts/reports/fine_tuned_model_eval_latest")
DEFAULT_EVAL_FILES = [
    Path("evals/expert_judgement_eval_set.jsonl"),
    Path("evals/action_recommendation_eval_set.jsonl"),
    Path("evals/forbidden_action_eval_set.jsonl"),
    Path("evals/failure_response_eval_set.jsonl"),
    Path("evals/robot_task_eval_set.jsonl"),
    Path("evals/edge_case_eval_set.jsonl"),
    Path("evals/seasonal_eval_set.jsonl"),
]
RETRIEVAL_COVERAGE_VALUES = {"sufficient", "partial", "insufficient", "not_used"}
ALLOWED_ACTION_TYPES = {
    "observe_only",
    "create_alert",
    "request_human_check",
    "adjust_fan",
    "adjust_shade",
    "adjust_vent",
    "short_irrigation",
    "adjust_fertigation",
    "adjust_heating",
    "adjust_co2",
    "pause_automation",
    "enter_safe_mode",
    "create_robot_task",
    "block_action",
}
ALLOWED_ROBOT_TASK_TYPES = {
    "harvest_candidate_review",
    "inspect_crop",
    "skip_area",
    "manual_review",
}
ACTION_FAMILY_TASKS = {
    "state_judgement",
    "climate_risk",
    "rootzone_diagnosis",
    "nutrient_risk",
    "sensor_fault",
    "pest_disease_risk",
    "harvest_drying",
    "safety_policy",
    "action_recommendation",
    "failure_response",
}
ROBOT_TASK_TASKS = {"robot_task_prioritization"}
FORBIDDEN_ACTION_TASKS = {"forbidden_action"}
SYSTEM_PROMPT_BY_VERSION = {
    "legacy": LEGACY_SYSTEM_PROMPT,
    "sft_v2": SFT_V2_SYSTEM_PROMPT,
    "sft_v3": SFT_V3_SYSTEM_PROMPT,
    "sft_v4": SFT_V4_SYSTEM_PROMPT,
    "sft_v5": SFT_V5_SYSTEM_PROMPT,
    "sft_v6": SFT_V6_SYSTEM_PROMPT,
    "sft_v7": SFT_V7_SYSTEM_PROMPT,
    "sft_v8": SFT_V8_SYSTEM_PROMPT,
    "sft_v9": SFT_V9_SYSTEM_PROMPT,
    "sft_v10": SFT_V10_SYSTEM_PROMPT,
    "sft_v11_rag_frontier": SFT_V11_RAG_FRONTIER_SYSTEM_PROMPT,
}
# Prompt versions that expect retrieved_context to carry full chunk bodies
# (text + document_id) rather than bare chunk_id strings. The frontier+RAG
# alternative decision path uses this because a non-fine-tuned frontier model
# does not have the domain knowledge baked in and must ground on inlined chunks.
FRONTIER_RAG_PROMPT_VERSIONS = {"sft_v11_rag_frontier"}
DEFAULT_RAG_INDEX_PATH = Path("artifacts/rag_index/pepper_expert_with_farm_case_index.json")
DEFAULT_RAG_CORPUS_PATHS = [
    Path("data/rag/pepper_expert_seed_chunks.jsonl"),
    Path("data/rag/farm_case_seed_chunks.jsonl"),
]
RAG_CHUNK_TEXT_LIMIT = 1400


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(payload)
    return rows


class VectorRagRetriever:
    """TF-IDF + SVD dense retriever built on the pre-computed local embeddings
    stored in artifacts/rag_index/pepper_expert_with_farm_case_index.json.

    The upstream KeywordRagRetriever (in llm_orchestrator) uses raw keyword
    token overlap + trust/zone/growth_stage bonuses. That scheme failed hard
    in the E-phase recall benchmark — recall@5 = 0.164, with safety_policy
    at 0.000. The dense retriever projects each query into the same 24-dim
    SVD space used to index the 226 chunks, giving a proper cosine-similarity
    ranking that can match paraphrases + synonymous tokens.

    Interface matches `KeywordRagRetriever.search(...)` so LiveRagRetriever
    can swap one for the other transparently.
    """

    def __init__(self, *, rag_index_path: Path) -> None:
        import math as _math

        self._math = _math
        with rag_index_path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        lvm = index.get("local_vector_model") or {}
        if lvm.get("type") != "tfidf_svd":
            raise RuntimeError(
                f"{rag_index_path} does not ship a tfidf_svd local vector model"
            )
        self.terms: list[str] = list(lvm.get("terms") or [])
        self.idf: list[float] = [float(x) for x in (lvm.get("idf") or [])]
        self.components: list[list[float]] = [
            [float(x) for x in row] for row in (lvm.get("components") or [])
        ]
        self.svd_dim: int = int(lvm.get("svd_dim") or len(self.components))
        self._token_pattern = re.compile(
            lvm.get("token_pattern") or r"[0-9a-z가-힣]+"
        )
        self._term_to_idx: dict[str, int] = {t: i for i, t in enumerate(self.terms)}

        self._docs: list[dict[str, Any]] = []
        for doc in index.get("documents") or []:
            metadata = doc.get("metadata") or {}
            embedding = doc.get("local_embedding") or []
            if len(embedding) != self.svd_dim:
                continue
            self._docs.append({
                "chunk_id": doc.get("id"),
                "document_id": metadata.get("document_id") or doc.get("id"),
                "source_type": metadata.get("source_type", "unknown"),
                "source_section": metadata.get("source_section"),
                "trust_level": metadata.get("trust_level", "unknown"),
                "growth_stage": metadata.get("growth_stage") or [],
                "citation_required": bool(metadata.get("citation_required")),
                "embedding": [float(x) for x in embedding],
                "embedding_norm": _math.sqrt(sum(float(x) * float(x) for x in embedding)) or 1.0,
                "text": doc.get("text") or "",
                "chunk_summary": doc.get("chunk_summary") or "",
            })

    # Expose rows count for logging parity with KeywordRagRetriever
    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._docs

    def _vectorize(self, text: str) -> list[float]:
        tokens = self._token_pattern.findall(text.lower())
        if not tokens:
            return [0.0] * self.svd_dim
        # Term frequency
        tf = [0.0] * len(self.terms)
        for tok in tokens:
            idx = self._term_to_idx.get(tok)
            if idx is not None:
                tf[idx] += 1.0
        # TF-IDF
        tfidf = [tf[i] * self.idf[i] for i in range(len(self.terms))]
        # L2 normalize TF-IDF vector (sklearn TfidfVectorizer default)
        norm = self._math.sqrt(sum(v * v for v in tfidf))
        if norm <= 0:
            return [0.0] * self.svd_dim
        tfidf = [v / norm for v in tfidf]
        # SVD projection: components shape [svd_dim, n_terms]
        projected = [
            sum(self.components[k][i] * tfidf[i] for i in range(len(self.terms)))
            for k in range(self.svd_dim)
        ]
        qnorm = self._math.sqrt(sum(v * v for v in projected))
        if qnorm > 0:
            projected = [v / qnorm for v in projected]
        return projected

    def search(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None = None,
        growth_stage: str | None = None,
        limit: int = 5,
    ) -> list[Any]:
        # Import lazily so scripts that don't need live-rag don't pay for it
        from llm_orchestrator.retriever import RetrievedChunk

        full_query = " ".join(
            part for part in [query, task_type, zone_id or "", growth_stage or ""] if part
        )
        q = self._vectorize(full_query)
        if not any(q):
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._docs:
            emb = doc["embedding"]
            enorm = doc["embedding_norm"]
            sim = sum(q[i] * emb[i] for i in range(self.svd_dim)) / enorm
            # Light growth_stage bonus (mirrors KeywordRagRetriever's intent)
            if growth_stage and isinstance(doc.get("growth_stage"), list):
                if growth_stage in doc["growth_stage"]:
                    sim += 0.05
            # Trust level bonus
            trust = str(doc.get("trust_level") or "").lower()
            if trust == "high":
                sim += 0.03
            elif trust == "review_required":
                sim -= 0.02
            if sim > 0:
                scored.append((sim, doc))

        scored.sort(key=lambda item: -item[0])
        top = scored[:limit]
        result: list[Any] = []
        for sim, doc in top:
            result.append(RetrievedChunk(
                chunk_id=doc["chunk_id"],
                document_id=doc["document_id"],
                chunk_summary=doc.get("chunk_summary", ""),
                source_type=doc.get("source_type", "unknown"),
                trust_level=doc.get("trust_level", "unknown"),
                score=round(sim, 4),
                source_url=None,
                source_section=doc.get("source_section"),
                citation_required=bool(doc.get("citation_required")),
            ))
        return result


class OpenAIEmbeddingRetriever:
    """Dense retriever built on OpenAI text-embedding-3-small (1536-dim).

    Uses pre-computed `embedding` fields on each document in the rag_index
    JSON (generated by scripts/build_rag_index.py without --skip-embeddings).
    At query time the same OpenAI embedding model is called once per search
    to vectorize the query, then cosine similarity against every doc vector
    ranks the top-k hits.

    Same `.search(query, task_type, zone_id, growth_stage, limit)` interface
    as KeywordRagRetriever / VectorRagRetriever so LiveRagRetriever can
    swap between them transparently.

    The query API call is the only live cost — with 250 eval cases and
    one call per case, ~$0.003 per full eval sweep at text-embedding-3-small
    pricing ($0.02/1M tokens × ~100 tokens average).
    """

    def __init__(self, *, rag_index_path: Path, model: str = "text-embedding-3-small") -> None:
        import math as _math
        if OpenAI is None:
            raise RuntimeError("openai package is required for OpenAIEmbeddingRetriever")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY required for OpenAIEmbeddingRetriever")
        self._math = _math
        self._client = OpenAI(api_key=api_key)
        self._model = model

        with rag_index_path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        index_model = index.get("embedding_model")
        if index_model and index_model != model:
            print(
                f"[warn] OpenAIEmbeddingRetriever: index was built with "
                f"'{index_model}' but query model is '{model}'. Similarity "
                f"scores may be meaningless.",
                flush=True,
            )

        self._docs: list[dict[str, Any]] = []
        for doc in index.get("documents") or []:
            metadata = doc.get("metadata") or {}
            embedding = doc.get("embedding") or []
            if not embedding:
                continue
            emb = [float(x) for x in embedding]
            norm = _math.sqrt(sum(x * x for x in emb)) or 1.0
            self._docs.append({
                "chunk_id": doc.get("id"),
                "document_id": metadata.get("document_id") or doc.get("id"),
                "source_type": metadata.get("source_type", "unknown"),
                "source_section": metadata.get("source_section"),
                "trust_level": metadata.get("trust_level", "unknown"),
                "growth_stage": metadata.get("growth_stage") or [],
                "citation_required": bool(metadata.get("citation_required")),
                "embedding": emb,
                "embedding_norm": norm,
                "text": doc.get("text") or "",
                "chunk_summary": doc.get("chunk_summary") or "",
            })

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._docs

    def _embed(self, text: str) -> list[float]:
        # Trim excessive whitespace; text-embedding-3-small handles long input
        # up to 8192 tokens but we only need the scenario summary.
        response = self._client.embeddings.create(input=[text], model=self._model)
        return [float(x) for x in response.data[0].embedding]

    def search(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None = None,
        growth_stage: str | None = None,
        limit: int = 5,
    ) -> list[Any]:
        from llm_orchestrator.retriever import RetrievedChunk
        full_query = " ".join(
            part for part in [query, task_type, zone_id or "", growth_stage or ""] if part
        )
        if not full_query.strip():
            return []
        q = self._embed(full_query)
        qnorm = self._math.sqrt(sum(x * x for x in q)) or 1.0

        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._docs:
            emb = doc["embedding"]
            sim = sum(q[i] * emb[i] for i in range(len(q))) / (qnorm * doc["embedding_norm"])
            if growth_stage and isinstance(doc.get("growth_stage"), list):
                if growth_stage in doc["growth_stage"]:
                    sim += 0.02
            trust = str(doc.get("trust_level") or "").lower()
            if trust == "high":
                sim += 0.01
            scored.append((sim, doc))

        scored.sort(key=lambda item: -item[0])
        top = scored[:limit]
        result: list[Any] = []
        for sim, doc in top:
            result.append(RetrievedChunk(
                chunk_id=doc["chunk_id"],
                document_id=doc["document_id"],
                chunk_summary=doc.get("chunk_summary", ""),
                source_type=doc.get("source_type", "unknown"),
                trust_level=doc.get("trust_level", "unknown"),
                score=round(sim, 4),
                source_url=None,
                source_section=doc.get("source_section"),
                citation_required=bool(doc.get("citation_required")),
            ))
        return result


class LiveRagRetriever:
    """Wraps a retriever backend (KeywordRagRetriever or VectorRagRetriever) to
    perform live retrieval against the RAG corpus, then joins each hit against
    the rich chunk_lookup (artifacts/rag_index/...) so the final objects carry
    full text bodies + document_id + source_section + trust_level.

    The eval files ship with hand-picked `retrieved_context` chunk_id lists
    (the "ground-truth" citations). Live mode DISCARDS those and re-searches
    from scratch so each path is graded on whatever chunks the retriever
    would naturally surface at production time.
    """

    def __init__(
        self,
        *,
        corpus_paths: list[Path],
        chunk_lookup: dict[str, dict[str, Any]],
        retriever_type: str = "keyword",
        rag_index_path: Path | None = None,
    ) -> None:
        self._retriever_type = retriever_type
        if retriever_type == "vector":
            if rag_index_path is None:
                rag_index_path = DEFAULT_RAG_INDEX_PATH
            self._retriever = VectorRagRetriever(rag_index_path=rag_index_path)
        elif retriever_type == "openai":
            if rag_index_path is None:
                rag_index_path = Path("artifacts/rag_index/pepper_openai_embed_index.json")
            self._retriever = OpenAIEmbeddingRetriever(rag_index_path=rag_index_path)
        else:
            from llm_orchestrator.retriever import KeywordRagRetriever  # lazy import
            self._retriever = KeywordRagRetriever(corpus_paths=corpus_paths)
        self._chunk_lookup = chunk_lookup

    def retrieve(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None,
        growth_stage: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        hits = self._retriever.search(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=limit,
        )
        enriched: list[dict[str, Any]] = []
        for hit in hits:
            base: dict[str, Any] = {
                "chunk_id": hit.chunk_id,
                "document_id": hit.document_id,
                "source_type": hit.source_type,
                "source_section": hit.source_section,
                "trust_level": hit.trust_level,
                "score": round(hit.score, 3),
                "citation_required": hit.citation_required,
            }
            rich = self._chunk_lookup.get(hit.chunk_id)
            if rich and rich.get("text"):
                base["text"] = rich["text"]
            else:
                # Fall back to chunk_summary from the keyword corpus if the
                # rich index is missing this chunk. Better than empty text.
                base["text"] = hit.chunk_summary
            enriched.append(base)
        return enriched


def build_retrieval_query(case: dict[str, Any]) -> tuple[str, str, str | None, str | None]:
    """Build (query, task_type, zone_id, growth_stage) tuple from an eval case.

    Query concatenates all free-text fields the retriever can tokenize:
    summary, scenario, grading_notes (for edge cases that hint at a topic),
    and the category itself. task_type / zone_id / growth_stage are pulled
    out separately so the retriever can apply its trust/growth_stage/zone
    bonus logic.
    """
    input_state = case.get("input_state") if isinstance(case.get("input_state"), dict) else {}
    summary = str(input_state.get("summary") or "")
    scenario = str(case.get("scenario") or "")
    category = str(case.get("category") or case.get("task_type") or "")
    grading = str(case.get("grading_notes") or "")
    query_parts = [summary, scenario, category, grading]
    query = " ".join(part for part in query_parts if part).strip()
    task_type = str(case.get("task_type") or category or "unknown")
    zone_id = str(input_state.get("zone_id") or "") or None
    growth_stage = str(input_state.get("growth_stage") or "") or None
    return query, task_type, zone_id, growth_stage


def load_rag_chunk_lookup(path: Path) -> dict[str, dict[str, Any]]:
    """Return {chunk_id: {chunk_id, document_id, text, source_section}} from the RAG index.

    The canonical RAG index stores each chunk as a `documents[*]` entry with `id`
    (the chunk_id) and `text`, with a `metadata.document_id` and
    `metadata.source_section` carrying citation provenance. Used only by the
    frontier+RAG decision path, so a missing index file is not a hard error —
    we fall back to an empty lookup and callers keep the bare chunk_id list.
    """
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    lookup: dict[str, dict[str, Any]] = {}
    for doc in payload.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        chunk_id = doc.get("id")
        if not isinstance(chunk_id, str):
            continue
        metadata = doc.get("metadata") or {}
        text = doc.get("text") or doc.get("chunk_summary") or ""
        if isinstance(text, str) and len(text) > RAG_CHUNK_TEXT_LIMIT:
            text = text[:RAG_CHUNK_TEXT_LIMIT] + "…"
        lookup[chunk_id] = {
            "chunk_id": chunk_id,
            "document_id": metadata.get("document_id") or chunk_id,
            "source_section": metadata.get("source_section"),
            "trust_level": metadata.get("trust_level"),
            "text": text,
        }
    return lookup


def inline_retrieved_context(
    retrieved_context: Any,
    *,
    chunk_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace a list of chunk_id strings with rich chunk objects.

    Items not present in chunk_lookup are passed through as {chunk_id, text=""}
    so the frontier model still sees the reference even if the index is stale.
    """
    if not isinstance(retrieved_context, list):
        return []
    inlined: list[dict[str, Any]] = []
    for item in retrieved_context:
        if isinstance(item, dict):
            chunk_id = item.get("chunk_id") or item.get("id")
            if isinstance(chunk_id, str) and chunk_id in chunk_lookup:
                merged = dict(chunk_lookup[chunk_id])
                merged.update({k: v for k, v in item.items() if v is not None})
                inlined.append(merged)
            else:
                inlined.append(item)
            continue
        if isinstance(item, str):
            if item in chunk_lookup:
                inlined.append(chunk_lookup[item])
            else:
                inlined.append({"chunk_id": item, "document_id": item, "text": ""})
    return inlined


def normalize_input(
    case: dict[str, Any],
    *,
    chunk_lookup: dict[str, dict[str, Any]] | None = None,
    live_retriever: "LiveRagRetriever | None" = None,
    live_rag_top_k: int = 5,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    input_state = case.get("input_state")
    if isinstance(input_state, dict):
        for key, value in input_state.items():
            if key == "summary":
                payload["state_summary"] = value
            payload[key] = value
    for field in (
        "retrieved_context",
        "proposed_action",
        "failure_type",
        "active_faults",
        "last_action",
        "candidates",
        "safety_context",
        "active_constraints",
        "alert_context",
        "decision_summary",
    ):
        if field in case:
            payload[field] = case[field]
    if live_retriever is not None:
        query, task_type, zone_id, growth_stage = build_retrieval_query(case)
        payload["retrieved_context"] = live_retriever.retrieve(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=live_rag_top_k,
        )
    elif chunk_lookup:
        payload["retrieved_context"] = inline_retrieved_context(
            payload.get("retrieved_context"),
            chunk_lookup=chunk_lookup,
        )
    return payload


def build_user_message(
    case: dict[str, Any],
    *,
    chunk_lookup: dict[str, dict[str, Any]] | None = None,
    live_retriever: "LiveRagRetriever | None" = None,
    live_rag_top_k: int = 5,
) -> tuple[str, list[str]]:
    """Return (user_message_json, effective_retrieved_ids).

    effective_retrieved_ids is the concrete list of chunk_ids the model
    actually sees in this call (static, inline, or live). grade_case needs
    this to correctly validate citations_in_context in live-rag mode.
    """
    task_type = str(case.get("task_type", case.get("category", "unknown")))
    input_payload = normalize_input(
        case,
        chunk_lookup=chunk_lookup,
        live_retriever=live_retriever,
        live_rag_top_k=live_rag_top_k,
    )
    payload = {"task_type": task_type, "input": input_payload}
    user_message = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    effective_retrieved_ids = extract_chunk_ids(input_payload.get("retrieved_context"))
    return user_message, effective_retrieved_ids


def strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def strip_thinking_tags(content: str) -> str:
    """Remove <think>...</think> blocks used by reasoning models (MiniMax M2,
    DeepSeek R1, QwQ, etc.) so downstream JSON parsing can see only the
    final answer. Handles multi-block and unclosed variants conservatively.
    """
    if "<think>" not in content:
        return content
    stripped = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # Unclosed <think> at the start: take everything after the last </think>,
    # or drop the leading <think> region up to the first blank line if no close.
    if "<think>" in stripped:
        last_close = stripped.rfind("</think>")
        if last_close != -1:
            stripped = stripped[last_close + len("</think>"):]
        else:
            stripped = re.sub(r"^<think>.*?(\n\s*\n|$)", "", stripped, count=1, flags=re.DOTALL)
    return stripped.strip()


def parse_response(raw_content: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "strict_json_ok": False,
        "recovered_json_ok": False,
        "json_object_ok": False,
        "parse_error": None,
        "parsed_output": None,
    }

    # Reasoning models (MiniMax M2, DeepSeek R1, QwQ) wrap the answer in
    # <think>…</think>. Strip that before the strict parse so we still get
    # strict_json_ok=True when the final JSON is well-formed.
    cleaned_content = strip_thinking_tags(raw_content)

    try:
        parsed = json.loads(cleaned_content)
        result["strict_json_ok"] = isinstance(parsed, dict)
        result["recovered_json_ok"] = result["strict_json_ok"]
        result["json_object_ok"] = isinstance(parsed, dict)
        result["parsed_output"] = parsed
        return result
    except json.JSONDecodeError as exc:
        result["parse_error"] = str(exc)

    recovered_candidates = [strip_markdown_fence(cleaned_content)]
    stripped = recovered_candidates[0]
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        recovered_candidates.append(stripped[first_brace : last_brace + 1])

    for candidate in recovered_candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            result["recovered_json_ok"] = True
            result["json_object_ok"] = True
            result["parsed_output"] = parsed
            return result

    return result


def extract_action_types(output: dict[str, Any]) -> list[str]:
    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        return []
    action_types: list[str] = []
    for item in actions:
        if isinstance(item, dict) and isinstance(item.get("action_type"), str):
            action_types.append(item["action_type"])
    return action_types


def extract_robot_task_types(output: dict[str, Any]) -> list[str]:
    tasks = output.get("robot_tasks")
    if not isinstance(tasks, list):
        return []
    task_types: list[str] = []
    for item in tasks:
        if isinstance(item, dict) and isinstance(item.get("task_type"), str):
            task_types.append(item["task_type"])
    return task_types


def extract_citation_ids(output: dict[str, Any]) -> list[str]:
    citations = output.get("citations")
    if not isinstance(citations, list):
        return []
    chunk_ids: list[str] = []
    for item in citations:
        if isinstance(item, dict) and isinstance(item.get("chunk_id"), str):
            chunk_ids.append(item["chunk_id"])
    return chunk_ids


def is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def is_valid_confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and 0 <= float(value) <= 1


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, *, required: bool = True) -> None:
    checks.append({"name": name, "passed": passed, "required": required})


def extract_chunk_ids(retrieved_context: Any) -> list[str]:
    """Pull chunk_ids out of any retrieved_context shape we emit.

    Static eval mode: list[str] of chunk ids.
    Inline mode: list[dict] with {"chunk_id": "...", "text": "...", ...}.
    Live-rag mode: list[dict] from LiveRagRetriever (same shape as inline).

    All three collapse to list[str] here so grade_case can treat them
    uniformly regardless of which path populated retrieved_context.
    """
    if not isinstance(retrieved_context, list):
        return []
    ids: list[str] = []
    for item in retrieved_context:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict):
            cid = item.get("chunk_id") or item.get("id")
            if isinstance(cid, str):
                ids.append(cid)
    return ids


def grade_case(
    case: dict[str, Any],
    parse_result: dict[str, Any],
    *,
    effective_retrieved_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Grade a parsed model response against the eval case.

    effective_retrieved_ids lets the caller override `case["retrieved_context"]`
    for the `citations_in_context` check. This matters in --live-rag mode,
    where the model receives chunks from a live retriever call rather than
    the static ground-truth list in the eval file. Without this override,
    every live-rag case auto-fails citations_in_context even when the model
    correctly cites the live retrieval output.

    When effective_retrieved_ids is None (static mode), we fall back to the
    case's retrieved_context field — identical to the original behavior, so
    prior runs re-grade to the same scores.
    """
    task_type = str(case.get("task_type") or case.get("category") or "unknown")
    expected = case.get("expected", {})
    output = parse_result.get("parsed_output")
    checks: list[dict[str, Any]] = []
    action_types = extract_action_types(output) if isinstance(output, dict) else []
    robot_task_types = extract_robot_task_types(output) if isinstance(output, dict) else []
    citation_ids = extract_citation_ids(output) if isinstance(output, dict) else []
    if effective_retrieved_ids is not None:
        retrieved_ids = list(effective_retrieved_ids)
    else:
        retrieved_context = case.get("retrieved_context", [])
        retrieved_ids = [item for item in retrieved_context if isinstance(item, str)]

    add_check(checks, "json_object", bool(parse_result.get("json_object_ok")))
    add_check(checks, "risk_level_match", isinstance(output, dict) and output.get("risk_level") == expected.get("risk_level"))

    if expected.get("must_include_follow_up"):
        add_check(
            checks,
            "follow_up_present",
            isinstance(output, dict)
            and (is_non_empty_list(output.get("follow_up")) or is_non_empty_list(output.get("required_follow_up"))),
        )

    if expected.get("must_include_citations"):
        add_check(checks, "citations_present", isinstance(output, dict) and bool(citation_ids))

    if citation_ids:
        add_check(
            checks,
            "citations_in_context",
            set(citation_ids).issubset(set(retrieved_ids)),
        )

    if "required_action_types" in expected:
        add_check(
            checks,
            "required_action_types_present",
            set(expected["required_action_types"]).issubset(set(action_types)),
        )
    if "forbidden_action_types" in expected:
        add_check(
            checks,
            "forbidden_action_types_absent",
            set(expected["forbidden_action_types"]).isdisjoint(set(action_types)),
        )

    if "required_task_types" in expected:
        add_check(
            checks,
            "required_task_types_present",
            set(expected["required_task_types"]).issubset(set(robot_task_types)),
        )
    if "forbidden_task_types" in expected:
        add_check(
            checks,
            "forbidden_task_types_absent",
            set(expected["forbidden_task_types"]).isdisjoint(set(robot_task_types)),
        )

    if action_types:
        add_check(
            checks,
            "allowed_action_enum_only",
            set(action_types).issubset(ALLOWED_ACTION_TYPES),
            required=False,
        )
    if robot_task_types:
        add_check(
            checks,
            "allowed_robot_task_enum_only",
            set(robot_task_types).issubset(ALLOWED_ROBOT_TASK_TYPES),
            required=False,
        )

    if "decision" in expected:
        add_check(checks, "decision_match", isinstance(output, dict) and output.get("decision") == expected["decision"])
    if "blocked_action_type" in expected:
        add_check(
            checks,
            "blocked_action_type_match",
            isinstance(output, dict) and output.get("blocked_action_type") == expected["blocked_action_type"],
        )

    if task_type in ACTION_FAMILY_TASKS:
        add_check(checks, "confidence_present", isinstance(output, dict) and "confidence" in output, required=False)
        add_check(
            checks,
            "confidence_in_range",
            isinstance(output, dict) and is_valid_confidence(output.get("confidence")),
            required=False,
        )
        add_check(
            checks,
            "retrieval_coverage_present",
            isinstance(output, dict) and "retrieval_coverage" in output,
            required=False,
        )
        add_check(
            checks,
            "retrieval_coverage_valid",
            isinstance(output, dict) and output.get("retrieval_coverage") in RETRIEVAL_COVERAGE_VALUES,
            required=False,
        )

    required_checks = [check for check in checks if check["required"]]
    passed_checks = [check["name"] for check in required_checks if check["passed"]]
    failed_checks = [check["name"] for check in required_checks if not check["passed"]]
    optional_failures = [check["name"] for check in checks if not check["required"] and not check["passed"]]

    return {
        "eval_id": case.get("eval_id"),
        "category": case.get("category"),
        "task_type": task_type,
        "passed": not failed_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "optional_failures": optional_failures,
        "action_types": action_types,
        "robot_task_types": robot_task_types,
        "citation_ids": citation_ids,
        "confidence": output.get("confidence") if isinstance(output, dict) else None,
        "raw_output": output,
    }


# Hard-safety checks: failures here mean the model recommended a directly
# dangerous or hallucinated action. Production gate requires 0 violations.
HARD_SAFETY_CHECKS = {
    "forbidden_action_types_absent",
    "forbidden_task_types_absent",
    "citations_in_context",
}
# Category floor thresholds used to flag domains where a single model path
# collapses even if the aggregate pass_rate looks acceptable.
CATEGORY_FLOOR_WARN = 0.60
CATEGORY_FLOOR_CRIT = 0.30


def summarize_cases(records: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(records)
    strict_json_cases = sum(1 for record in records if record["strict_json_ok"])
    recovered_json_cases = sum(1 for record in records if record["recovered_json_ok"])
    passed_cases = sum(1 for record in records if record["passed"])
    confidence_values = [
        float(record["confidence"])
        for record in records
        if isinstance(record.get("confidence"), (int, float))
    ]
    confidence_on_pass = [
        float(record["confidence"])
        for record in records
        if record["passed"] and isinstance(record.get("confidence"), (int, float))
    ]
    confidence_on_fail = [
        float(record["confidence"])
        for record in records
        if not record["passed"] and isinstance(record.get("confidence"), (int, float))
    ]

    by_category: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["category"])].append(record)
    for category, items in sorted(grouped.items()):
        by_category[category] = {
            "cases": len(items),
            "passed": sum(1 for item in items if item["passed"]),
            "pass_rate": round(sum(1 for item in items if item["passed"]) / len(items), 4),
        }

    failed_check_counter: Counter[str] = Counter()
    optional_failure_counter: Counter[str] = Counter()
    check_attempt_counter: Counter[str] = Counter()
    request_errors = sum(1 for record in records if record.get("request_error"))
    hard_safety_violation_cases = 0
    hard_safety_violation_breakdown: Counter[str] = Counter()
    for record in records:
        failed_check_counter.update(record["failed_checks"])
        optional_failure_counter.update(record["optional_failures"])
        # A check "attempt" = grader actually applied it for this case
        # (either passed or failed). This is needed for per-check pass_rate
        # because many checks are conditional on expected fields.
        check_attempt_counter.update(record.get("passed_checks", []))
        check_attempt_counter.update(record.get("failed_checks", []))
        # Hard-safety violation = any required hard-safety check failed
        failed_hard = HARD_SAFETY_CHECKS.intersection(record["failed_checks"])
        if failed_hard:
            hard_safety_violation_cases += 1
            hard_safety_violation_breakdown.update(failed_hard)

    # Per-check pass rate (case-level AND-grading drowns out fine signal)
    per_check: dict[str, dict[str, Any]] = {}
    for check_name, attempts in check_attempt_counter.most_common():
        failures = failed_check_counter.get(check_name, 0)
        passed = attempts - failures
        per_check[check_name] = {
            "attempted": attempts,
            "passed": passed,
            "pass_rate": round(passed / attempts, 4) if attempts else 0.0,
        }

    # Category floor flags: which categories are below warn/crit thresholds
    category_floors: dict[str, list[str]] = {"warn": [], "critical": []}
    for cat, stats in by_category.items():
        rate = stats["pass_rate"]
        if rate < CATEGORY_FLOOR_CRIT:
            category_floors["critical"].append(cat)
        elif rate < CATEGORY_FLOOR_WARN:
            category_floors["warn"].append(cat)

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0.0,
        "strict_json_rate": round(strict_json_cases / total_cases, 4) if total_cases else 0.0,
        "recovered_json_rate": round(recovered_json_cases / total_cases, 4) if total_cases else 0.0,
        "average_confidence": round(mean(confidence_values), 4) if confidence_values else None,
        "average_confidence_on_pass": round(mean(confidence_on_pass), 4) if confidence_on_pass else None,
        "average_confidence_on_fail": round(mean(confidence_on_fail), 4) if confidence_on_fail else None,
        "by_category": by_category,
        "request_errors": request_errors,
        "top_failed_checks": failed_check_counter.most_common(10),
        "top_optional_failures": optional_failure_counter.most_common(10),
        # New aggregates
        "per_check": per_check,
        "hard_safety_violation_cases": hard_safety_violation_cases,
        "hard_safety_violation_breakdown": dict(hard_safety_violation_breakdown),
        "hard_safety_violation_rate": round(hard_safety_violation_cases / total_cases, 4) if total_cases else 0.0,
        "category_floors": category_floors,
        "category_floor_warn_threshold": CATEGORY_FLOOR_WARN,
        "category_floor_critical_threshold": CATEGORY_FLOOR_CRIT,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    report_status = report.get("status", "completed")
    lines = [
        "# Fine-tuned Model Eval Summary",
        "",
        f"- status: `{report_status}`",
        f"- model: `{report['model']}`",
        f"- evaluated_at: `{report['evaluated_at']}`",
        f"- total_cases: `{summary['total_cases']}`",
        f"- passed_cases: `{summary['passed_cases']}`",
        f"- pass_rate: `{summary['pass_rate']}`",
        f"- strict_json_rate: `{summary['strict_json_rate']}`",
        f"- recovered_json_rate: `{summary['recovered_json_rate']}`",
        f"- request_errors: `{summary['request_errors']}`",
        "",
        "## Category Results",
        "",
        "| category | cases | passed | pass_rate |",
        "|---|---:|---:|---:|",
    ]

    for category, row in summary["by_category"].items():
        lines.append(f"| {category} | {row['cases']} | {row['passed']} | {row['pass_rate']} |")

    lines.extend(
        [
            "",
            "## Confidence",
            "",
            f"- average_confidence: `{summary['average_confidence']}`",
            f"- average_confidence_on_pass: `{summary['average_confidence_on_pass']}`",
            f"- average_confidence_on_fail: `{summary['average_confidence_on_fail']}`",
            "",
            "## Top Failed Checks",
            "",
        ]
    )

    if summary["top_failed_checks"]:
        for name, count in summary["top_failed_checks"]:
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Top Optional Failures", ""])
    if summary["top_optional_failures"]:
        for name, count in summary["top_optional_failures"]:
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "## Failed Cases", ""])
    failed_records = [record for record in report["cases"] if not record["passed"]]
    if not failed_records:
        lines.append("- 없음")
    else:
        for record in failed_records:
            lines.append(
                f"- `{record['eval_id']}` ({record['category']}): "
                f"{', '.join(record['failed_checks'])}"
            )

    return "\n".join(lines) + "\n"


def write_report(
    output_prefix: Path,
    *,
    model: str,
    system_prompt: str,
    temperature: float,
    eval_files: list[Path],
    records: list[dict[str, Any]],
    status: str,
) -> dict[str, Any]:
    summary = summarize_cases(records)
    report = {
        "schema_version": "fine_tuned_model_eval.v1",
        "status": status,
        "evaluated_at": utc_now_iso(),
        "model": model,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "eval_files": [path.as_posix() for path in eval_files],
        "summary": summary,
        "cases": records,
    }

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    jsonl_path = output_prefix.with_suffix(".jsonl")
    markdown_path = output_prefix.with_suffix(".md")

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"summary_json: {json_path.as_posix()}", flush=True)
    print(f"case_jsonl: {jsonl_path.as_posix()}", flush=True)
    print(f"summary_md: {markdown_path.as_posix()}", flush=True)
    print(f"pass_rate: {summary['pass_rate']}", flush=True)
    return report


def should_retry_openai_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if isinstance(exc, (APIError, APITimeoutError, RateLimitError)):
        return True
    return isinstance(exc, BadRequestError) and "could not parse the json body" in message


def create_completion_with_retry(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_completion_tokens: int,
    max_attempts: int = 3,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )
        except Exception as exc:  # pragma: no cover - depends on upstream API behavior
            last_error = exc
            if attempt >= max_attempts or not should_retry_openai_error(exc):
                break
            sleep_seconds = attempt * 2
            print(
                f"retrying_openai_request attempt={attempt + 1}/{max_attempts} "
                f"sleep_seconds={sleep_seconds} error={exc}",
                flush=True,
            )
            time.sleep(sleep_seconds)
    assert last_error is not None
    raise last_error


def should_retry_gemini_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in ("rate", "timeout", "unavailable", "503", "500", "deadline", "quota")
    )


def call_gemini_with_retry(
    client: Any,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_completion_tokens: int,
    thinking_budget: int | None,
    max_attempts: int = 3,
) -> tuple[str, str | None, dict[str, Any] | None]:
    """Return (raw_text, response_id, usage_dict).

    Uses response_mime_type=application/json so the frontier path's strict
    JSON contract is enforced at the API layer, matching how we'd deploy it.

    thinking_budget controls 2.5 Flash/Pro reasoning budget in tokens.
    None → use model default (dynamic). 0 → disable thinking entirely.
    Positive int → explicit budget. Thinking tokens are billed separately
    from max_output_tokens in 2.5 models but still extend latency.
    """
    if google_genai_types is None:
        raise RuntimeError("google-genai SDK is not installed")
    config_kwargs: dict[str, Any] = dict(
        system_instruction=system_prompt,
        temperature=temperature,
        max_output_tokens=max_completion_tokens,
        response_mime_type="application/json",
    )
    if thinking_budget is not None:
        try:
            config_kwargs["thinking_config"] = google_genai_types.ThinkingConfig(
                thinking_budget=thinking_budget
            )
        except Exception:
            pass
    config = google_genai_types.GenerateContentConfig(**config_kwargs)
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[user_message],
                config=config,
            )
            raw_text = getattr(response, "text", None) or ""
            if not raw_text:
                # Fallback: walk candidates for text parts
                parts: list[str] = []
                for cand in getattr(response, "candidates", None) or []:
                    content = getattr(cand, "content", None)
                    for part in getattr(content, "parts", None) or []:
                        text = getattr(part, "text", None)
                        if text:
                            parts.append(text)
                raw_text = "".join(parts)
            usage_obj = getattr(response, "usage_metadata", None)
            usage: dict[str, Any] | None = None
            if usage_obj is not None:
                usage = {
                    "prompt_token_count": getattr(usage_obj, "prompt_token_count", None),
                    "candidates_token_count": getattr(usage_obj, "candidates_token_count", None),
                    "total_token_count": getattr(usage_obj, "total_token_count", None),
                }
            response_id = getattr(response, "response_id", None)
            return raw_text, response_id, usage
        except Exception as exc:  # pragma: no cover
            last_error = exc
            if attempt >= max_attempts or not should_retry_gemini_error(exc):
                break
            sleep_seconds = attempt * 2
            print(
                f"retrying_gemini_request attempt={attempt + 1}/{max_attempts} "
                f"sleep_seconds={sleep_seconds} error={exc}",
                flush=True,
            )
            time.sleep(sleep_seconds)
    assert last_error is not None
    raise last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini", "minimax"],
        default="openai",
        help=(
            "Which upstream API to call. gemini uses google-genai SDK; "
            "minimax uses the OpenAI SDK with MiniMax base_url."
        ),
    )
    parser.add_argument(
        "--minimax-base-url",
        default="https://api.minimax.io/v1",
        help="MiniMax API base URL (only used when --provider minimax). Default is international endpoint.",
    )
    parser.add_argument("--eval-files", nargs="*", default=[str(path) for path in DEFAULT_EVAL_FILES])
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    parser.add_argument("--system-prompt-version", choices=sorted(SYSTEM_PROMPT_BY_VERSION), default="legacy")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--max-completion-tokens", type=int, default=1600)
    parser.add_argument(
        "--rag-index-path",
        default=str(DEFAULT_RAG_INDEX_PATH),
        help=(
            "RAG index to inline retrieved_context chunk bodies for frontier+RAG prompt versions. "
            "Non-frontier prompt versions ignore this."
        ),
    )
    parser.add_argument(
        "--force-rag-inline",
        action="store_true",
        help="Force chunk-body inlining even for non-frontier prompt versions (A/B experiments).",
    )
    parser.add_argument(
        "--live-rag",
        action="store_true",
        help=(
            "Discard each eval case's static retrieved_context and re-run the "
            "keyword retriever against data/rag/*.jsonl live for every case. "
            "Enforces production-realistic RAG grounding for all model paths."
        ),
    )
    parser.add_argument(
        "--rag-top-k",
        type=int,
        default=5,
        help="Top-k chunks to retrieve in live-rag mode (default: 5).",
    )
    parser.add_argument(
        "--rag-corpus-paths",
        nargs="*",
        default=[str(p) for p in DEFAULT_RAG_CORPUS_PATHS],
        help="JSONL corpus files the KeywordRagRetriever searches in live-rag mode.",
    )
    parser.add_argument(
        "--rag-retriever-type",
        choices=["keyword", "vector", "openai"],
        default="keyword",
        help=(
            "Which retriever backend to use in --live-rag mode. 'keyword' uses "
            "llm_orchestrator.KeywordRagRetriever (token overlap + bonus). "
            "'vector' uses the TF-IDF+SVD dense embeddings from --rag-index-path. "
            "'openai' uses text-embedding-3-small against "
            "artifacts/rag_index/pepper_openai_embed_index.json."
        ),
    )
    parser.add_argument(
        "--pacing-seconds",
        type=float,
        default=0.0,
        help="Minimum seconds to wait between API calls. Use 13.0 for Gemini free tier (5 RPM).",
    )
    parser.add_argument(
        "--gemini-thinking-budget",
        type=int,
        default=None,
        help=(
            "Gemini 2.5 thinking budget in tokens. None (default) = model default dynamic, "
            "0 = disable thinking, >0 = explicit budget. Only applies when --provider gemini."
        ),
    )
    args = parser.parse_args()

    if load_dotenv:
        load_dotenv()

    openai_client: Any = None
    gemini_client: Any = None
    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY not found.")
        if OpenAI is None:
            raise SystemExit("openai package is not installed in the current environment.")
        openai_client = OpenAI(api_key=api_key)
    elif args.provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise SystemExit("GEMINI_API_KEY (or GOOGLE_API_KEY) not found.")
        if google_genai is None:
            raise SystemExit("google-genai package is not installed in the current environment.")
        gemini_client = google_genai.Client(api_key=api_key)
    elif args.provider == "minimax":
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            raise SystemExit("MINIMAX_API_KEY not found.")
        if OpenAI is None:
            raise SystemExit("openai package is not installed in the current environment.")
        openai_client = OpenAI(api_key=api_key, base_url=args.minimax_base_url)
        print(
            f"minimax_client_ready base_url={args.minimax_base_url} model={args.model}",
            flush=True,
        )
    else:  # pragma: no cover - argparse choices guard
        raise SystemExit(f"unsupported provider: {args.provider}")

    eval_files = [Path(path) for path in args.eval_files]
    system_prompt = SYSTEM_PROMPT_BY_VERSION[args.system_prompt_version]
    cases: list[dict[str, Any]] = []
    for eval_file in eval_files:
        cases.extend(load_jsonl(eval_file))
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    chunk_lookup: dict[str, dict[str, Any]] | None = None
    needs_chunk_lookup = (
        args.live_rag
        or args.system_prompt_version in FRONTIER_RAG_PROMPT_VERSIONS
        or args.force_rag_inline
    )
    if needs_chunk_lookup:
        rag_path = Path(args.rag_index_path)
        chunk_lookup = load_rag_chunk_lookup(rag_path)
        print(
            f"rag_inline_enabled prompt_version={args.system_prompt_version} "
            f"rag_index={rag_path.as_posix()} chunks_loaded={len(chunk_lookup)}",
            flush=True,
        )
        if not chunk_lookup:
            print(
                "rag_inline_warning chunk_lookup empty — "
                "frontier path will see only bare chunk_ids",
                flush=True,
            )

    live_retriever: LiveRagRetriever | None = None
    if args.live_rag:
        # Ensure llm_orchestrator and policy_engine are importable
        for sibling in ("llm-orchestrator", "policy-engine"):
            sibling_path = (Path(__file__).resolve().parent.parent / sibling).as_posix()
            if sibling_path not in sys.path:
                sys.path.insert(0, sibling_path)
        corpus_paths = [Path(p) for p in args.rag_corpus_paths]
        live_retriever = LiveRagRetriever(
            corpus_paths=corpus_paths,
            chunk_lookup=chunk_lookup or {},
            retriever_type=args.rag_retriever_type,
            rag_index_path=Path(args.rag_index_path),
        )
        print(
            f"live_rag_enabled top_k={args.rag_top_k} "
            f"retriever_type={args.rag_retriever_type} "
            f"corpus={[p.as_posix() for p in corpus_paths]} "
            f"retriever_rows={len(live_retriever._retriever.rows)}",
            flush=True,
        )

    records: list[dict[str, Any]] = []
    output_prefix = Path(args.output_prefix)
    last_call_at: float = 0.0

    for index, case in enumerate(cases, start=1):
        if args.pacing_seconds > 0 and last_call_at > 0:
            elapsed = time.time() - last_call_at
            wait = args.pacing_seconds - elapsed
            if wait > 0:
                time.sleep(wait)
        user_message, effective_retrieved_ids = build_user_message(
            case,
            chunk_lookup=chunk_lookup,
            live_retriever=live_retriever,
            live_rag_top_k=args.rag_top_k,
        )
        raw_content = ""
        response_id: str | None = None
        usage: dict[str, Any] | None = None
        request_error: Exception | None = None
        try:
            if args.provider in ("openai", "minimax"):
                completion = create_completion_with_retry(
                    openai_client,
                    model=args.model,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    temperature=args.temperature,
                    max_completion_tokens=args.max_completion_tokens,
                )
                raw_content = completion.choices[0].message.content or ""
                response_id = completion.id
                if getattr(completion, "usage", None) is not None:
                    usage_payload = completion.usage
                    usage = usage_payload.model_dump() if hasattr(usage_payload, "model_dump") else dict(usage_payload)
            else:  # gemini
                raw_content, response_id, usage = call_gemini_with_retry(
                    gemini_client,
                    model=args.model,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    temperature=args.temperature,
                    max_completion_tokens=args.max_completion_tokens,
                    thinking_budget=args.gemini_thinking_budget,
                )
        except Exception as exc:  # pragma: no cover - depends on upstream API behavior
            request_error = exc
        finally:
            last_call_at = time.time()

        if request_error is not None:
            record = {
                "eval_id": case.get("eval_id"),
                "category": case.get("category"),
                "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                "prompt_index": index,
                "strict_json_ok": False,
                "recovered_json_ok": False,
                "parse_error": str(request_error),
                "passed": False,
                "passed_checks": [],
                "failed_checks": ["request_error"],
                "optional_failures": [],
                "action_types": [],
                "robot_task_types": [],
                "citation_ids": [],
                "confidence": None,
                "request_error": True,
                "request": {
                    "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                    "user_message": user_message,
                },
                "response": {
                    "raw_content": "",
                    "parsed_output": None,
                    "response_id": None,
                    "usage": None,
                    "request_error": str(request_error),
                },
            }
            records.append(record)
            print(
                f"[{index}/{len(cases)}] {case.get('eval_id')} "
                f"passed=False strict_json=False request_error={request_error}",
                flush=True,
            )
            continue

        parse_result = parse_response(raw_content)
        graded = grade_case(
            case,
            parse_result,
            effective_retrieved_ids=effective_retrieved_ids,
        )

        record = {
            "eval_id": case.get("eval_id"),
            "category": case.get("category"),
            "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
            "prompt_index": index,
            "strict_json_ok": parse_result["strict_json_ok"],
            "recovered_json_ok": parse_result["recovered_json_ok"],
            "parse_error": parse_result["parse_error"],
            "passed": graded["passed"],
            "passed_checks": graded["passed_checks"],
            "failed_checks": graded["failed_checks"],
            "optional_failures": graded["optional_failures"],
            "action_types": graded["action_types"],
            "robot_task_types": graded["robot_task_types"],
            "citation_ids": graded["citation_ids"],
            "confidence": graded["confidence"],
            "effective_retrieved_ids": effective_retrieved_ids,
            "request_error": False,
            "request": {
                "task_type": str(case.get("task_type") or case.get("category") or "unknown"),
                "user_message": user_message,
            },
            "response": {
                "raw_content": raw_content,
                "parsed_output": graded["raw_output"],
                "response_id": response_id,
                "usage": usage,
            },
        }
        records.append(record)
        print(
            f"[{index}/{len(cases)}] {case.get('eval_id')} "
            f"passed={record['passed']} strict_json={record['strict_json_ok']}",
            flush=True,
        )

    status = "completed_with_errors" if any(record.get("request_error") for record in records) else "completed"
    write_report(
        output_prefix,
        model=args.model,
        system_prompt=system_prompt,
        temperature=args.temperature,
        eval_files=eval_files,
        records=records,
        status=status,
    )


if __name__ == "__main__":
    main()
