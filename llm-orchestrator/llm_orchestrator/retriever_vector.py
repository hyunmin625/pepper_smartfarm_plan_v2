"""Dense retriever backends for llm-orchestrator.

Two implementations share the same `.search(...)` interface as
`llm_orchestrator.retriever.KeywordRagRetriever`, so the orchestrator
service can swap backends at runtime via a single env var flag
(`OPS_API_RETRIEVER_TYPE`):

- `TfidfSvdRagRetriever`: reads the `local_embedding` field already stored
  on every document in `artifacts/rag_index/pepper_expert_with_farm_case_index.json`
  by `scripts/build_rag_index.py`. Pure offline, zero external calls.
- `OpenAIEmbeddingRetriever`: reads the `embedding` field (1536-dim,
  text-embedding-3-small) and vectorizes each query via the OpenAI API
  at call time. Query latency ~200-500 ms, cost ~$0.000002 per call.

Phase F recall benchmark (250 eval cases):

| retriever                    | avg recall@5 | any_hit@5 |
|------------------------------|-------------:|----------:|
| KeywordRagRetriever          |        0.164 |     0.232 |
| TfidfSvdRagRetriever (24d)   |        0.172 |     0.272 |
| OpenAIEmbeddingRetriever     |        0.352 |     0.492 |
|   (text-embedding-3-small)   |              |           |

See `artifacts/reports/phase_f_validator_retriever_improvements.md`.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

from .retriever import RetrievedChunk


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCAL_RAG_INDEX_PATH = (
    REPO_ROOT / "artifacts" / "rag_index" / "pepper_expert_with_farm_case_index.json"
)
DEFAULT_OPENAI_RAG_INDEX_PATH = (
    REPO_ROOT / "artifacts" / "rag_index" / "pepper_openai_embed_index.json"
)


class TfidfSvdRagRetriever:
    """Offline TF-IDF + SVD dense retriever.

    Loads a `local_vector_model` definition (terms, idf, components) and
    per-document `local_embedding` vectors from the rag_index JSON produced
    by `scripts/build_rag_index.py`. Queries are tokenized with the same
    regex used at index build time, projected into the SVD space, then
    matched to docs by cosine similarity.
    """

    def __init__(self, *, rag_index_path: Path | str | None = None) -> None:
        path = Path(rag_index_path or DEFAULT_LOCAL_RAG_INDEX_PATH)
        with path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        lvm = index.get("local_vector_model") or {}
        if lvm.get("type") != "tfidf_svd":
            raise RuntimeError(
                f"{path} does not ship a tfidf_svd local vector model"
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
            emb = [float(x) for x in embedding]
            enorm = math.sqrt(sum(x * x for x in emb)) or 1.0
            self._docs.append({
                "chunk_id": doc.get("id"),
                "document_id": metadata.get("document_id") or doc.get("id"),
                "source_type": metadata.get("source_type", "unknown"),
                "source_section": metadata.get("source_section"),
                "trust_level": metadata.get("trust_level", "unknown"),
                "growth_stage": metadata.get("growth_stage") or [],
                "citation_required": bool(metadata.get("citation_required")),
                "embedding": emb,
                "embedding_norm": enorm,
                "text": doc.get("text") or "",
                "chunk_summary": doc.get("chunk_summary") or "",
            })

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._docs

    def _vectorize(self, text: str) -> list[float]:
        tokens = self._token_pattern.findall(text.lower())
        if not tokens:
            return [0.0] * self.svd_dim
        tf = [0.0] * len(self.terms)
        for tok in tokens:
            idx = self._term_to_idx.get(tok)
            if idx is not None:
                tf[idx] += 1.0
        tfidf = [tf[i] * self.idf[i] for i in range(len(self.terms))]
        norm = math.sqrt(sum(v * v for v in tfidf))
        if norm <= 0:
            return [0.0] * self.svd_dim
        tfidf = [v / norm for v in tfidf]
        projected = [
            sum(self.components[k][i] * tfidf[i] for i in range(len(self.terms)))
            for k in range(self.svd_dim)
        ]
        qnorm = math.sqrt(sum(v * v for v in projected))
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
    ) -> list[RetrievedChunk]:
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
            if growth_stage and isinstance(doc.get("growth_stage"), list):
                if growth_stage in doc["growth_stage"]:
                    sim += 0.05
            trust = str(doc.get("trust_level") or "").lower()
            if trust == "high":
                sim += 0.03
            elif trust == "review_required":
                sim -= 0.02
            if sim > 0:
                scored.append((sim, doc))

        scored.sort(key=lambda item: -item[0])
        top = scored[:limit]
        return [
            RetrievedChunk(
                chunk_id=doc["chunk_id"],
                document_id=doc["document_id"],
                chunk_summary=doc.get("chunk_summary", ""),
                source_type=doc.get("source_type", "unknown"),
                trust_level=doc.get("trust_level", "unknown"),
                score=round(sim, 4),
                source_url=None,
                source_section=doc.get("source_section"),
                citation_required=bool(doc.get("citation_required")),
            )
            for sim, doc in top
        ]


class OpenAIEmbeddingRetriever:
    """Dense retriever built on OpenAI text-embedding-3-small (1536 dim).

    Reads pre-computed `embedding` vectors from the rag_index JSON produced
    by `scripts/build_rag_index.py` (without `--skip-embeddings`). Query
    vectors are created on demand via the OpenAI embeddings API, cached
    per-instance nothing — the caller is expected to re-use the instance
    across requests.

    Query cost at text-embedding-3-small pricing is ~$0.000002 per call.
    Latency typically 150-400 ms depending on region.
    """

    def __init__(
        self,
        *,
        rag_index_path: Path | str | None = None,
        model: str = "text-embedding-3-small",
        api_key_env: str = "OPENAI_API_KEY",
    ) -> None:
        try:
            from openai import OpenAI  # lazy import
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "openai package is required for OpenAIEmbeddingRetriever"
            ) from exc
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"{api_key_env} not set")
        self._client = OpenAI(api_key=api_key)
        self._model = model

        path = Path(rag_index_path or DEFAULT_OPENAI_RAG_INDEX_PATH)
        with path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        index_model = index.get("embedding_model")
        if index_model and index_model != model:
            import warnings
            warnings.warn(
                f"OpenAIEmbeddingRetriever: rag_index was built with "
                f"'{index_model}' but query model is '{model}'. Cosine "
                f"scores may be inconsistent.",
                stacklevel=2,
            )

        self._docs: list[dict[str, Any]] = []
        for doc in index.get("documents") or []:
            metadata = doc.get("metadata") or {}
            embedding = doc.get("embedding") or []
            if not embedding:
                continue
            emb = [float(x) for x in embedding]
            norm = math.sqrt(sum(x * x for x in emb)) or 1.0
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
    ) -> list[RetrievedChunk]:
        full_query = " ".join(
            part for part in [query, task_type, zone_id or "", growth_stage or ""] if part
        )
        if not full_query.strip():
            return []
        q = self._embed(full_query)
        qnorm = math.sqrt(sum(x * x for x in q)) or 1.0

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
        return [
            RetrievedChunk(
                chunk_id=doc["chunk_id"],
                document_id=doc["document_id"],
                chunk_summary=doc.get("chunk_summary", ""),
                source_type=doc.get("source_type", "unknown"),
                trust_level=doc.get("trust_level", "unknown"),
                score=round(sim, 4),
                source_url=None,
                source_section=doc.get("source_section"),
                citation_required=bool(doc.get("citation_required")),
            )
            for sim, doc in top
        ]


def create_retriever(
    retriever_type: str,
    *,
    corpus_paths: list[Path] | None = None,
    rag_index_path: Path | str | None = None,
) -> Any:
    """Factory that instantiates the retriever selected by env/config.

    Keeps the import-time cost of TfidfSvdRagRetriever and
    OpenAIEmbeddingRetriever lazy: callers that stay on keyword retrieval
    never load the dense indices.
    """
    rtype = (retriever_type or "keyword").lower()
    if rtype == "keyword":
        from .retriever import KeywordRagRetriever
        return KeywordRagRetriever(corpus_paths=corpus_paths)
    if rtype in ("vector", "tfidf", "tfidf_svd", "local"):
        return TfidfSvdRagRetriever(rag_index_path=rag_index_path)
    if rtype in ("openai", "openai_embedding", "text-embedding-3-small"):
        return OpenAIEmbeddingRetriever(rag_index_path=rag_index_path)
    raise ValueError(f"unknown retriever_type: {retriever_type!r}")
