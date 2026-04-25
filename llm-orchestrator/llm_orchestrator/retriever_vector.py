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
- `LocalSemanticRagRetriever`: dependency-free local semantic candidate
  using domain synonym expansion plus word/character n-gram feature hashing.
  Pure offline, zero external calls.

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
from hashlib import blake2b
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

_SEMANTIC_GROUPS = [
    {
        "worker",
        "worker_present",
        "human",
        "operator",
        "person",
        "작업자",
        "사람",
        "출입",
        "인원",
    },
    {"manual", "manual_override", "override", "수동", "수동모드", "수동전환", "개입"},
    {"safe_mode", "safemode", "estop", "emergency", "비상", "비상정지", "안전모드", "safe"},
    {
        "readback",
        "ack",
        "feedback",
        "communication",
        "comm",
        "통신",
        "응답",
        "피드백",
        "확인신호",
    },
    {"sensor", "stale", "missing", "bad", "flatline", "센서", "결측", "불량", "이상", "오류"},
    {"irrigation", "watering", "valve", "drain", "관수", "급액", "배액", "밸브"},
    {"fertigation", "nutrient", "ec", "ph", "양액", "비료", "영양", "농도"},
    {
        "rootzone",
        "substrate",
        "dryback",
        "moisture",
        "wilt",
        "wilting",
        "근권",
        "배지",
        "함수율",
        "건조",
        "시듦",
        "위조",
    },
    {"alert", "alarm", "notify", "create_alert", "알림", "경보", "알람", "보고"},
    {"approval", "audit", "policy", "block", "block_action", "승인", "감사", "정책", "차단"},
    {
        "robot",
        "inspect_crop",
        "manual_review",
        "skip_area",
        "로봇",
        "점검",
        "작물점검",
        "수동검토",
        "구역제외",
    },
]

_SEMANTIC_EXPANSIONS: dict[str, set[str]] = {}
for _group in _SEMANTIC_GROUPS:
    _normalized_group = {item.lower() for item in _group}
    for _term in _normalized_group:
        _SEMANTIC_EXPANSIONS[_term] = _normalized_group


def _stable_bucket(feature: str, dimension: int) -> int:
    digest = blake2b(feature.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimension


def _add_sparse_feature(vector: dict[int, float], feature: str, weight: float, dimension: int) -> None:
    if not feature:
        return
    idx = _stable_bucket(feature, dimension)
    vector[idx] = vector.get(idx, 0.0) + weight


def _normalize_sparse(vector: dict[int, float]) -> dict[int, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm <= 0:
        return {}
    return {idx: value / norm for idx, value in vector.items()}


def _sparse_dot(left: dict[int, float], right: dict[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(idx, 0.0) for idx, value in left.items())


def _flatten_metadata(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        flattened: list[str] = []
        for item in value:
            flattened.extend(_flatten_metadata(item))
        return flattened
    if isinstance(value, dict):
        flattened = []
        for key, item in value.items():
            flattened.append(str(key))
            flattened.extend(_flatten_metadata(item))
        return flattened
    return [str(value)]


def _text_ngrams(text: str, *, min_n: int = 2, max_n: int = 3) -> list[str]:
    compact = "".join(re.findall(r"[0-9a-z가-힣]+", text.lower()))
    if len(compact) < min_n:
        return []
    ngrams: list[str] = []
    for n in range(min_n, max_n + 1):
        if len(compact) < n:
            continue
        ngrams.extend(compact[i : i + n] for i in range(len(compact) - n + 1))
    return ngrams


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


class LocalSemanticRagRetriever:
    """Dependency-free local semantic retriever.

    This is not a neural embedding model. It is a zero-cost candidate that
    tries to capture domain-adjacent wording through:

    - domain synonym expansion (`worker_present` ~= 작업자 ~= 사람 출입)
    - word tokens from text + metadata
    - character n-grams for Korean/English mixed queries
    - deterministic feature hashing into a sparse normalized vector

    The goal is to provide a stronger no-network candidate than plain
    keyword overlap while keeping ops-api startup free of ML dependencies.
    """

    def __init__(
        self,
        *,
        rag_index_path: Path | str | None = None,
        dimension: int = 4096,
    ) -> None:
        self.dimension = dimension
        path = Path(rag_index_path or DEFAULT_LOCAL_RAG_INDEX_PATH)
        with path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)

        self._token_pattern = re.compile(r"[0-9a-zA-Z가-힣_]+")
        self._docs: list[dict[str, Any]] = []
        for doc in index.get("documents") or []:
            metadata = doc.get("metadata") or {}
            chunk_id = doc.get("id")
            if not chunk_id:
                continue
            text_parts = [
                str(doc.get("text") or ""),
                str(doc.get("chunk_summary") or ""),
                *(_flatten_metadata(metadata)),
            ]
            searchable_text = " ".join(part for part in text_parts if part)
            vector = self._vectorize(searchable_text, is_document=True)
            if not vector:
                continue
            self._docs.append({
                "chunk_id": chunk_id,
                "document_id": metadata.get("document_id") or chunk_id,
                "source_type": metadata.get("source_type", "unknown"),
                "source_section": metadata.get("source_section"),
                "trust_level": metadata.get("trust_level", "unknown"),
                "growth_stage": metadata.get("growth_stage") or [],
                "citation_required": bool(metadata.get("citation_required")),
                "embedding": vector,
                "text": doc.get("text") or "",
                "chunk_summary": doc.get("chunk_summary") or "",
            })

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._docs

    def _vectorize(self, text: str, *, is_document: bool = False) -> dict[int, float]:
        vector: dict[int, float] = {}
        tokens = [tok.lower() for tok in self._token_pattern.findall(text) if len(tok) >= 2]
        for token in tokens:
            _add_sparse_feature(vector, f"tok:{token}", 1.0, self.dimension)
            for expanded in _SEMANTIC_EXPANSIONS.get(token, ()):
                _add_sparse_feature(vector, f"sem:{expanded}", 1.35, self.dimension)

        # Char n-grams are noisy but useful for Korean inflection and
        # English/Korean mixed operational terms. Keep their weight lower
        # than explicit tokens/synonyms so exact domain tags still dominate.
        ngram_weight = 0.18 if is_document else 0.24
        for ngram in _text_ngrams(text):
            _add_sparse_feature(vector, f"ng:{ngram}", ngram_weight, self.dimension)
        return _normalize_sparse(vector)

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
        if not q:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._docs:
            sim = _sparse_dot(q, doc["embedding"])
            if growth_stage and isinstance(doc.get("growth_stage"), list):
                if growth_stage in doc["growth_stage"]:
                    sim += 0.04
            trust = str(doc.get("trust_level") or "").lower()
            if trust == "high":
                sim += 0.02
            elif trust == "review_required":
                sim -= 0.01
            if sim > 0:
                scored.append((sim, doc))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("chunk_id"))))
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
            for sim, doc in scored[:limit]
        ]


class LocalHybridRagRetriever:
    """Reciprocal Rank Fusion of keyword + LocalSemanticRagRetriever."""

    def __init__(
        self,
        *,
        corpus_paths: list[Path] | None = None,
        rag_index_path: Path | str | None = None,
        rrf_k: int = 60,
    ) -> None:
        from .retriever import KeywordRagRetriever

        self._keyword = KeywordRagRetriever(corpus_paths=corpus_paths)
        self._local_semantic = LocalSemanticRagRetriever(rag_index_path=rag_index_path)
        self._rrf_k = rrf_k
        self._rows = self._local_semantic.rows

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._rows

    def search(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None = None,
        growth_stage: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedChunk]:
        backend_limit = max(limit * 3, 10)
        keyword_hits = self._keyword.search(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=backend_limit,
        )
        semantic_hits = self._local_semantic.search(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=backend_limit,
        )

        fused: dict[str, dict[str, Any]] = {}
        for backend_label, hits in (("keyword", keyword_hits), ("local_embed", semantic_hits)):
            for rank, chunk in enumerate(hits):
                cid = chunk.chunk_id
                entry = fused.get(cid)
                if entry is None:
                    entry = {"chunk": chunk, "fused_score": 0.0, "backends": []}
                    fused[cid] = entry
                if backend_label == "local_embed":
                    entry["chunk"] = chunk
                entry["fused_score"] += 1.0 / (self._rrf_k + rank + 1)
                entry["backends"].append(f"{backend_label}#{rank + 1}")

        ordered = sorted(
            fused.values(),
            key=lambda item: (-item["fused_score"], item["chunk"].chunk_id),
        )
        result: list[RetrievedChunk] = []
        for entry in ordered[:limit]:
            base = entry["chunk"]
            result.append(RetrievedChunk(
                chunk_id=base.chunk_id,
                document_id=base.document_id,
                chunk_summary=base.chunk_summary,
                source_type=base.source_type,
                trust_level=base.trust_level,
                score=round(float(entry["fused_score"]), 4),
                source_url=base.source_url,
                source_section=base.source_section,
                citation_required=base.citation_required,
            ))
        return result


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


class HybridRagRetriever:
    """Reciprocal Rank Fusion of KeywordRagRetriever + OpenAIEmbeddingRetriever.

    Phase F confirmed two facts that motivate a hybrid approach:

    - ``KeywordRagRetriever`` wins on categories whose eval queries carry
      very specific Korean domain tokens (climate_risk 0.222 / harvest_drying
      0.312 / rootzone_diagnosis 0.400 on recall@5). Keyword overlap + trust
      boost beats dense embeddings when the query literally contains the
      slab names and tag words the chunks use.
    - ``OpenAIEmbeddingRetriever`` wins on almost everything else, especially
      ``safety_policy`` (0.000 → 0.542) and ``edge_case`` (0.088 → 0.471),
      because 1536-d OpenAI vectors cover paraphrases and synonyms that
      keyword overlap misses entirely.

    Hybrid (RRF) averages those strengths. At each query we ask both
    backends for their top ``per_retriever_limit`` hits, score each doc by
    ``sum(1 / (rrf_k + rank_i))`` across all backends that surfaced it,
    then return the top ``limit`` by fused score. ``rrf_k = 60`` is the
    standard RRF constant (Cormack et al. 2009). Each sub-retriever cost
    is the same as running it directly, so hybrid costs roughly the
    combined price of its components (still < $0.000005 per query at
    text-embedding-3-small pricing).

    Interface matches :meth:`KeywordRagRetriever.search` so a caller that
    swaps in hybrid sees the same ``list[RetrievedChunk]`` shape.
    """

    def __init__(
        self,
        *,
        corpus_paths: list[Path] | None = None,
        rag_index_path: Path | str | None = None,
        rrf_k: int = 60,
        per_retriever_limit: int = 10,
    ) -> None:
        from .retriever import KeywordRagRetriever
        self._keyword = KeywordRagRetriever(corpus_paths=corpus_paths)
        self._openai = OpenAIEmbeddingRetriever(rag_index_path=rag_index_path)
        self._rrf_k = int(rrf_k)
        self._per_retriever_limit = int(per_retriever_limit)

    @property
    def rows(self) -> list[dict[str, Any]]:
        # Expose the denser retriever's rows for logging/smoke parity with
        # the other backends. The keyword corpus is a jsonl of row dicts,
        # not RetrievedChunk, so the openai doc list is more useful here.
        return self._openai.rows

    def search(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None = None,
        growth_stage: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedChunk]:
        kw_hits = self._keyword.search(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=self._per_retriever_limit,
        )
        oa_hits = self._openai.search(
            query=query,
            task_type=task_type,
            zone_id=zone_id,
            growth_stage=growth_stage,
            limit=self._per_retriever_limit,
        )

        # Fuse by reciprocal rank. Two backends is enough here but the
        # loop is general so we can add the TF-IDF backend later.
        fused: dict[str, dict[str, Any]] = {}
        for backend_label, hits in (("keyword", kw_hits), ("openai", oa_hits)):
            for rank, chunk in enumerate(hits):
                cid = chunk.chunk_id
                entry = fused.get(cid)
                if entry is None:
                    entry = {
                        "chunk": chunk,
                        "fused_score": 0.0,
                        "backends": [],
                    }
                    fused[cid] = entry
                # Prefer the openai-sourced RetrievedChunk because it carries
                # source_section/source_type from the rich index, but keep
                # whichever we saw first if the keyword retriever found a
                # chunk the openai one missed.
                if backend_label == "openai":
                    entry["chunk"] = chunk
                entry["fused_score"] += 1.0 / (self._rrf_k + rank + 1)
                entry["backends"].append(f"{backend_label}#{rank + 1}")

        ordered = sorted(
            fused.values(),
            key=lambda item: (-item["fused_score"], item["chunk"].chunk_id),
        )
        top = ordered[:limit]
        result: list[RetrievedChunk] = []
        for entry in top:
            base = entry["chunk"]
            # Re-stamp the fused score into the returned RetrievedChunk so
            # downstream audit logs capture the blended rank, not whichever
            # raw similarity happened to come from the last backend.
            result.append(RetrievedChunk(
                chunk_id=base.chunk_id,
                document_id=base.document_id,
                chunk_summary=base.chunk_summary,
                source_type=base.source_type,
                trust_level=base.trust_level,
                score=round(float(entry["fused_score"]), 4),
                source_url=base.source_url,
                source_section=base.source_section,
                citation_required=base.citation_required,
            ))
        return result


def create_retriever(
    retriever_type: str,
    *,
    corpus_paths: list[Path] | None = None,
    rag_index_path: Path | str | None = None,
) -> Any:
    """Factory that instantiates the retriever selected by env/config.

    Keeps the import-time cost of TfidfSvdRagRetriever,
    LocalSemanticRagRetriever, OpenAIEmbeddingRetriever, and
    HybridRagRetriever lazy: callers that stay on keyword retrieval never
    load the dense indices.
    """
    rtype = (retriever_type or "keyword").lower()
    if rtype == "keyword":
        from .retriever import KeywordRagRetriever
        return KeywordRagRetriever(corpus_paths=corpus_paths)
    if rtype in ("vector", "tfidf", "tfidf_svd", "local"):
        return TfidfSvdRagRetriever(rag_index_path=rag_index_path)
    if rtype in ("local_embed", "local_semantic", "semantic", "hashing"):
        return LocalSemanticRagRetriever(rag_index_path=rag_index_path)
    if rtype in ("local_hybrid", "keyword_local", "keyword_semantic"):
        return LocalHybridRagRetriever(
            corpus_paths=corpus_paths,
            rag_index_path=rag_index_path,
        )
    if rtype in ("openai", "openai_embedding", "text-embedding-3-small"):
        return OpenAIEmbeddingRetriever(rag_index_path=rag_index_path)
    if rtype in ("hybrid", "rrf", "keyword_openai"):
        return HybridRagRetriever(
            corpus_paths=corpus_paths,
            rag_index_path=rag_index_path,
        )
    raise ValueError(f"unknown retriever_type: {retriever_type!r}")
